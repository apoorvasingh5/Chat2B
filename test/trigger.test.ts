import { describe, expect, it } from "vitest";
import {
  commandMarker,
  isDuplicateInvocation,
  isPullRequestCommentEvent,
  markerOf,
  parseCommand
} from "../src/trigger.js";

describe("isPullRequestCommentEvent", () => {
  it("accepts comments on pull requests", () => {
    expect(
      isPullRequestCommentEvent({ issue: { pull_request: { url: "https://api/x" } } })
    ).toBe(true);
  });

  it("rejects comments on plain issues", () => {
    expect(isPullRequestCommentEvent({ issue: {} })).toBe(false);
    expect(isPullRequestCommentEvent({})).toBe(false);
  });
});

describe("parseCommand", () => {
  it("parses bare review command", () => {
    expect(parseCommand("@cxbot review")).toEqual({ command: "review", args: [] });
  });

  it("parses fix with arguments", () => {
    expect(parseCommand("please @cxbot fix a1b2c3d4 now")).toEqual({
      command: "fix",
      args: ["a1b2c3d4", "now"]
    });
  });

  it("parses explain command anywhere in the body", () => {
    const result = parseCommand("thanks!\n\n@cxbot explain cxone-sql-injection");
    expect(result).toEqual({ command: "explain", args: ["cxone-sql-injection"] });
  });

  it("is case-insensitive on the handle", () => {
    expect(parseCommand("@CXBOT HELP")?.command).toBe("help");
  });

  it("returns null without a command", () => {
    expect(parseCommand("just a normal comment")).toBeNull();
    expect(parseCommand("@cxbot look at this")).toBeNull();
  });
});

describe("invocation markers", () => {
  it("generates a stable marker per comment id", () => {
    const marker = commandMarker(12345);
    expect(marker).toMatch(/^<!-- cxbot:cmd:[a-f0-9]{16} -->$/);
    expect(commandMarker(12345)).toBe(marker);
    expect(commandMarker(12346)).not.toBe(marker);
  });

  it("round-trips through markerOf", () => {
    const marker = commandMarker(999);
    const digest = /<!-- cxbot:cmd:([a-f0-9]{16}) -->/.exec(marker)?.[1];
    expect(digest).toBeTruthy();
    expect(markerOf(`body ${marker}`)).toBe(digest);
    expect(markerOf("no marker here")).toBeNull();
  });
});

describe("isDuplicateInvocation", () => {
  it("flags already-seen comment ids", () => {
    const seen = new Set([10, 11]);
    expect(isDuplicateInvocation(10, seen)).toBe(true);
    expect(isDuplicateInvocation(12, seen)).toBe(false);
  });
});
