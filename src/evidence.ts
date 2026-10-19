import { readFileSync, statSync } from "node:fs";
import { isAbsolute, resolve, sep } from "node:path";
import type { Finding } from "./findings.js";

export const EXCERPT_CONTEXT_LINES = 12;
export const MAX_EVIDENCE_BYTES = 8192;

const NUL = String.fromCharCode(0);

/**
 * Reads a line-numbered excerpt of `file` around `line` from inside `absRoot`.
 * Returns undefined for anything unsafe or unreadable: absolute paths, paths
 * escaping the root, missing files, binary content, or oversized excerpts.
 */
export function readExcerpt(
  absRoot: string,
  file: string,
  line: number | undefined
): string | undefined {
  if (isAbsolute(file)) return undefined;
  const abs = resolve(absRoot, file);
  if (abs !== absRoot && !abs.startsWith(`${absRoot}${sep}`)) return undefined;

  let text: string;
  try {
    if (!statSync(abs).isFile()) return undefined;
    text = readFileSync(abs, "utf8");
  } catch {
    return undefined;
  }
  if (text.includes(NUL)) return undefined;

  const lines = text.split(/\r?\n/);
  if (lines.length > 1 && lines[lines.length - 1] === "") lines.pop();
  const target = line !== undefined && line > 0 ? Math.min(line, lines.length) : 1;
  const start = Math.max(1, Math.min(target - EXCERPT_CONTEXT_LINES, lines.length));
  const end = Math.min(lines.length, target + EXCERPT_CONTEXT_LINES);

  const numbered = lines
    .slice(start - 1, end)
    .map((content, index) => `${String(start + index).padStart(6)} | ${content}`)
    .join("\n");
  const header = `${file}:${start}-${end}`;
  const body =
    numbered.length > MAX_EVIDENCE_BYTES
      ? `${numbered.slice(0, MAX_EVIDENCE_BYTES)}\n… (excerpt truncated)`
      : numbered;
  return `${header}\n${body}`;
}

/** Collects evidence excerpts for findings; ids without a readable file are omitted. */
export function collectEvidence(
  findings: Finding[],
  absRoot: string | undefined
): Map<string, string> {
  const evidence = new Map<string, string>();
  if (!absRoot) return evidence;
  let root: string;
  try {
    root = resolve(absRoot);
    statSync(root);
  } catch {
    return evidence;
  }
  for (const finding of findings) {
    if (evidence.has(finding.id)) continue;
    const excerpt = readExcerpt(root, finding.file, finding.line);
    if (excerpt !== undefined) evidence.set(finding.id, excerpt);
  }
  return evidence;
}
