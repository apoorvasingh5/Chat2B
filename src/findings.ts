import { createHash } from "node:crypto";

export type ScannerId = "trufflehog" | "cxone";

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Finding {
  id: string;
  scanner: ScannerId;
  severity: Severity;
  title: string;
  file: string;
  line: number;
  cwe?: string;
  cve?: string;
  verified?: boolean;
  details: string;
  fixHint?: string;
  rawRef?: string;
}

export interface FindingIdentityParts {
  scanner: ScannerId;
  file: string;
  line: number;
  rule: string;
}

export function findingId(parts: FindingIdentityParts): string {
  const key = `${parts.scanner}|${parts.file}|${parts.line}|${parts.rule}`;
  return createHash("sha256").update(key).digest("hex").slice(0, 16);
}

const SEVERITY_ALIASES: Record<string, Severity> = {
  critical: "critical",
  high: "high",
  medium: "medium",
  low: "low",
  info: "info",
  error: "high",
  warning: "medium",
  note: "low",
  none: "info"
};

export function normalizeSeverity(raw: string | undefined): Severity | undefined {
  if (!raw) return undefined;
  return SEVERITY_ALIASES[raw.trim().toLowerCase()];
}

export function severityFromSecurityScore(score: string | number): Severity {
  const n = typeof score === "number" ? score : Number.parseFloat(score);
  if (Number.isNaN(n)) return "medium";
  if (n >= 9) return "critical";
  if (n >= 7) return "high";
  if (n >= 4) return "medium";
  return "low";
}
