#!/usr/bin/env node
// Entry point for `npm run publish-weekly`, run daily by
// .github/workflows/automatic-blog-publisher.yml so it can make
// incremental progress on a staged rollout (see below), plus on-demand via
// workflow_dispatch.
//
// A new article's English page and non-English rollout are NOT published
// in one run. Translating one article into 9 languages is ~130-150 calls
// to a free, unofficial, rate-limited endpoint — doing that in one burst
// is what triggered a real 429 while building this pipeline. Instead:
//   - A new article only STARTS on Tuesday or Friday (or via a manual
//     workflow_dispatch run) and only if nothing is currently rolling out.
//     English publishes immediately that day.
//   - Every day after that, this script publishes a small batch of the
//     remaining non-English languages (DAILY_LANGUAGE_BUDGET at a time)
//     for whichever article is mid-rollout, until all languages are done.
//   - At 2/day, 9 non-English languages complete in 5 days, leaving buffer
//     inside the 7-day target for a failed/retried day.
// Progress is tracked implicitly: content-queue/in-progress/<file>.json
// marks which article is rolling out, and "which languages are already
// done" is read straight off which {lang}/blog/{slug}/index.html files
// already exist on disk — no separate state file to keep in sync.
//
// This script never writes original article content. See
// content-queue/README.md for why, and for the queue file schema.

import { mkdirSync, writeFileSync, existsSync, appendFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { LANG_ORDER, LANG_META } from './lib/lang-meta.js';
import { translateArticle } from './lib/translate.js';
import { renderArticleHtml } from './lib/render-article.js';
import { addArticleToSitemap } from './lib/sitemap.js';
import { updateHubPage } from './lib/hub.js';
import {
  getInProgressArticle,
  getNextQueuedArticle,
  countPending,
  startRollout,
  completeRollout,
} from './lib/queue.js';

const SITEMAP_PATH = 'sitemap.xml';
const HUB_PATH = 'blog/index.html';
const DAILY_LANGUAGE_BUDGET = 2;
const NON_ENGLISH_LANGS = LANG_ORDER.filter((l) => l !== 'en');
const ARTICLE_START_DAYS_UTC = [2, 5]; // Tuesday, Friday

function articleFilePath(lang, slug) {
  const prefix = LANG_META[lang].homePrefix; // '' for en, '/es' etc.
  return join(`.${prefix}`, 'blog', slug, 'index.html');
}

/** Lets the GitHub Actions workflow read the in-progress article's slug (to name a stable per-article PR branch) without parsing log output. No-op outside CI. */
function writeGithubOutput(slug) {
  if (!process.env.GITHUB_OUTPUT) return;
  appendFileSync(process.env.GITHUB_OUTPUT, `slug=${slug}\n`);
}

function isArticleStartAllowedToday() {
  if (process.env.PUBLISH_FORCE_START === '1') return true;
  return ARTICLE_START_DAYS_UTC.includes(new Date().getUTCDay());
}

function languagesAlreadyPublished(slug) {
  return NON_ENGLISH_LANGS.filter((lang) => existsSync(articleFilePath(lang, slug)));
}

async function publishLanguage(article, lang, dates) {
  console.log(`  translating -> ${lang}...`);
  const translated = await translateArticle(article, lang);
  const html = renderArticleHtml(translated, lang, dates);
  const outPath = articleFilePath(lang, article.slug);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, html, 'utf8');
  return outPath;
}

async function main() {
  const dates = { datePublished: new Date().toISOString().slice(0, 10), dateModified: new Date().toISOString().slice(0, 10) };
  const written = [];

  let inProgress = getInProgressArticle();

  if (!inProgress) {
    if (!isArticleStartAllowedToday()) {
      console.log('No article rollout in progress, and today is not an article-start day (Tue/Fri) or a manual run.');
      console.log(`(${countPending()} items pending in content-queue/pending — will start Tue/Fri.)`);
      return;
    }

    const next = getNextQueuedArticle();
    if (!next) {
      console.log('content-queue/pending is empty — nothing to start today.');
      return;
    }

    const { filename, article } = next;
    console.log(`Starting rollout: "${article.title}" (${article.slug}) from ${filename}`);

    startRollout(filename);
    written.push(await publishLanguage(article, 'en', dates));
    addArticleToSitemap(SITEMAP_PATH, article.slug);
    updateHubPage(HUB_PATH, article);

    inProgress = { filename, article };
  } else {
    console.log(`Continuing rollout: "${inProgress.article.title}" (${inProgress.article.slug})`);
  }

  const { filename, article } = inProgress;
  writeGithubOutput(article.slug);
  const alreadyDone = languagesAlreadyPublished(article.slug);
  const remaining = NON_ENGLISH_LANGS.filter((l) => !alreadyDone.includes(l));

  if (remaining.length === 0) {
    completeRollout(filename);
    console.log(`All languages already published for "${article.slug}" — rollout complete.`);
  } else {
    const todaysBatch = remaining.slice(0, DAILY_LANGUAGE_BUDGET);
    console.log(`${alreadyDone.length}/${NON_ENGLISH_LANGS.length} non-English languages already done. Publishing ${todaysBatch.length} more today: ${todaysBatch.join(', ')}`);

    for (const lang of todaysBatch) {
      written.push(await publishLanguage(article, lang, dates));
    }

    const stillRemaining = remaining.length - todaysBatch.length;
    if (stillRemaining === 0) {
      completeRollout(filename);
      console.log(`\nRollout complete for "${article.slug}" — all ${NON_ENGLISH_LANGS.length} non-English languages published.`);
    } else {
      console.log(`\n${stillRemaining} language(s) remaining for "${article.slug}"; will continue on the next run.`);
    }
  }

  if (written.length > 0) {
    console.log('\nFiles written this run:');
    for (const f of written) console.log(`  ${f}`);
  }
}

main().catch((err) => {
  console.error('publish-weekly failed:', err);
  process.exitCode = 1;
});
