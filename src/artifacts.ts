import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { parseCxOneSarif } from "./adapters/cxone.js";
import { parseTrufflehogJsonl } from "./adapters/trufflehog.js";
import type { CxbotConfig } from "./config.js";
import type { Finding, ScannerId, Severity } from "./findings.js";

export interface ScannerFiles {
  trufflehog?: string;
  cxone?: string;
}

export interface FindingsSummary {
  total: number;
  bySeverity: Record<Severity, number>;
  byScanner: Record<ScannerId, number>;
}

export interface FindingsBundle {
  schemaVersion: 1;
  generatedAt: string;
  configSource: string;
  summary: FindingsSummary;
  findings: Finding[];
}

const SEVERITY_RANK: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4
};

export function mergeFindings(...groups: Finding[][]): Finding[] {
  const byId = new Map<string, Finding>();
  for (const group of groups) {
    for (const finding of group) {
      if (!byId.has(finding.id)) byId.set(finding.id, finding);
    }
  }
  return [...byId.values()].sort(
    (a, b) =>
      SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity] ||
      a.file.localeCompare(b.file) ||
      a.line - b.line
  );
}

export function loadScannerFindings(files: ScannerFiles, config: CxbotConfig): Finding[] {
  const groups: Finding[][] = [];

  if (config.scanners.trufflehog && files.trufflehog && existsSync(files.trufflehog)) {
    groups.push(
      parseTrufflehogJsonl(readFileSync(files.trufflehog, "utf8"), {
        requireVerified: config.scanners.require_verified
      })
    );
  }

  if (config.scanners.cxone && files.cxone && existsSync(files.cxone)) {
    groups.push(parseCxOneSarif(readFileSync(files.cxone, "utf8"), { newOnly: true }));
  }

  return mergeFindings(...groups);
}

export function summarizeFindings(findings: Finding[]): FindingsSummary {
  const summary: FindingsSummary = {
    total: findings.length,
    bySeverity: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
    byScanner: { trufflehog: 0, cxone: 0 }
  };
  for (const finding of findings) {
    summary.bySeverity[finding.severity] += 1;
    summary.byScanner[finding.scanner] += 1;
  }
  return summary;
}

export function buildBundle(
  findings: Finding[],
  summary: FindingsSummary,
  configSource: string
): FindingsBundle {
  return {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    configSource,
    summary,
    findings
  };
}

export function writeBundle(bundle: FindingsBundle, outPath: string): void {
  writeFileSync(outPath, `${JSON.stringify(bundle, null, 2)}\n`, "utf8");
}

export function readBundle(bundlePath: string): FindingsBundle | undefined {
  if (!existsSync(bundlePath)) return undefined;
  try {
    const parsed = JSON.parse(readFileSync(bundlePath, "utf8")) as Partial<FindingsBundle>;
    if (parsed.schemaVersion !== 1 || !Array.isArray(parsed.findings)) return undefined;
    return {
      schemaVersion: 1,
      generatedAt: parsed.generatedAt ?? "",
      configSource: parsed.configSource ?? "unknown",
      summary: parsed.summary ?? summarizeFindings(parsed.findings),
      findings: parsed.findings
    };
  } catch {
    return undefined;
  }
}
