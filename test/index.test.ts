import { describe, expect, it } from "vitest";
import { routeEvent } from "../src/index.js";

const prComment = {
  issue: { pull_request: { url: "https://api.github.com/repos/o/r/pulls/1" } },
  comment: {
    id: 1,
    body: "@cxbot review",
    user: { login: "apoorvasingh5", type: "User" },
    author_association: "OWNER"
  }
};

describe("routeEvent", () => {
  it("auto-reviews pull_request events", () => {
    expect(routeEvent("pull_request", { action: "opened" })).toEqual({
      action: "auto-review",
      reason: "pull_request event: opened"
    });
    expect(routeEvent("pull_request", { action: "synchronize" }).action).toBe("auto-review");
  });

  it("skips comments on plain issues", () => {
    const result = routeEvent("issue_comment", { issue: {}, comment: prComment.comment });
    expect(result).toEqual({ action: "skip", reason: "comment on issue, not pull request" });
  });

  it("routes human commands on PRs", () => {
    const result = routeEvent("issue_comment", prComment);
    expect(result).toMatchObject({
      action: "comment",
      verdict: "human-command",
      command: { command: "review", args: [] }
    });
  });

  it("skips human comments without a command", () => {
    const result = routeEvent("issue_comment", {
      ...prComment,
      comment: { ...prComment.comment, body: "nice change!" }
    });
    expect(result.action).toBe("skip");
  });

  it("routes scanner-of-interest comments for ingestion", () => {
    const result = routeEvent("issue_comment", {
      ...prComment,
      comment: {
        id: 2,
        body: "::error file=src/a.ts,line=10::trufflehog: verified secret",
        user: { login: "github-actions[bot]", type: "Bot" },
        author_association: "NONE"
      }
    });
    expect(result).toMatchObject({ action: "comment", verdict: "scanner" });
  });

  it("skips self-authored cxbot comments (loop protection)", () => {
    const result = routeEvent("issue_comment", {
      ...prComment,
      comment: {
        id: 3,
        body: "<!-- cxbot:summary:start -->\nreviewed\n<!-- cxbot:summary:end -->",
        user: { login: "github-actions[bot]", type: "Bot" },
        author_association: "NONE"
      }
    });
    expect(result).toEqual({
      action: "skip",
      reason: "self-authored or cxbot-marked comment"
    });
  });

  it("skips unhandled events", () => {
    expect(routeEvent("push", {})).toEqual({
      action: "skip",
      reason: "unhandled event: push"
    });
  });
});
