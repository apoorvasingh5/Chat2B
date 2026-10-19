import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { parseCxOneSarif } from "../src/adapters/cxone.js";

const fixture = readFileSync(
  fileURLToPath(new URL("./fixtures/cxone.sarif", import.meta.url)),
  "utf8"
);

describe("parseCxOneSarif", () => {
  it("parses all results with file, line, and rule metadata", () => {
    const findings = parseCxOneSarif(fixture);
    expect(findings).toHaveLength(3);
    expect(findings[0]).toMatchObject({
      scanner: "cxone",
      title: "SQL Injection",
      file: "src/main/java/com/cx/App.java",
      line: 87,
      cwe: "89",
      severity: "high"
    });
    expect(findings[1]).toMatchObject({
      title: "Reflected Cross-Site Scripting",
      file: "src/web/Search.jsx",
      line: 33,
      cwe: "79",
      severity: "medium"
    });
    expect(findings[2]).toMatchObject({ cwe: "327", severity: "low" });
  });

  it("honors newOnly by dropping unchanged baseline results", () => {
    const findings = parseCxOneSarif(fixture, { newOnly: true });
    expect(findings).toHaveLength(2);
    expect(findings.every((f) => f.file !== "src/web/Search.jsx")).toBe(true);
  });

  it("produces stable ids across parses", () => {
    const a = parseCxOneSarif(fixture).map((f) => f.id);
    const b = parseCxOneSarif(fixture).map((f) => f.id);
    expect(a).toEqual(b);
    expect(new Set(a).size).toBe(3);
  });

  it("carries fix hint and help URI when present", () => {
    const findings = parseCxOneSarif(fixture);
    expect(findings[0]?.fixHint).toContain("parameterized queries");
    expect(findings[0]?.rawRef).toBe(
      "https://checkmarx.com/knowledge/knowledge-articles/sql-injection/"
    );
    expect(findings[2]?.rawRef).toBeUndefined();
  });

  it("falls back to SARIF level mapping when no severity property", () => {
    const minimal = JSON.stringify({
      version: "2.1.0",
      runs: [{ results: [{ level: "error", message: { text: "boom" } }] }]
    });
    const findings = parseCxOneSarif(minimal);
    expect(findings[0]).toMatchObject({ severity: "high", file: "", line: 0 });
  });
});
