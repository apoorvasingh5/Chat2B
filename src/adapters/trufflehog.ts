import { findingId, type Finding } from "../findings.js";

export interface TrufflehogOptions {
  requireVerified?: boolean;
}

interface TrufflehogSource {
  file?: string;
  line?: number;
  commit?: string;
}

interface TrufflehogEntry {
  DetectorName?: string;
  DetectorType?: number | string;
  DecoderName?: string;
  Verified?: boolean;
  Raw?: string;
  Redacted?: string;
  ExtraData?: Record<string, unknown>;
  SourceMetadata?: {
    Data?: {
      Git?: TrufflehogSource;
      Filesystem?: TrufflehogSource;
    } & Partial<TrufflehogSource>;
  };
}

function sourceOf(entry: TrufflehogEntry): TrufflehogSource {
  const data = entry.SourceMetadata?.Data;
  if (!data) return {};
  return data.Git ?? data.Filesystem ?? (data as TrufflehogSource);
}

function detectorLabel(entry: TrufflehogEntry): string {
  return entry.DetectorName ?? String(entry.DetectorType ?? "unknown detector");
}

export function parseTrufflehogJsonl(
  jsonl: string,
  options: TrufflehogOptions = {}
): Finding[] {
  const findings: Finding[] = [];
  for (const rawLine of jsonl.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    let entry: TrufflehogEntry;
    try {
      entry = JSON.parse(line) as TrufflehogEntry;
    } catch {
      continue;
    }
    if (options.requireVerified && entry.Verified !== true) continue;

    const source = sourceOf(entry);
    const file = source.file ?? "";
    const lineNumber = source.line ?? 0;
    const detector = detectorLabel(entry);
    const commit = source.commit;

    const detailsParts = [`TruffleHog detected ${detector}`];
    if (entry.Redacted) detailsParts.push(`match: ${entry.Redacted}`);
    if (commit) detailsParts.push(`commit: ${commit}`);

    findings.push({
      id: findingId({
        scanner: "trufflehog",
        file,
        line: lineNumber,
        rule: detector
      }),
      scanner: "trufflehog",
      severity: entry.Verified ? "critical" : "medium",
      title: `${detector} secret`,
      file,
      line: lineNumber,
      verified: entry.Verified === true,
      details: detailsParts.join(" — "),
      rawRef: file ? `${file}:${lineNumber}` : undefined
    });
  }
  return findings;
}
