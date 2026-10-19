import type { Finding } from "./findings.js";

export const SUMMARY_START = "<!-- cxbot:summary:start -->";
export const SUMMARY_END = "<!-- cxbot:summary:end -->";

export const SUGGESTION_START = "<!-- cxbot:suggestion:start -->";
export const SUGGESTION_END = "<!-- cxbot:suggestion:end -->";

export const PROMPT_FOR_AGENTS_LABEL = "🤖 Prompt for AI Agents";

export const CHECK_RUN_NAME = "CxPRBot / triage";

export const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;

export function severityRollup(findings: Finding[]): string {
  const counts = new Map<string, number>(SEVERITIES.map((s) => [s, 0]));
  for (const finding of findings) counts.set(finding.severity, (counts.get(finding.severity) ?? 0) + 1);
  const parts = SEVERITIES.map((s) => `${s} ${counts.get(s) ?? 0}`);
  return `**Severity roll-up:** ${parts.join(" · ")}`;
}

export function renderAgentPromptBlock(finding: Finding): string {
  const cwe = finding.cwe ? ` (CWE-${finding.cwe})` : "";
  const verified = finding.verified === undefined ? "" : ` Verified by scanner: ${finding.verified}.`;
  return [
    `**${PROMPT_FOR_AGENTS_LABEL}**`,
    [
      "```",
      `Fix the ${finding.severity} ${finding.scanner} finding "${finding.title}" at ${finding.file}:${finding.line}${cwe}.`,
      "Verify the issue still exists in the current code before changing anything,",
      "make the smallest change that resolves it, and run the relevant tests.",
      verified.trim(),
      "```"
    ]
      .filter((line) => line !== "")
      .join("\n")
  ].join("\n\n");
}

export interface Provenance {
  runId: string;
  profile: string;
  configSource: string;
  model: string;
}

export function findingMarker(id: string): string {
  return `<!-- cxbot:f:${id} -->`;
}

export function renderInlineComment(
  finding: Finding,
  body: string,
  options: { suggestion?: string; provenance?: Provenance } = {}
): string {
  const parts = [
    findingMarker(finding.id),
    `**[${finding.severity}] ${finding.scanner}** — ${finding.title} at \`${finding.file}:${finding.line}\`${
      finding.cwe ? ` (CWE-${finding.cwe})` : ""
    }`,
    body,
    renderAgentPromptBlock(finding)
  ];
  if (options.suggestion) {
    parts.push(
      `${SUGGESTION_START}\n\`\`\`suggestion\n${options.suggestion}\n\`\`\`\n${SUGGESTION_END}`
    );
  }
  if (options.provenance) {
    parts.push(provenanceLine(options.provenance, finding.verified));
  }
  return parts.join("\n\n");
}

export function renderSummary(body: string, provenance: Provenance, findingCount: number): string {
  return [
    SUMMARY_START,
    body,
    `**${findingCount} finding(s) triaged.**`,
    provenanceLine(provenance),
    SUMMARY_END
  ].join("\n\n");
}

export function provenanceLine(provenance: Provenance, verified?: boolean): string {
  const verifiedTag = verified === undefined ? "" : ` · verified: ${verified}`;
  return `<sub>cxbot · run ${provenance.runId} · profile ${provenance.profile} · config ${provenance.configSource} · model ${provenance.model}${verifiedTag}</sub>`;
}

export const COMMENT_BODY_LIMIT = 65536;

export function truncateForComment(markdown: string): string {
  if (markdown.length <= COMMENT_BODY_LIMIT) return markdown;
  return `${markdown.slice(0, COMMENT_BODY_LIMIT - 40)}\n\n… _truncated by cxbot_`;
}

export const LOCK_TTL_MS = 10 * 60 * 1000;

const LOCK_PATTERN = /<!-- cxbot:lock:(\d+):([^ ]*) -->/;

export function renderLockComment(nowMs: number, runId: string): string {
  return `<!-- cxbot:lock:${nowMs}:${runId} -->`;
}

export interface LockRecord {
  commentId: number;
  atMs: number;
  runId: string;
}

export function findLock(comments: Array<{ id: number; body: string }>): LockRecord | undefined {
  for (const comment of comments) {
    const match = LOCK_PATTERN.exec(comment.body);
    if (match?.[1] !== undefined) {
      return { commentId: comment.id, atMs: Number(match[1]), runId: match[2] ?? "" };
    }
  }
  return undefined;
}
