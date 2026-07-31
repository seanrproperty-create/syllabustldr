// Appends <url> blocks (one per language, each with reciprocal hreflang
// links to the other 9) for a newly published article into sitemap.xml.
// Does not touch existing <url> blocks — articles published before this
// pipeline existed are out of scope for this pass (see the skill doc /
// project report for why).

import { readFileSync, writeFileSync } from 'node:fs';
import { LANG_ORDER, LANG_META, articleUrl } from './lang-meta.js';

function buildUrlBlock(lang, slug) {
  const alternates = LANG_ORDER
    .map((code) => `    <xhtml:link rel="alternate" hreflang="${LANG_META[code].hreflang}" href="${articleUrl(code, slug)}"/>`)
    .join('\n');
  const xDefault = `    <xhtml:link rel="alternate" hreflang="x-default" href="${articleUrl('en', slug)}"/>`;

  return [
    '  <url>',
    `    <loc>${articleUrl(lang, slug)}</loc>`,
    alternates,
    xDefault,
    '    <changefreq>monthly</changefreq>',
    '    <priority>0.6</priority>',
    '  </url>',
  ].join('\n');
}

/** Adds one <url> block per language for `slug` to sitemap.xml at `sitemapPath`, just before </urlset>. */
function addArticleToSitemap(sitemapPath, slug) {
  const xml = readFileSync(sitemapPath, 'utf8');
  if (xml.includes(`<loc>${articleUrl('en', slug)}</loc>`)) {
    throw new Error(`sitemap.xml already contains an entry for slug "${slug}" — refusing to add a duplicate`);
  }

  const needsXhtmlNs = !xml.includes('xmlns:xhtml=');
  let updated = xml;
  if (needsXhtmlNs) {
    updated = updated.replace(
      /<urlset xmlns="([^"]+)"([^>]*)>/,
      '<urlset xmlns="$1"$2 xmlns:xhtml="http://www.w3.org/1999/xhtml">'
    );
  }

  const blocks = LANG_ORDER.map((lang) => buildUrlBlock(lang, slug)).join('\n\n');
  updated = updated.replace('</urlset>', `${blocks}\n\n</urlset>`);

  writeFileSync(sitemapPath, updated, 'utf8');
}

export { addArticleToSitemap, buildUrlBlock };
