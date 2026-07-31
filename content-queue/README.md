# Content queue

This folder is the hand-off point between **writing** an article and
**publishing** it. `scripts/publish-weekly.js` (run automatically by
`.github/workflows/automatic-blog-publisher.yml`, Tue/Fri 09:00 UTC, and
manually via `npm run publish-weekly`) never writes original article prose —
it only translates and distributes whatever's already sitting in
`pending/`. Someone (Sean, or a Claude Code session) has to author the
English article first and drop it here. This is a deliberate choice: doing
it this way means the automation needs zero API keys/secrets, because the
one step that genuinely requires a real LLM — writing new, on-brand,
E-E-A-T-compliant prose — happens locally, not unattended in CI.

## Workflow

1. Write the next English article as a JSON file (schema below) and save it
   into `content-queue/pending/` with a filename like
   `2026-08-04-some-slug.json` — the date prefix controls processing order
   (oldest first), it's not otherwise used.
2. When the schedule fires (or you run `npm run publish-weekly` manually),
   the pipeline picks the oldest pending file, translates the body content
   into the other 9 site languages using a free translation package,
   renders all 10 language pages, updates `sitemap.xml`, moves the queue
   file to `published/`, and opens a pull request with everything for
   review. Nothing goes live until that PR is merged.
3. If `pending/` is empty when the schedule fires, the run exits cleanly
   with no PR — check `blog/BACKLOG.md` for the next topic and write it.

## Article schema

```json
{
  "slug": "kebab-case-url-slug",
  "category": "Short category label shown above the H1",
  "breadcrumbLabel": "Short label for the breadcrumb trail",
  "title": "Full article title",
  "metaDescription": "150-160 char meta description",
  "ogDescription": "Open Graph description (can differ slightly from meta)",
  "readTimeMinutes": 9,
  "sections": [
    { "type": "paragraph", "text": "Plain prose. Use {{link1}} as an inline placeholder for a link.", "links": [
      { "marker": "{{link1}}", "text": "anchor text", "url": "/blog/other-article-slug/" }
    ] },
    { "type": "heading", "text": "Subsection heading", "body": "Optional paragraph directly under the heading, same link-marker rules as above." },
    { "type": "table", "title": "Optional heading above the table", "headers": ["Col A", "Col B", "Col C"], "rows": [["...", "...", "..."]] },
    { "type": "blockquote", "label": "Pro Tip", "text": "Callout text." }
  ]
}
```

Notes:
- `links[].url` starting with `/blog/` or exactly `/` gets the right
  language prefix automatically for each translated page (e.g.
  `/blog/x/` becomes `/es/blog/x/` on the Spanish page). URLs to
  English-only pages (`/about/`, `/contact/`, `/privacy-policy.html`) are
  left unchanged on every language's page, matching the rest of the site.
- Every field except `links` gets machine-translated per language. Page
  chrome (nav, footer, author box, consent banner) is **not** translated
  per-article — it's a static, human-curated table in
  `scripts/lib/chrome-strings.js`, reused for every article. If you add an
  11th site language, add it there and to `LANG_ORDER` in
  `scripts/lib/lang-meta.js` (and `gen_i18n.py` for the app itself).
- `datePublished`/`dateModified` are set automatically to the date the
  pipeline runs, not written in the queue file.
- The exact author-box copy, banned-phrase rules, and E-E-A-T voice this
  English source should follow live in
  `~/.claude/skills/one-page-site/templates/eeat-article-prompt-template.md`.
