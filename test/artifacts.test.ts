import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  buildBundle,
  loadScannerFindings,
  mergeFindings,
  readBundle,
  summarizeFindings,
  writeBundle
} from "../src/artifacts.js";
import { defaultConfig } from "../src/config.js";
import type { Finding } from "../src/findings.js";

const thPath = fileURLToPath(new URL("./fixtures/trufflehog.jsonl", import.meta.url));
const sarifPath = fileURLToPath(new URL("./fixtures/cxone.sarif", import.meta.url));

describe("loadScannerFindings", () => {
  it("loads both scanners with new-only gate on Cx One", () => {
    const findings = loadScannerFindings(
      { trufflehog: thPath, cxone: sarifPath },
      defaultConfig()
    );
    expect(findings).toHaveLength(5);
    expect(findings.map((f) => f.scanner).sort()).toEqual([
      "cxone",
      "cxone",
      "trufflehog",
      "trufflehog",
      "trufflehog"
    ]);
    expect(findings.some((f) => f.file === "src/web/Search.jsx")).toBe(false);
  });

  it("sorts by severity then file", () => {
    const findings = loadScannerFindings(
      { trufflehog: thPath, cxone: sarifPath },
      defaultConfig()
    );
    expect(findings.map((f) => f.severity)).toEqual([
      "critical",
      "critical",
      "high",
      "medium",
      "low"
    ]);
  });

  it("honors scanners.trufflehog=false", () => {
    const config = defaultConfig();
    config.scanners.trufflehog = false;
    const findings = loadScannerFindings({ trufflehog: thPath, cxone: sarifPath }, config);
    expect(findings).toHaveLength(2);
    expect(findings.every((f) => f.scanner === "cxone")).toBe(true);
  });

  it("honors scanners.cxone=false", () => {
    const config = defaultConfig();
    config.scanners.cxone = false;
    const findings = loadScannerFindings({ trufflehog: thPath, cxone: sarifPath }, config);
    expect(findings).toHaveLength(3);
    expect(findings.every((f) => f.scanner === "trufflehog")).toBe(true);
  });

  it("honors require_verified", () => {
    const config = defaultConfig();
    config.scanners.require_verified = true;
    const findings = loadScannerFindings({ trufflehog: thPath, cxone: sarifPath }, config);
    expect(findings).toHaveLength(4);
    const th = findings.filter((f) => f.scanner === "trufflehog");
    expect(th).toHaveLength(2);
    expect(th.every((f) => f.verified)).toBe(true);
  });

  it("returns empty when files are missing", () => {
    const findings = loadScannerFindings(
      { trufflehog: "nope.jsonl", cxone: "nope.sarif" },
      defaultConfig()
    );
    expect(findings).toEqual([]);
  });
});

describe("mergeFindings", () => {
  it("deduplicates by stable id across groups", () => {
    const finding: Finding = {
      id: "dup1",
      scanner: "cxone",
      severity: "high",
      title: "t",
      file: "a.ts",
      line: 1,
      details: "d"
    };
    const merged = mergeFindings([finding], [finding, { ...finding, id: "dup2" }]);
    expect(merged).toHaveLength(2);
    expect(merged.map((f) => f.id)).toEqual(["dup1", "dup2"]);
  });

  it("never leaks raw secret material after merge", () => {
    const findings = loadScannerFindings(
      { trufflehog: thPath, cxone: sarifPath },
      defaultConfig()
    );
    const serialized = JSON.stringify(findings);
    expect(serialized).not.toContain("AKIAFAKESECRETKEYVALUE1234");
    expect(serialized).not.toContain("sk_live_FAKESTRIPEKEY123456789");
  });
});

describe("summarizeFindings", () => {
  it("counts by scanner and severity", () => {
    const findings = loadScannerFindings(
      { trufflehog: thPath, cxone: sarifPath },
      defaultConfig()
    );
    const summary = summarizeFindings(findings);
    expect(summary.total).toBe(5);
    expect(summary.byScanner).toEqual({ trufflehog: 3, cxone: 2 });
    expect(summary.bySeverity).toEqual({
      critical: 2,
      high: 1,
      medium: 1,
      low: 1,
      info: 0
    });
  });

  it("returns zeroed counts for no findings", () => {
    expect(summarizeFindings([])).toEqual({
      total: 0,
      bySeverity: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
      byScanner: { trufflehog: 0, cxone: 0 }
    });
  });
});

describe("bundle round-trip", () => {
  it("writes findings.json that parses back with summary intact", () => {
    const dir = mkdtempSync(join(tmpdir(), "cxbot-"));
    try {
      const findings = loadScannerFindings(
        { trufflehog: thPath, cxone: sarifPath },
        defaultConfig()
      );
      const summary = summarizeFindings(findings);
      const out = join(dir, "findings.json");
      writeBundle(buildBundle(findings, summary, ".cxbot.yaml"), out);
      const parsed = JSON.parse(readFileSync(out, "utf8")) as ReturnType<
        typeof buildBundle
      >;
      expect(parsed.schemaVersion).toBe(1);
      expect(parsed.configSource).toBe(".cxbot.yaml");
      expect(parsed.summary).toEqual(summary);
      expect(parsed.findings).toHaveLength(5);
      expect(parsed.generatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("accepts a config file path mapping (smoke for analyze inputs)", () => {
    const dir = mkdtempSync(join(tmpdir(), "cxbot-"));
    try {
      writeFileSync(join(dir, "trufflehog.json"), readFileSync(thPath, "utf8"), "utf8");
      writeFileSync(join(dir, "cxone.sarif"), readFileSync(sarifPath, "utf8"), "utf8");
      const findings = loadScannerFindings(
        { trufflehog: join(dir, "trufflehog.json"), cxone: join(dir, "cxone.sarif") },
        defaultConfig()
      );
      expect(findings).toHaveLength(5);
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});

describe("readBundle", () => {
  it("round-trips a written bundle", () => {
    const dir = mkdtempSync(join(tmpdir(), "cxbot-"));
    try {
      const findings = loadScannerFindings(
        { trufflehog: thPath, cxone: sarifPath },
        defaultConfig()
      );
      const summary = summarizeFindings(findings);
      const out = join(dir, "findings.json");
      writeBundle(buildBundle(findings, summary, ".cxbot.yaml"), out);
      const bundle = readBundle(out);
      expect(bundle?.findings).toEqual(findings);
      expect(bundle?.summary).toEqual(summary);
      expect(bundle?.configSource).toBe(".cxbot.yaml");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("returns undefined for missing, malformed, or wrong-version bundles", () => {
    const dir = mkdtempSync(join(tmpdir(), "cxbot-"));
    try {
      expect(readBundle(join(dir, "nope.json"))).toBeUndefined();

      const garbage = join(dir, "garbage.json");
      writeFileSync(garbage, "{not json", "utf8");
      expect(readBundle(garbage)).toBeUndefined();

      const wrongVersion = join(dir, "v2.json");
      writeFileSync(wrongVersion, JSON.stringify({ schemaVersion: 2, findings: [] }), "utf8");
      expect(readBundle(wrongVersion)).toBeUndefined();

      const notArray = join(dir, "na.json");
      writeFileSync(notArray, JSON.stringify({ schemaVersion: 1, findings: "x" }), "utf8");
      expect(readBundle(notArray)).toBeUndefined();
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
