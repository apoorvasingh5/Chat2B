import { describe, expect, it } from "vitest";
import { sanitizeModelText, sanitizePatchText } from "../src/sanitize.js";

describe("sanitizeModelText", () => {
  it("neutralizes cxbot HTML comment markers so they cannot forge dedup/summary state", () => {
    const raw = "bogus <!-- cxbot:summary:start --> and <!-- cxbot:cmd:deadbeefdeadbeef -->";
    const out = sanitizeModelText(raw);
    expect(out).not.toContain("<!-- cxbot:");
    expect(out).toContain("&lt;!-- cxbot:summary:start");
    expect(out).toContain("&lt;!-- cxbot:cmd:deadbeefdeadbeef");
  });

  it("neutralizes cxbot mentions to prevent trigger loops", () => {
    const out = sanitizeModelText("please run @cxbot review again @CXBOT help");
    expect(out).not.toMatch(/@cxbot/i);
    expect(out.toLowerCase()).toContain("cxbot");
  });

  it("strips C0 control characters and DEL but keeps tabs and newlines", () => {
    const raw =
      "a" +
      String.fromCharCode(0) +
      "b\tc\nd" +
      String.fromCharCode(7) +
      "e" +
      String.fromCharCode(127) +
      "f";
    const out = sanitizeModelText(raw);
    expect(out).toBe("ab\tc\ndef");
  });

  it("normalizes CRLF line endings", () => {
    expect(sanitizeModelText("one\r\ntwo\rthree")).toBe("one\ntwo\nthree");
  });

  it("leaves ordinary text untouched", () => {
    expect(sanitizeModelText("SQL injection in `src/a.ts:12` (CWE-89)")).toBe(
      "SQL injection in `src/a.ts:12` (CWE-89)"
    );
  });
});

describe("sanitizePatchText", () => {
  it("accepts an ordinary patch", () => {
    expect(sanitizePatchText("key: ${AWS_KEY}\n")).toBe("key: ${AWS_KEY}\n");
  });

  it("rejects patches that would break out of the suggestion fence", () => {
    expect(sanitizePatchText("safe\n```\nevil")).toBeUndefined();
    expect(sanitizePatchText("```suggestion\nfake")).toBeUndefined();
  });

  it("rejects patches containing HTML comments", () => {
    expect(sanitizePatchText("a\n<!-- cxbot:summary:start -->\nb")).toBeUndefined();
  });

  it("strips control characters but preserves the code", () => {
    const dirty = "const x = 1;" + String.fromCharCode(1);
    expect(sanitizePatchText(dirty)).toBe("const x = 1;");
  });
});
