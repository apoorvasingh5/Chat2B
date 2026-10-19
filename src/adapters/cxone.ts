import {
  findingId,
  normalizeSeverity,
  severityFromSecurityScore,
  type Finding,
  type Severity
} from "../findings.js";

export interface CxOneOptions {
  newOnly?: boolean;
}

interface SarifRegion {
  startLine?: number;
}

interface SarifLocation {
  physicalLocation?: {
    artifactLocation?: { uri?: string };
    region?: SarifRegion;
  };
}

interface SarifRule {
  id?: string;
  name?: string;
  shortDescription?: { text?: string };
  help?: { text?: string };
  helpUri?: string;
  properties?: {
    cwe?: string | string[];
    tags?: string[];
    "security-severity"?: string;
    severity?: string;
  };
}

interface SarifResult {
  ruleId?: string;
  level?: string;
  message?: { text?: string };
  locations?: SarifLocation[];
  baselineState?: string;
  properties?: {
    severity?: string;
    Severity?: string;
    cwe?: string;
    "security-severity"?: string;
  };
}

interface SarifLog {
  runs?: Array<{
    tool?: {
      driver?: {
        name?: string;
        rules?: SarifRule[];
      };
    };
    results?: SarifResult[];
  }>;
}

function cweFromTags(tags: string[] | undefined): string | undefined {
  if (!tags) return undefined;
  for (const tag of tags) {
    const match = /cwe[/-](\d+)/i.exec(tag);
    if (match?.[1]) return match[1];
  }
  return undefined;
}

function firstString(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) return value[0];
  return value;
}

function resolveSeverity(result: SarifResult, rule: SarifRule | undefined): Severity {
  const explicit =
    result.properties?.severity ??
    result.properties?.Severity ??
    rule?.properties?.severity;
  const normalized = normalizeSeverity(explicit);
  if (normalized) return normalized;

  const score = result.properties?.["security-severity"] ?? rule?.properties?.["security-severity"];
  if (score !== undefined) return severityFromSecurityScore(score);

  return normalizeSeverity(result.level) ?? "medium";
}

export function parseCxOneSarif(sarifJson: string, options: CxOneOptions = {}): Finding[] {
  const log = JSON.parse(sarifJson) as SarifLog;
  const run = log.runs?.[0];
  const results = run?.results ?? [];
  const rulesById = new Map<string, SarifRule>();
  for (const rule of run?.tool?.driver?.rules ?? []) {
    if (rule.id) rulesById.set(rule.id, rule);
  }

  const findings: Finding[] = [];
  for (const result of results) {
    if (options.newOnly && result.baselineState === "unchanged") continue;

    const ruleId = result.ruleId ?? "unknown-rule";
    const rule = rulesById.get(ruleId);
    const location = result.locations?.[0]?.physicalLocation;
    const file = location?.artifactLocation?.uri ?? "";
    const line = location?.region?.startLine ?? 0;
    const title = rule?.shortDescription?.text ?? rule?.name ?? ruleId;

    const cwe =
      result.properties?.cwe ??
      firstString(rule?.properties?.cwe) ??
      cweFromTags(rule?.properties?.tags);

    findings.push({
      id: findingId({ scanner: "cxone", file, line, rule: ruleId }),
      scanner: "cxone",
      severity: resolveSeverity(result, rule),
      title,
      file,
      line,
      cwe,
      details: result.message?.text ?? title,
      fixHint: rule?.help?.text,
      rawRef: rule?.helpUri
    });
  }
  return findings;
}
