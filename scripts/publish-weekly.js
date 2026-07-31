#!/usr/bin/env node
// Entry point for `npm run publish-weekly`, run by
// .github/workflows/automatic-blog-publisher.yml (Tue/Fri 09:00 UTC and
// on-demand via workflow_dispatch). Picks the oldest article waiting in
// content-queue/pending/, translates it into all 10 site languages,
// renders each language's page, updates sitemap.xml and the English blog
// hub, and archives the queue file. Writes files to disk only — committing
// and opening the review PR is the workflow's job, not this script's.
//
// This script never writes original article content. See
// content-queue/README.md for why, and for the queue file schema.

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { LANG_ORDER, LANG_META } from './lib/lang-meta.js';
import { translateArticle } from './lib/translate.js';
import { renderArticleHtml } from './lib/render-article.js';
import { addArticleToSitemap } from './lib/sitemap.js';
import { updateHubPage } from './lib/hub.js';
import { getNextQueuedArticle, archiveQueuedArticle, countPending } from './lib/queue.js';

const SITEMAP_PATH = 'sitemap.xml';
const HUB_PATH = 'blog/index.html';

function articleFilePath(lang, slug) {
  const prefix = LANG_META[lang].homePrefix; // '' for en, '/es' etc.
  return join(`.${prefix}`, 'blog', slug, 'index.html');
}

async function main() {
  const next = getNextQueuedArticle();

  if (!next) {
    console.log('content-queue/pending is empty — nothing to publish this run.');
    console.log(`(${countPending()} items pending.)`);
    process.exitCode = 0;
    return;
  }

  const { filename, article } = next;
  console.log(`Publishing "${article.title}" (${article.slug}) from ${filename}`);

  const today = new Date().toISOString().slice(0, 10);
  const dates = { datePublished: today, dateModified: today };

  const writtenFiles = [];
  for (const lang of LANG_ORDER) {
    console.log(`  translating -> ${lang}...`);
    const translated = await translateArticle(article, lang);
    const html = renderArticleHtml(translated, lang, dates);
    const outPath = articleFilePath(lang, article.slug);
    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, html, 'utf8');
    writtenFiles.push(outPath);
  }

  addArticleToSitemap(SITEMAP_PATH, article.slug);
  updateHubPage(HUB_PATH, article);
  archiveQueuedArticle(filename);

  console.log('\nDone. Files written:');
  for (const f of writtenFiles) console.log(`  ${f}`);
  console.log(`  ${SITEMAP_PATH} (updated)`);
  console.log(`  ${HUB_PATH} (updated — English hub only, see content-queue/README.md)`);
  console.log(`  content-queue/published/${filename} (archived)`);
}

main().catch((err) => {
  console.error('publish-weekly failed:', err);
  process.exitCode = 1;
});
