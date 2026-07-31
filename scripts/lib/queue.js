// Reads/moves queued English articles through three states:
//   pending/     someone (a human, or a Claude Code session — never this
//                script) wrote an article and dropped it here.
//   in-progress/ English is live and the 9-language rollout is under way,
//                staged over several runs (see publish-weekly.js) so
//                translation doesn't fire ~150 calls at once and trip the
//                free translate endpoint's rate limit.
//   published/   every language is done; rollout complete.
//
// This module never invents or writes article prose itself, and never
// decides how many languages to publish in a given run — that's
// publish-weekly.js's job. It only tracks which article is where.

import { readdirSync, readFileSync, renameSync, existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const PENDING_DIR = 'content-queue/pending';
const IN_PROGRESS_DIR = 'content-queue/in-progress';
const PUBLISHED_DIR = 'content-queue/published';

function ensureDirs() {
  for (const dir of [PENDING_DIR, IN_PROGRESS_DIR, PUBLISHED_DIR]) {
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  }
}

function readJsonFilesIn(dir) {
  ensureDirs();
  return readdirSync(dir).filter((f) => f.endsWith('.json')).sort();
}

/** The article whose rollout is currently under way, or null if none. There should only ever be zero or one. */
function getInProgressArticle() {
  const files = readJsonFilesIn(IN_PROGRESS_DIR);
  if (files.length === 0) return null;
  if (files.length > 1) {
    throw new Error(`content-queue/in-progress has ${files.length} articles — expected at most 1. Resolve manually before running again.`);
  }
  const filename = files[0];
  const article = JSON.parse(readFileSync(join(IN_PROGRESS_DIR, filename), 'utf8'));
  return { filename, article };
}

/** Oldest-queued pending article (by filename, which should be date-prefixed), or null if the queue is empty. */
function getNextQueuedArticle() {
  const files = readJsonFilesIn(PENDING_DIR);
  if (files.length === 0) return null;
  const filename = files[0];
  const article = JSON.parse(readFileSync(join(PENDING_DIR, filename), 'utf8'));
  return { filename, article };
}

function countPending() {
  return readJsonFilesIn(PENDING_DIR).length;
}

/** pending/<filename> -> in-progress/<filename>. Call once, when English is first published for this article. */
function startRollout(filename) {
  ensureDirs();
  renameSync(join(PENDING_DIR, filename), join(IN_PROGRESS_DIR, filename));
}

/** in-progress/<filename> -> published/<filename>. Call once every non-English language is on disk. */
function completeRollout(filename) {
  ensureDirs();
  renameSync(join(IN_PROGRESS_DIR, filename), join(PUBLISHED_DIR, filename));
}

export {
  getInProgressArticle,
  getNextQueuedArticle,
  countPending,
  startRollout,
  completeRollout,
  PENDING_DIR,
  IN_PROGRESS_DIR,
  PUBLISHED_DIR,
};
