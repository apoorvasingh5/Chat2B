import { describe, expect, it } from "vitest";
import { defaultConfig, parseConfig } from "../src/config.js";

describe("parseConfig", () => {
  it("applies defaults for an empty config", () => {
    const config = defaultConfig();
    expect(config.profile).toBe("balanced");
    expect(config.scanners).toEqual({
      trufflehog: true,
      cxone: true,
      require_verified: false
    });
    expect(config.auto_review.enabled).toBe(true);
    expect(config.auto_review.drafts).toBe(false);
    expect(config.auto_review.base_branches).toEqual(["^main$"]);
    expect(config.deny_fix_paths).toContain(".github/workflows/**");
  });

  it("parses a full .cxbot.yaml", () => {
    const config = parseConfig(`
language: en-US
profile: thorough
tone_instructions: "Be concise and cite Cx query IDs."
scanners:
  trufflehog: true
  cxone: true
  require_verified: true
auto_review:
  enabled: true
  drafts: false
  base_branches: ["^main$", "^release/.*$"]
  labels: ["security", "!wip"]
  ignore_usernames: ["bot-staging"]
path_filters: ["src/**", "!src/generated/**"]
path_instructions:
  - path: "src/auth/**"
    instructions: "Focus on authn/authz and token validation."
deny_fix_paths: [".github/workflows/**"]
`);
    expect(config.profile).toBe("thorough");
    expect(config.scanners.require_verified).toBe(true);
    expect(config.auto_review.base_branches).toEqual(["^main$", "^release/.*$"]);
    expect(config.path_filters).toEqual(["src/**", "!src/generated/**"]);
    expect(config.path_instructions[0]?.path).toBe("src/auth/**");
  });

  it("rejects an unknown profile", () => {
    expect(() => parseConfig("profile: aggressive")).toThrow();
  });

  it("rejects tone_instructions over 250 chars", () => {
    const long = "x".repeat(251);
    expect(() => parseConfig(`tone_instructions: "${long}"`)).toThrow();
  });

  it("accepts tone_instructions at the 250-char limit", () => {
    const atLimit = "x".repeat(250);
    expect(parseConfig(`tone_instructions: "${atLimit}"`).tone_instructions).toHaveLength(250);
  });
});
