import { describe, expect, it } from "vitest";
import type { Finding } from "../src/findings.js";
import {
  CHECK_RUN_NAME,
  COMMENT_BODY_LIMIT,
  findingMarker,
  renderAgentPromptBlock,
  renderInlineComment,
  renderSummary,
  severityRollup,
  truncateForComment,
  SUMMARY_START,
  SUMMARY_END
} from "../src/publisher.js";

const finding: Finding = {
  id: "a1b2c3d4e5f60718",
  scanner: "trufflehog",
  severity: "critical",
  title: "AWS secret",
  file: "config/app.yml",
  line: 42,
  cwe: "798",
  verified: true,
  details: "TruffleHog detected AWS — match: AKIA********************"
};

const provenance = {
  runId: "98765",
  profile: "balanced",
  configSource: ".cxbot.yaml",
  model: "openai/gpt-4o-mini"
};

describe("renderInlineComment", () => {
  it("stamps the stable finding marker", () => {
    const comment = renderInlineComment(finding, "Valid in current code.");
    expect(comment).toContain(`<!-- cxbot:f:${finding.id} -->`);
    expect(comment.startsWith(findingMarker(finding.id))).toBe(true);
    expect(renderInlineComment(finding, "x")).toBe(comment.replace("Valid in current code.", "x"));
  });

  it("renders severity, location, and CWE header", () => {
    const comment = renderInlineComment(finding, "body");
    expect(comment).toContain("**[critical] trufflehog** — AWS secret at `config/app.yml:42` (CWE-798)");
  });

  it("wraps fixes in native suggestion fences with cxbot boundaries", () => {
    const comment = renderInlineComment(finding, "Rotate the key.", {
      suggestion: "api_key: ${secrets.AWS_KEY}"
    });
    expect(comment).toContain("```suggestion\napi_key: ${secrets.AWS_KEY}\n```");
    expect(comment).toContain("<!-- cxbot:suggestion:start -->");
    expect(comment).toContain("<!-- cxbot:suggestion:end -->");
  });

  it("appends provenance when provided", () => {
    const comment = renderInlineComment(finding, "body", { provenance });
    expect(comment).toContain("run 98765");
    expect(comment).toContain("profile balanced");
    expect(comment).toContain("verified: true");
  });
});

describe("renderSummary", () => {
  it("wraps body in summary markers with count and provenance", () => {
    const summary = renderSummary("## Walkthrough\nAll good.", provenance, 3);
    expect(summary.startsWith(SUMMARY_START)).toBe(true);
    expect(summary.trimEnd().endsWith(SUMMARY_END)).toBe(true);
    expect(summary).toContain("**3 finding(s) triaged.**");
    expect(summary).toContain("model openai/gpt-4o-mini");
  });
});

describe("truncateForComment", () => {
  it("passes small bodies through untouched", () => {
    expect(truncateForComment("hello")).toBe("hello");
  });

  it("truncates oversized bodies with a marker", () => {
    const big = "x".repeat(COMMENT_BODY_LIMIT + 100);
    const out = truncateForComment(big);
    expect(out.length).toBeLessThanOrEqual(COMMENT_BODY_LIMIT);
    expect(out).toContain("_truncated by cxbot_");
  });
});

describe("severityRollup", () => {
  it("counts findings per severity in fixed order", () => {
    const findings: Finding[] = [
      finding,
      { ...finding, id: "b", severity: "high" },
      { ...finding, id: "c", severity: "high" },
      { ...finding, id: "d", severity: "info" }
    ];
    expect(severityRollup(findings)).toBe(
      "**Severity roll-up:** critical 1 · high 2 · medium 0 · low 0 · info 1"
    );
  });

  it("renders zeros for an empty finding list", () => {
    expect(severityRollup([])).toContain("critical 0");
    expect(severityRollup([])).toContain("info 0");
  });
});

describe("renderAgentPromptBlock", () => {
  it("includes the label and a copy-pasteable verification prompt", () => {
    const block = renderAgentPromptBlock(finding);
    expect(block).toContain("🤖 Prompt for AI Agents");
    expect(block).toContain("config/app.yml:42");
    expect(block).toContain("Verify the issue still exists");
    expect(block).toContain("smallest change");
    expect(block).toContain("Verified by scanner: true");
  });

  it("omits verification note when scanner did not verify", () => {
    const block = renderAgentPromptBlock({ ...finding, verified: undefined });
    expect(block).not.toContain("Verified by scanner");
  });
});

describe("check run name", () => {
  it("is stable for upsert dedup", () => {
    expect(CHECK_RUN_NAME).toBe("CxPRBot / triage");
  });
});
