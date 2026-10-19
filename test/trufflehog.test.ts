import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { parseTrufflehogJsonl } from "../src/adapters/trufflehog.js";

const fixture = readFileSync(
  fileURLToPath(new URL("./fixtures/trufflehog.jsonl", import.meta.url)),
  "utf8"
);

const RAW_SECRETS = [
  "AKIAFAKESECRETKEYVALUE1234",
  "-----BEGIN OPENSSH PRIVATE KEY BLOBfakefakefake",
  "sk_live_FAKESTRIPEKEY123456789"
];

describe("parseTrufflehogJsonl", () => {
  it("parses all findings with stable unique ids", () => {
    const findings = parseTrufflehogJsonl(fixture);
    expect(findings).toHaveLength(3);
    const ids = findings.map((f) => f.id);
    expect(new Set(ids).size).toBe(3);
    expect(parseTrufflehogJsonl(fixture).map((f) => f.id)).toEqual(ids);
  });

  it("extracts source file/line from Git and Filesystem metadata", () => {
    const findings = parseTrufflehogJsonl(fixture);
    expect(findings[0]).toMatchObject({
      scanner: "trufflehog",
      file: "config/app.yml",
      line: 42,
      verified: true
    });
    expect(findings[1]).toMatchObject({ file: "dev/id_rsa", line: 7, verified: false });
    expect(findings[2]).toMatchObject({ file: "src/payments.ts", line: 10, verified: true });
  });

  it("maps verified to critical and unverified to medium", () => {
    const findings = parseTrufflehogJsonl(fixture);
    expect(findings.map((f) => f.severity)).toEqual(["critical", "medium", "critical"]);
  });

  it("never leaks Raw secret values, only Redacted", () => {
    const findings = parseTrufflehogJsonl(fixture);
    const serialized = JSON.stringify(findings);
    for (const secret of RAW_SECRETS) {
      expect(serialized).not.toContain(secret);
    }
    expect(serialized).toContain("AKIA********************");
  });

  it("requireVerified filters unverified entries", () => {
    const findings = parseTrufflehogJsonl(fixture, { requireVerified: true });
    expect(findings).toHaveLength(2);
    expect(findings.every((f) => f.verified)).toBe(true);
  });

  it("skips malformed lines without throwing", () => {
    const findings = parseTrufflehogJsonl(`{"DetectorName":"AWS","Verified":true}\nnot-json\n\n`);
    expect(findings).toHaveLength(1);
    expect(findings[0]?.file).toBe("");
  });
});
