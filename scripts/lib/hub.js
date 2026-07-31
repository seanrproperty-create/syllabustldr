// Adds a new article's card + JSON-LD entry to the English /blog/ hub page.
// Scope note: this only updates the English hub. Per-language blog hubs
// don't exist yet (blog content has been English-only until this
// pipeline) — see the project report / skill doc for why that's a
// deliberate, flagged gap rather than an oversight.

import { readFileSync, writeFileSync } from 'node:fs';
import { SITE_ORIGIN } from './lang-meta.js';

const CARDS_START = '<!-- BLOG_CARDS_START -->';
const CARDS_END = '<!-- BLOG_CARDS_END -->';

function buildCardHtml(article) {
  return `            <a href="/blog/${article.slug}/" class="block bg-zinc-900/60 border border-zinc-800 hover:border-orange-500/60 rounded-3xl p-6 transition group">
                <span class="text-[10px] font-bold tracking-widest text-orange-400 uppercase">${article.category}</span>
                <h3 class="font-display text-xl font-bold text-white mt-1.5 group-hover:text-orange-300 transition">${article.title}</h3>
                <p class="text-sm text-zinc-400 mt-2 leading-relaxed">${article.ogDescription}</p>
                <span class="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 mt-3">
                    Read the guide <i class="fa-solid fa-arrow-right text-[10px] group-hover:translate-x-0.5 transition"></i>
                </span>
            </a>`;
}

/** Rebuilds the Blog JSON-LD script's text with one more blogPost entry, keeping the file's existing one-line-per-item style rather than round-tripping through JSON.stringify (which would reformat every field). */
function buildJsonLdScript(data, newEntry) {
  const items = [...data.blogPost, newEntry]
    .map((p) => `    { "@type": "BlogPosting", "headline": ${JSON.stringify(p.headline)}, "url": ${JSON.stringify(p.url)} }`)
    .join(',\n');

  return `<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": ${JSON.stringify(data.name)},
  "url": ${JSON.stringify(data.url)},
  "description": ${JSON.stringify(data.description)},
  "isPartOf": { "@type": "WebSite", "name": ${JSON.stringify(data.isPartOf.name)}, "url": ${JSON.stringify(data.isPartOf.url)} },
  "publisher": { "@type": "Organization", "name": ${JSON.stringify(data.publisher.name)}, "url": ${JSON.stringify(data.publisher.url)} },
  "blogPost": [
${items}
  ]
}
</script>`;
}

function updateHubPage(hubPath, article) {
  let html = readFileSync(hubPath, 'utf8');

  const startIdx = html.indexOf(CARDS_START);
  const endIdx = html.indexOf(CARDS_END);
  if (startIdx === -1 || endIdx === -1) {
    throw new Error(`${hubPath} is missing BLOG_CARDS_START/END markers — can't safely add a card`);
  }
  // Insert as a new line directly before CARDS_END's own line, reusing that
  // line's existing indentation rather than stacking a second copy of it.
  const lineStart = html.lastIndexOf('\n', endIdx) + 1;
  const indent = html.slice(lineStart, endIdx);
  const newCard = buildCardHtml(article);
  html = `${html.slice(0, lineStart)}${newCard}\n${indent}${html.slice(endIdx)}`;

  const scriptRe = /<script type="application\/ld\+json">\s*([\s\S]*?)<\/script>/;
  const match = html.match(scriptRe);
  if (!match) throw new Error(`${hubPath}: could not find a JSON-LD script block`);

  let data;
  try {
    data = JSON.parse(match[1]);
  } catch (err) {
    throw new Error(`${hubPath}: JSON-LD block is not valid JSON — refusing to touch it (${err.message})`);
  }
  if (data['@type'] !== 'Blog' || !Array.isArray(data.blogPost)) {
    throw new Error(`${hubPath}: first JSON-LD script isn't the expected Blog type`);
  }

  const newScript = buildJsonLdScript(data, {
    headline: article.title,
    url: `${SITE_ORIGIN}/blog/${article.slug}/`,
  });
  html = html.replace(scriptRe, newScript);

  writeFileSync(hubPath, html, 'utf8');
}

export { updateHubPage };
