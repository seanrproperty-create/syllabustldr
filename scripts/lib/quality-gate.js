// Automated pre-merge quality gate. Runs once, when a rollout has just
// completed (all 10 languages on disk), and stands in for a human review
// step. It is deliberately a pass/fail machine check, not real editorial
// or translation-accuracy review — it cannot tell you a Korean sentence
// reads awkwardly, only that something structural is broken. Be honest
// with the project owner about that gap: this catches "the pipeline
// broke," not "the translation is bad but well-formed." See
// scheduled-content-pipeline.md in the one-page-site skill for the
// tradeoff this represents.

import { readFileSync, existsSync } from 'node:fs';
import { LANG_ORDER } from './lang-meta.js';

const PROTECTED_TERMS = ['SyllabusTLDR', 'EIGHTFINITY LTD'];
const MIN_CHARS_RATIO = 0.35; // vs. the English page — loose, since some scripts (e.g. CJK) are naturally far more compact per character

function extractTitle(html) {
  const m = html.match(/<title>([\s\S]*?)<\/title>/);
  return m ? m[1] : null;
}

function extractVisibleTextLength(html) {
  const articleMatch = html.match(/<article[\s\S]*?<\/article>/);
  if (!articleMatch) return 0;
  return articleMatch[0].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().length;
}

function extractInternalLinks(html) {
  const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map((m) => m[1]);
  return hrefs.filter((h) => h.startsWith('/') || h.startsWith('https://syllabustldr.com/'));
}

function localHrefToPath(href) {
  let path = href.replace('https://syllabustldr.com', '');
  if (path === '') path = '/';
  if (path.endsWith('/')) path += 'index.html';
  return `.${path}`;
}

function checkLanguagePage(lang, slug, englishCharCount) {
  const problems = [];
  const path = `.${lang === 'en' ? '' : '/' + lang}/blog/${slug}/index.html`;

  if (!existsSync(path)) {
    return [`${path}: missing entirely`];
  }
  const html = readFileSync(path, 'utf8');

  if (!html.includes('<!DOCTYPE html>') || !html.trimEnd().endsWith('</html>')) {
    problems.push(`${path}: doesn't look like a complete HTML document (missing doctype or unclosed </html> — likely a truncated write)`);
  }

  for (const term of PROTECTED_TERMS) {
    if (!html.includes(term)) {
      problems.push(`${path}: missing "${term}" — brand/company name may have been mangled or the page failed to render fully`);
    }
  }

  if (html.includes('{{link') || html.includes('undefined') || html.includes('[object Object]')) {
    problems.push(`${path}: contains a leftover template artifact ({{link.../undefined/[object Object]) — link substitution or rendering likely broke`);
  }

  const title = extractTitle(html);
  if (!title) {
    problems.push(`${path}: no <title> found`);
  }

  const charCount = extractVisibleTextLength(html);
  if (englishCharCount > 0 && charCount < englishCharCount * MIN_CHARS_RATIO) {
    problems.push(`${path}: article body is only ${charCount} characters vs. ${englishCharCount} in English (under the ${Math.round(MIN_CHARS_RATIO * 100)}% floor) — looks truncated or failed to translate`);
  }

  const hreflangCount = (html.match(/rel="alternate" hreflang=/g) || []).length;
  if (hreflangCount < LANG_ORDER.length) {
    problems.push(`${path}: only ${hreflangCount}/${LANG_ORDER.length} hreflang links present`);
  }

  for (const href of extractInternalLinks(html)) {
    if (href.startsWith('mailto:') || href.includes('#')) continue;
    const localPath = localHrefToPath(href);
    if (!existsSync(localPath)) {
      problems.push(`${path}: internal link "${href}" doesn't resolve to an existing file (${localPath})`);
    }
  }

  return problems;
}

/** Returns { pass: boolean, problems: string[] }. Call only once a rollout is fully complete (all 10 languages present). */
function runQualityGate(slug) {
  const englishPath = `./blog/${slug}/index.html`;
  const englishCharCount = existsSync(englishPath) ? extractVisibleTextLength(readFileSync(englishPath, 'utf8')) : 0;

  const problems = [];
  for (const lang of LANG_ORDER) {
    problems.push(...checkLanguagePage(lang, slug, lang === 'en' ? 0 : englishCharCount));
  }

  const sitemap = existsSync('sitemap.xml') ? readFileSync('sitemap.xml', 'utf8') : '';
  const locCount = (sitemap.match(new RegExp(`<loc>[^<]*${slug}/</loc>`, 'g')) || []).length;
  if (locCount !== LANG_ORDER.length) {
    problems.push(`sitemap.xml: expected ${LANG_ORDER.length} <loc> entries for "${slug}", found ${locCount}`);
  }
  if (!sitemap.trimEnd().endsWith('</urlset>')) {
    problems.push('sitemap.xml: does not end with </urlset> — possibly corrupted');
  }

  return { pass: problems.length === 0, problems };
}

export { runQualityGate };
