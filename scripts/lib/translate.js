// Thin wrapper around @vitalets/google-translate-api (an unofficial,
// keyless client for translate.google.com — not the paid, ToS-compliant
// Google Cloud Translation API). Chosen over the package name in the
// original brief, `google-translate-api-next`, which hasn't been published
// since 2022; this fork was last updated January 2025.
//
// IMPORTANT CAVEAT: because this hits Google's public web endpoint rather
// than an authorized API, it has no uptime/rate-limit guarantee and Google
// can change or block it at any time without notice — this is the tradeoff
// for zero cost and zero API key. If translation calls start failing
// consistently in the GitHub Actions run, that's the most likely cause;
// the workflow surfaces failures via a non-zero exit code rather than
// publishing partial/broken language sets.

import { translate as googleTranslate } from '@vitalets/google-translate-api';
import { LANG_META } from './lang-meta.js';

const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 4000;

// Free MT will happily translate half of a proper noun and leave the rest
// (confirmed while testing this pipeline: "SyllabusTLDR" came back as
// "Programa de estudiosTLDR" in Spanish — "Syllabus" got translated,
// "TLDR" didn't). Anything that's an EXACT match for one of these is
// passed through untouched instead of round-tripped through translation.
// This only protects exact matches, not the brand name embedded inside a
// longer sentence — that's a known limitation of the keyless-MT approach,
// documented in the project report rather than solved here.
const DO_NOT_TRANSLATE = new Set(['SyllabusTLDR', 'EIGHTFINITY LTD', 'EIGHTFINITY']);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// A single article run makes ~15-20 calls per language x 9 languages, back
// to back. Firing them with no pacing at all is what tripped a real 429
// while testing this pipeline locally, after roughly a hundred calls in a
// couple of minutes. This fixed gap between every call is a blunt fix, not
// a guarantee — Google's actual limit is undocumented and can differ for
// GitHub's shared runner IPs, which is why the CI workflow treats a
// translation failure as fatal (non-zero exit, no PR opened) rather than
// silently publishing a partially-translated language.
const INTER_CALL_DELAY_MS = 600;

/** Translates a single plain-text string from English into `lang`. Returns the source string unchanged for lang === 'en' or for an exact protected-term match. */
async function translateString(text, lang) {
  if (lang === 'en' || !text || !text.trim()) return text;
  if (DO_NOT_TRANSLATE.has(text.trim())) return text;
  const googleCode = LANG_META[lang].googleCode;

  let lastError;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      await sleep(INTER_CALL_DELAY_MS);
      const { text: translated } = await googleTranslate(text, { from: 'en', to: googleCode });
      return translated;
    } catch (err) {
      lastError = err;
      if (attempt < MAX_ATTEMPTS) await sleep(RETRY_DELAY_MS * attempt * 2);
    }
  }
  throw new Error(`Translation failed for lang=${lang} after ${MAX_ATTEMPTS} attempts: ${lastError.message}`);
}

/**
 * Translates every leaf string in a structured article's sections (see
 * content-queue/README.md for the schema) into `lang`, preserving structure.
 * HTML tags are never present in section text/table/blockquote fields by
 * schema convention, so nothing needs to be masked out before translating —
 * only link anchor text (already split into its own leaf string) and plain
 * prose ever reach the translator.
 */
async function translateArticle(article, lang) {
  if (lang === 'en') return article;

  const title = await translateString(article.title, lang);
  const metaDescription = await translateString(article.metaDescription, lang);
  const ogDescription = await translateString(article.ogDescription, lang);
  const breadcrumbLabel = await translateString(article.breadcrumbLabel, lang);

  const sections = [];
  for (const section of article.sections) {
    if (section.type === 'paragraph') {
      const text = await translateString(section.text, lang);
      const links = [];
      for (const link of section.links || []) {
        links.push({ ...link, text: await translateString(link.text, lang) });
      }
      sections.push({ ...section, text, links });
    } else if (section.type === 'heading') {
      const text = await translateString(section.text, lang);
      const body = section.body ? await translateString(section.body, lang) : section.body;
      const links = [];
      for (const link of section.links || []) {
        links.push({ ...link, text: await translateString(link.text, lang) });
      }
      sections.push({ ...section, text, body, links });
    } else if (section.type === 'table') {
      const title = section.title ? await translateString(section.title, lang) : section.title;
      const headers = [];
      for (const h of section.headers) headers.push(await translateString(h, lang));
      const rows = [];
      for (const row of section.rows) {
        const translatedRow = [];
        for (const cell of row) translatedRow.push(await translateString(cell, lang));
        rows.push(translatedRow);
      }
      sections.push({ ...section, title, headers, rows });
    } else if (section.type === 'blockquote') {
      sections.push({
        ...section,
        label: await translateString(section.label, lang),
        text: await translateString(section.text, lang),
      });
    } else {
      throw new Error(`Unknown section type "${section.type}" in article "${article.slug}"`);
    }
  }

  return { ...article, title, metaDescription, ogDescription, breadcrumbLabel, sections };
}

export { translateString, translateArticle };
