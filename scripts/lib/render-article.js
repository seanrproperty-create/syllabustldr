// Renders a full localized blog article HTML page from a structured
// article object (see content-queue/README.md for the schema) plus the
// static chrome-strings table. The output must stay byte-for-byte
// consistent in structure/classes with the hand-authored articles already
// live under /blog/ — this is effectively that template, parameterized.

import { LANG_META, articleUrl, homeUrl, LANG_ORDER, SITE_ORIGIN } from './lang-meta.js';
import { CHROME_STRINGS } from './chrome-strings.js';

const FAVICON_DATA_URI = 'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%20100%20100%22%3E%3Cdefs%3E%3ClinearGradient%20id%3D%22g%22%20x1%3D%220%22%20y1%3D%220%22%20x2%3D%221%22%20y2%3D%221%22%3E%3Cstop%20offset%3D%220%22%20stop-color%3D%22%23f97316%22/%3E%3Cstop%20offset%3D%221%22%20stop-color%3D%22%23db2777%22/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect%20width%3D%22100%22%20height%3D%22100%22%20rx%3D%2224%22%20fill%3D%22url%28%2523g%29%22/%3E%3Cpath%20d%3D%22M56%2012%20L26%2056%20H45%20L38%2088%20L74%2040%20H52%20Z%22%20fill%3D%22white%22/%3E%3C/svg%3E';

// The blog hub page (the article listing at /blog/) only exists in
// English — building translated hub pages is a separate, not-yet-built
// feature (see the project report). Every "back to blog" link points at
// the one hub that actually exists, in every language, rather than a
// per-language hub that would 404. Links to specific OTHER ARTICLES
// (via localizeUrl below) are unaffected — once an article's rollout
// finishes, its translated pages genuinely do exist per language.
const BLOG_HUB_URL = `${SITE_ORIGIN}/blog/`;

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** Internal `/` and `/blog/...` links get the language prefix; everything else (external, mailto:, English-only pages like /about/) passes through unchanged. */
function localizeUrl(url, lang) {
  const prefix = LANG_META[lang].homePrefix;
  if (url === '/') return `${prefix}/`;
  if (url.startsWith('/blog/')) return prefix + url;
  return url;
}

function renderParagraphHtml(text, links, lang) {
  let html = escapeHtml(text);
  for (const link of links || []) {
    const token = escapeHtml(link.marker);
    const href = localizeUrl(link.url, lang);
    const anchor = `<a href="${href}" class="text-orange-400 hover:text-orange-300 underline underline-offset-2">${escapeHtml(link.text)}</a>`;
    html = html.split(token).join(anchor);
  }
  return html;
}

function renderSection(section, lang) {
  if (section.type === 'paragraph') {
    return `            <p>${renderParagraphHtml(section.text, section.links, lang)}</p>`;
  }
  if (section.type === 'heading') {
    return [
      '            <section class="space-y-3">',
      `                <h2 class="font-display text-xl font-bold text-white">${escapeHtml(section.text)}</h2>`,
      section.body ? `                <p>${renderParagraphHtml(section.body, section.links, lang)}</p>` : '',
      '            </section>',
    ].filter(Boolean).join('\n');
  }
  if (section.type === 'table') {
    const headerCells = section.headers.map((h) => `                                <th class="px-4 py-3">${escapeHtml(h)}</th>`).join('\n');
    const rows = section.rows.map((row) => {
      const cells = row.map((cell, i) => {
        const emphasize = i === 0 ? ' text-white font-medium' : '';
        return `                                <td class="px-4 py-3${emphasize}">${escapeHtml(cell)}</td>`;
      }).join('\n');
      return `                            <tr>\n${cells}\n                            </tr>`;
    }).join('\n');
    return [
      '            <section class="space-y-3">',
      section.title ? `                <h2 class="font-display text-xl font-bold text-white">${escapeHtml(section.title)}</h2>` : '',
      '                <div class="overflow-x-auto rounded-2xl border border-zinc-800">',
      '                    <table class="w-full text-xs text-left">',
      '                        <thead class="bg-zinc-900 text-zinc-400 uppercase tracking-wide text-[10px]">',
      '                            <tr>',
      headerCells,
      '                            </tr>',
      '                        </thead>',
      '                        <tbody class="divide-y divide-zinc-800">',
      rows,
      '                        </tbody>',
      '                    </table>',
      '                </div>',
      '            </section>',
    ].filter(Boolean).join('\n');
  }
  if (section.type === 'blockquote') {
    return [
      '            <blockquote class="border-l-4 border-orange-500 bg-zinc-900/60 rounded-r-2xl px-5 py-4 text-sm text-zinc-300">',
      `                <span class="font-bold text-orange-400 not-italic">${escapeHtml(section.label)}:</span> ${renderParagraphHtml(section.text, section.links, lang)}`,
      '            </blockquote>',
    ].join('\n');
  }
  throw new Error(`Unknown section type "${section.type}"`);
}

function buildHreflangBlock(slug) {
  const lines = LANG_ORDER.map((code) => `<link rel="alternate" hreflang="${LANG_META[code].hreflang}" href="${articleUrl(code, slug)}">`);
  lines.push(`<link rel="alternate" hreflang="x-default" href="${articleUrl('en', slug)}">`);
  return lines.join('\n');
}

/**
 * @param {object} article - structured article (see content-queue/README.md)
 * @param {string} lang - one of LANG_ORDER
 * @param {{datePublished: string, dateModified: string}} dates
 * @param {string} translatedTitle - already-translated title (or source title for 'en')
 */
function renderArticleHtml(article, lang, dates) {
  const meta = LANG_META[lang];
  const chrome = CHROME_STRINGS[lang];
  const url = articleUrl(lang, article.slug);
  const gtagId = 'G-CQT3CXF341';

  const sectionsHtml = article.sections.map((s) => renderSection(s, lang)).join('\n\n');

  return `<!DOCTYPE html>
<html lang="${lang}"${meta.dir === 'rtl' ? ' dir="rtl"' : ''}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="${FAVICON_DATA_URI}">
<title>${escapeHtml(article.title)}</title>
<meta name="description" content="${escapeHtml(article.metaDescription)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="${url}">
<meta property="og:title" content="${escapeHtml(article.title)}">
<meta property="og:description" content="${escapeHtml(article.ogDescription)}">
<meta property="og:url" content="${url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="${meta.og_locale}">
<meta name="twitter:card" content="summary">

<!-- HREFLANG_BLOCK_START -->
${buildHreflangBlock(article.slug)}
<!-- HREFLANG_BLOCK_END -->

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": ${JSON.stringify(article.title)},
  "description": ${JSON.stringify(article.metaDescription)},
  "url": ${JSON.stringify(url)},
  "mainEntityOfPage": ${JSON.stringify(url)},
  "datePublished": "${dates.datePublished}",
  "dateModified": "${dates.dateModified}",
  "inLanguage": "${meta.hreflang}",
  "author": { "@type": "Organization", "name": "EIGHTFINITY LTD Academic Engineering Team" },
  "publisher": { "@type": "Organization", "name": "EIGHTFINITY LTD", "url": "${SITE_ORIGIN}/" },
  "isPartOf": { "@type": "Blog", "name": "SyllabusTLDR Blog", "url": "${BLOG_HUB_URL}" }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": ${JSON.stringify(chrome.breadcrumbHome)}, "item": ${JSON.stringify(homeUrl(lang))} },
    { "@type": "ListItem", "position": 2, "name": ${JSON.stringify(chrome.breadcrumbBlog)}, "item": ${JSON.stringify(BLOG_HUB_URL)} },
    { "@type": "ListItem", "position": 3, "name": ${JSON.stringify(article.breadcrumbLabel)}, "item": ${JSON.stringify(url)} }
  ]
}
</script>

<!-- Consent Mode v2 — default to denied for ad/analytics storage until the
     visitor makes a choice in the cookie banner below. Must run before
     gtag.js loads so the very first hit already respects it. -->
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    wait_for_update: 500
  });
</script>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=${gtagId}"></script>
<script>
  gtag('js', new Date());
  gtag('config', '${gtagId}');
</script>

<link rel="stylesheet" href="/tailwind.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;800&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<style>
  html { scroll-behavior: smooth; }
  body { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; }
  .font-display { font-family: 'Space Grotesk', 'Inter', ui-sans-serif, sans-serif; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 999px; }
</style>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col justify-between relative overflow-x-hidden">

    <!-- HEADER -->
    <header class="border-b border-zinc-800/80 bg-zinc-950/60 backdrop-blur-xl sticky top-0 z-50 px-4 py-3">
        <div class="max-w-2xl mx-auto flex items-center justify-between">
            <a href="${homeUrl(lang)}" class="flex items-center gap-2.5">
                <div class="bg-gradient-to-br from-orange-500 to-pink-600 text-white p-2 rounded-xl shadow-lg shadow-orange-600/30">
                    <i class="fa-solid fa-bolt text-lg"></i>
                </div>
                <div>
                    <p class="font-display font-bold tracking-tight text-xl bg-gradient-to-r from-orange-400 via-pink-400 to-fuchsia-400 bg-clip-text text-transparent">SyllabusTLDR</p>
                    <p class="text-xs text-zinc-500">${escapeHtml(chrome.tagline)}</p>
                </div>
            </a>
            <a href="${homeUrl(lang)}" class="text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition flex items-center gap-1.5">
                <i class="fa-solid fa-arrow-left text-[10px]"></i> ${escapeHtml(chrome.backToApp)}
            </a>
        </div>
    </header>

    <!-- MAIN -->
    <main class="flex-grow px-4 py-10 max-w-2xl mx-auto w-full relative z-10">
        <nav class="text-xs text-zinc-500 mb-6 flex items-center gap-1.5" aria-label="Breadcrumb">
            <a href="${homeUrl(lang)}" class="hover:text-zinc-300 transition">${escapeHtml(chrome.breadcrumbHome)}</a>
            <span>/</span>
            <a href="${BLOG_HUB_URL}" class="hover:text-zinc-300 transition">${escapeHtml(chrome.breadcrumbBlog)}</a>
            <span>/</span>
            <span class="text-zinc-400">${escapeHtml(article.breadcrumbLabel)}</span>
        </nav>

        <article class="space-y-8 text-sm leading-relaxed text-zinc-300">
            <header class="space-y-2 mb-2">
                <span class="text-[11px] font-black tracking-widest text-orange-400 uppercase">${escapeHtml(article.category)}</span>
                <h1 class="font-display text-3xl font-bold tracking-tight text-white leading-tight">${escapeHtml(article.title)}</h1>
                <p class="text-xs text-zinc-500">${escapeHtml(article.readTimeMinutes)} ${escapeHtml(chrome.readTimeSuffix)} • ${escapeHtml(chrome.reviewedBy)}</p>
            </header>

${sectionsHtml}

            <div class="border-t border-zinc-800 pt-6 mt-2 text-xs text-zinc-500">
                <p class="font-bold text-zinc-300 mb-1.5">${escapeHtml(chrome.aboutAuthorHeading)}</p>
                <p>${chrome.authorBoxHtml.replace('info@eightfinity.net', '<a href="mailto:info@eightfinity.net" class="text-orange-400 hover:text-orange-300 underline underline-offset-2">info@eightfinity.net</a>')}</p>
            </div>
        </article>
    </main>

    <!-- FOOTER -->
    <footer class="px-4 py-6 text-center relative z-10 border-t border-zinc-800/60 mt-8">
        <div class="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 mb-2 text-xs">
            <a href="${homeUrl(lang)}" class="text-zinc-500 hover:text-zinc-300 transition">${escapeHtml(chrome.footerApp)}</a>
            <span class="text-zinc-700">•</span>
            <a href="/about/" class="text-zinc-500 hover:text-zinc-300 transition">${escapeHtml(chrome.footerAbout)}</a>
            <span class="text-zinc-700">•</span>
            <a href="/contact/" class="text-zinc-500 hover:text-zinc-300 transition">${escapeHtml(chrome.footerContact)}</a>
            <span class="text-zinc-700">•</span>
            <a href="${BLOG_HUB_URL}" class="text-zinc-500 hover:text-zinc-300 transition">${escapeHtml(chrome.footerBlog)}</a>
            <span class="text-zinc-700">•</span>
            <a href="/terms-of-service" class="text-zinc-500 hover:text-zinc-300 transition">${escapeHtml(chrome.footerTerms)}</a>
            <span class="text-zinc-700">•</span>
            <a href="/privacy-policy" class="text-zinc-500 hover:text-zinc-300 transition">${escapeHtml(chrome.footerPrivacy)}</a>
        </div>
        <p class="text-[11px] text-zinc-600">${escapeHtml(chrome.copyrightLine)}</p>
        <p class="text-[11px] text-zinc-700 mt-1">${escapeHtml(chrome.operatorLine)}</p>
    </footer>

    <!-- COOKIE CONSENT BANNER -->
    <div id="consent-banner" class="hidden fixed inset-x-0 bottom-0 z-[100] p-3 sm:p-4">
        <div class="max-w-xl mx-auto bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl shadow-black/50 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
            <p class="text-xs text-zinc-400 leading-relaxed flex-1">
                ${escapeHtml(chrome.consentText)}
                <a href="/privacy-policy" class="text-orange-400 hover:text-orange-300 underline underline-offset-2">${escapeHtml(chrome.footerPrivacy)}</a>.
            </p>
            <div class="flex items-center gap-2 shrink-0 w-full sm:w-auto">
                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">${escapeHtml(chrome.consentReject)}</button>
                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">${escapeHtml(chrome.consentAccept)}</button>
            </div>
        </div>
    </div>
    <script>
    (function () {
      'use strict';
      var KEY = 'stldr_consent';
      var banner = document.getElementById('consent-banner');
      var stored = null;
      try { stored = localStorage.getItem(KEY); } catch (e) {}

      function updateConsent(granted) {
        if (typeof gtag !== 'function') return;
        gtag('consent', 'update', {
          ad_storage: granted ? 'granted' : 'denied',
          ad_user_data: granted ? 'granted' : 'denied',
          ad_personalization: granted ? 'granted' : 'denied',
          analytics_storage: granted ? 'granted' : 'denied'
        });
      }

      if (stored === 'granted' || stored === 'denied') {
        updateConsent(stored === 'granted');
      } else if (banner) {
        banner.classList.remove('hidden');
      }

      function choose(granted) {
        try { localStorage.setItem(KEY, granted ? 'granted' : 'denied'); } catch (e) {}
        updateConsent(granted);
        if (banner) banner.classList.add('hidden');
      }

      var acceptBtn = document.getElementById('consent-accept');
      var rejectBtn = document.getElementById('consent-reject');
      if (acceptBtn) acceptBtn.addEventListener('click', function () { choose(true); });
      if (rejectBtn) rejectBtn.addEventListener('click', function () { choose(false); });
    })();
    </script>

</body>
</html>
`;
}

export { renderArticleHtml, escapeHtml, localizeUrl };
