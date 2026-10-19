import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { Finding } from "../src/findings.js";
import { collectEvidence, EXCERPT_CONTEXT_LINES, readExcerpt } from "../src/evidence.js";

function makeFinding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: "f000000000000001",
    scanner: "cxone",
    severity: "high",
    title: "SQL Injection",
    file: "src/app.ts",
    line: 20,
    details: "concatenated query",
    ...overrides
  };
}

describe("evidence", () => {
  let root: string;

  beforeEach(() => {
    root = mkdtempSync(join(tmpdir(), "cxbot-ev-"));
  });

  afterEach(() => {
    rmSync(root, { recursive: true, force: true });
  });

  it("returns a line-numbered excerpt around the finding line", () => {
    const lines = Array.from({ length: 60 }, (_, i) => `const line${i + 1} = ${i + 1};`);
    writeFileSync(join(root, "src-file.ts"), lines.join("\n"), "utf8");
    mkdirSync(join(root, "src"), { recursive: true });
    writeFileSync(join(root, "src", "app.ts"), lines.join("\n"), "utf8");

    const excerpt = readExcerpt(root, "src/app.ts", 20);
    expect(excerpt).toBeDefined();
    const [header, ...rest] = (excerpt ?? "").split("\n");
    const start = 20 - EXCERPT_CONTEXT_LINES;
    const end = 20 + EXCERPT_CONTEXT_LINES;
    expect(header).toBe(`src/app.ts:${start}-${end}`);
    expect(rest[0]).toContain(`${String(start).padStart(6)} | `);
    expect(excerpt).toContain("const line20 = 20;");
    expect(rest).toHaveLength(2 * EXCERPT_CONTEXT_LINES + 1);
  });

  it("clamps excerpts when the line is beyond the file or missing", () => {
    writeFileSync(join(root, "a.ts"), "only one line\n", "utf8");
    const beyond = readExcerpt(root, "a.ts", 500);
    expect(beyond).toContain("a.ts:1-1");
    const noLine = readExcerpt(root, "a.ts", undefined);
    expect(noLine).toContain("only one line");
  });

  it("rejects absolute paths and paths escaping the root", () => {
    expect(readExcerpt(root, join(root, "a.ts"), 1)).toBeUndefined();
    expect(readExcerpt(root, "../outside.ts", 1)).toBeUndefined();
    expect(readExcerpt(root, "a/../../b.ts", 1)).toBeUndefined();
  });

  it("returns undefined for missing files, directories, and binary content", () => {
    expect(readExcerpt(root, "missing.ts", 1)).toBeUndefined();
    mkdirSync(join(root, "adir"));
    expect(readExcerpt(root, "adir", 1)).toBeUndefined();
    const nul = String.fromCharCode(0);
    writeFileSync(join(root, "bin.dat"), `abc${nul}def`, "utf8");
    expect(readExcerpt(root, "bin.dat", 1)).toBeUndefined();
  });

  it("truncates oversized excerpts", () => {
    const wide = `${"x".repeat(4000)}\n${"y".repeat(4000)}\n${"z".repeat(4000)}`;
    writeFileSync(join(root, "wide.ts"), wide, "utf8");
    const excerpt = readExcerpt(root, "wide.ts", 1) ?? "";
    expect(excerpt).toContain("(excerpt truncated)");
    expect(excerpt.length).toBeLessThan(8200 + 60);
  });

  it("collectEvidence maps ids and skips unreadable files and roots", () => {
    mkdirSync(join(root, "src"), { recursive: true });
    writeFileSync(join(root, "src", "app.ts"), "line one\nline two\n", "utf8");
    const findings = [
      makeFinding(),
      makeFinding({ id: "f2", file: "src/nope.ts" }),
      makeFinding({ id: "f3", file: "/etc/passwd" })
    ];
    const evidence = collectEvidence(findings, root);
    expect(evidence.size).toBe(1);
    expect(evidence.get("f000000000000001")).toContain("line one");

    expect(collectEvidence(findings, undefined).size).toBe(0);
    expect(collectEvidence(findings, join(root, "does-not-exist")).size).toBe(0);
  });

  it("handles windows-style line endings", () => {
    writeFileSync(join(root, "crlf.ts"), "a\r\nb\r\nc\r\n", "utf8");
    const excerpt = readExcerpt(resolve(root), "crlf.ts", 2) ?? "";
    expect(excerpt).toContain("crlf.ts:1-3");
    expect(excerpt).not.toContain("\r");
  });
});
