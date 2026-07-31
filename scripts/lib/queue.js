// Reads/archives queued English articles. The queue is the hand-off point
// between "someone wrote an article" (a human, or a Claude Code session —
// never this script) and "the pipeline distributes it into 10 languages."
// This script never invents or writes article prose itself.

import { readdirSync, readFileSync, renameSync, existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const PENDING_DIR = 'content-queue/pending';
const PUBLISHED_DIR = 'content-queue/published';

function ensureDirs() {
  for (const dir of [PENDING_DIR, PUBLISHED_DIR]) {
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  }
}

/** Returns the oldest-queued pending article (by filename, which should be date-prefixed), or null if the queue is empty. */
function getNextQueuedArticle() {
  ensureDirs();
  const files = readdirSync(PENDING_DIR)
    .filter((f) => f.endsWith('.json'))
    .sort();
  if (files.length === 0) return null;

  const filename = files[0];
  const raw = readFileSync(join(PENDING_DIR, filename), 'utf8');
  const article = JSON.parse(raw);
  return { filename, article };
}

function countPending() {
  ensureDirs();
  return readdirSync(PENDING_DIR).filter((f) => f.endsWith('.json')).length;
}

function archiveQueuedArticle(filename) {
  ensureDirs();
  renameSync(join(PENDING_DIR, filename), join(PUBLISHED_DIR, filename));
}

export { getNextQueuedArticle, archiveQueuedArticle, countPending, PENDING_DIR, PUBLISHED_DIR };
