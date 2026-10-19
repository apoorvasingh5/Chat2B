import { describe, expect, it, vi } from "vitest";
import { createBotApi, type Octokit } from "../src/github.js";

function fakeOctokit(
  pages: Array<Array<{ id: number; body?: string }>>,
  created: Array<{ id: number; body: string }> = []
) {
  const listComments = vi.fn(async (args: { page?: number }) => ({
    data: pages[(args.page ?? 1) - 1] ?? []
  }));
  const createComment = vi.fn(async (args: { body: string }) => {
    const record = { id: 1000 + created.length, body: args.body };
    created.push(record);
    return { data: record };
  });
  const updateComment = vi.fn(async (args: { comment_id: number; body: string }) => {
    for (const page of pages) {
      const found = page.find((c) => c.id === args.comment_id);
      if (found) found.body = args.body;
    }
    return { data: { id: args.comment_id, body: args.body } };
  });
  const deleteComment = vi.fn(async (args: { comment_id: number }) => {
    for (const page of pages) {
      const index = page.findIndex((c) => c.id === args.comment_id);
      if (index >= 0) page.splice(index, 1);
    }
    return { data: {} };
  });
  const reviewComments: Array<{ id: number; body: string; path: string; line: number }> = [];
  const listReviewComments = vi.fn(async () => ({ data: reviewComments }));
  const createReviewComment = vi.fn(
    async (args: { body: string; path: string; line: number }) => {
      const record = { id: 3000 + reviewComments.length, body: args.body, path: args.path, line: args.line };
      reviewComments.push(record);
      return { data: record };
    }
  );
  const checkRuns: Array<{ id: number; name: string }> = [];
  const listForRef = vi.fn(async (args: { check_name?: string }) => {
    const check_runs = checkRuns.filter((run) => run.name === args.check_name);
    return { data: { total_count: check_runs.length, check_runs } };
  });
  const createCheck = vi.fn(async (args: { name: string }) => {
    const record = { id: 5000 + checkRuns.length, name: args.name };
    checkRuns.push(record);
    return { data: record };
  });
  const updateCheck = vi.fn(async (args: { check_run_id: number }) => ({
    data: { id: args.check_run_id }
  }));
  const octokit = {
    rest: {
      issues: { listComments, createComment, updateComment, deleteComment },
      pulls: {
        get: vi.fn(async (args: { pull_number: number }) => ({
          data: { title: `PR ${args.pull_number}`, body: "PR body", head: { sha: "deadbeef" } }
        })),
        listReviewComments,
        createReviewComment
      },
      checks: { listForRef, create: createCheck, update: updateCheck }
    }
  } as unknown as Octokit;
  return {
    octokit,
    listComments,
    createComment,
    updateComment,
    deleteComment,
    created,
    reviewComments,
    listReviewComments,
    createReviewComment,
    checkRuns,
    listForRef,
    createCheck,
    updateCheck
  };
}

describe("createBotApi", () => {
  it("lists comments from the first page and stops when short", async () => {
    const { octokit, listComments } = fakeOctokit([
      [
        { id: 1, body: "first" },
        { id: 2, body: "second" }
      ]
    ]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    const comments = await api.listComments(7);
    expect(comments).toEqual([
      { id: 1, body: "first" },
      { id: 2, body: "second" }
    ]);
    expect(listComments).toHaveBeenCalledTimes(1);
    expect(listComments).toHaveBeenCalledWith(
      expect.objectContaining({ owner: "o", repo: "r", issue_number: 7, per_page: 100, page: 1 })
    );
  });

  it("paginates until a short page", async () => {
    const fullPage = Array.from({ length: 100 }, (_, i) => ({ id: i, body: `c${i}` }));
    const { octokit, listComments } = fakeOctokit([fullPage, [{ id: 999, body: "last" }]]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    const comments = await api.listComments(1);
    expect(comments).toHaveLength(101);
    expect(listComments).toHaveBeenCalledTimes(2);
    expect(comments.at(-1)).toEqual({ id: 999, body: "last" });
  });

  it("creates comments and returns the new id", async () => {
    const { octokit, created } = fakeOctokit([[]]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    const result = await api.createComment(3, "hello");
    expect(result.id).toBe(1000);
    expect(created[0]?.body).toBe("hello");
  });

  it("updates comments in place", async () => {
    const pages = [[{ id: 5, body: "old" }]];
    const { octokit } = fakeOctokit(pages);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    await api.updateComment(5, "new");
    expect(pages[0]?.[0]?.body).toBe("new");
  });

  it("fetches PR title, body, and head sha", async () => {
    const { octokit } = fakeOctokit([[]]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    const pr = await api.getPull(17);
    expect(pr).toEqual({ title: "PR 17", body: "PR body", headSha: "deadbeef" });
  });

  it("lists and creates inline review comments", async () => {
    const { octokit, reviewComments } = fakeOctokit([[]]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    expect(await api.listReviewComments(9)).toEqual([]);

    const created = await api.createReviewComment(9, {
      commitId: "deadbeef",
      path: "src/app.ts",
      line: 12,
      body: "<!-- cxbot:f:abc -->\ncomment"
    });
    expect(created.id).toBe(3000);
    expect(reviewComments[0]?.path).toBe("src/app.ts");
    expect(await api.listReviewComments(9)).toHaveLength(1);
  });

  it("creates a check run when none exists for the head sha", async () => {
    const { octokit, checkRuns, createCheck, updateCheck } = fakeOctokit([[]]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    const result = await api.upsertCheckRun({
      name: "CxPRBot / triage",
      headSha: "deadbeef",
      status: "completed",
      conclusion: "success",
      summary: "all good"
    });
    expect(result.id).toBe(5000);
    expect(createCheck).toHaveBeenCalledTimes(1);
    expect(updateCheck).not.toHaveBeenCalled();
    expect(checkRuns[0]?.name).toBe("CxPRBot / triage");
  });

  it("updates an existing check run instead of creating a duplicate", async () => {
    const { octokit, createCheck, updateCheck, listForRef } = fakeOctokit([[]]);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    await api.upsertCheckRun({
      name: "CxPRBot / triage",
      headSha: "deadbeef",
      status: "completed",
      conclusion: "success",
      summary: "first"
    });
    const second = await api.upsertCheckRun({
      name: "CxPRBot / triage",
      headSha: "deadbeef",
      status: "completed",
      conclusion: "success",
      summary: "second"
    });
    expect(second.id).toBe(5000);
    expect(createCheck).toHaveBeenCalledTimes(1);
    expect(updateCheck).toHaveBeenCalledTimes(1);
    expect(listForRef).toHaveBeenCalledWith(
      expect.objectContaining({ ref: "deadbeef", check_name: "CxPRBot / triage" })
    );
  });

  it("deletes comments by id", async () => {
    const pages = [[{ id: 5, body: "lock" }]];
    const { octokit, deleteComment } = fakeOctokit(pages);
    const api = createBotApi(octokit, { owner: "o", repo: "r" });
    await api.deleteComment(5);
    expect(deleteComment).toHaveBeenCalledWith(
      expect.objectContaining({ owner: "o", repo: "r", comment_id: 5 })
    );
    expect(pages[0]).toHaveLength(0);
  });

  it("retries retryable API errors and then succeeds", async () => {
    const { octokit, listComments } = fakeOctokit([[{ id: 1, body: "only" }]]);
    let attempts = 0;
    const original = listComments.getMockImplementation()!;
    listComments.mockImplementation(async (args) => {
      attempts += 1;
      if (attempts === 1) {
        const error = Object.assign(new Error("rate limited"), { status: 429 });
        throw error;
      }
      return original(args);
    });
    const api = createBotApi(octokit, { owner: "o", repo: "r" }, {
      attempts: 3,
      sleep: async () => {}
    });
    const comments = await api.listComments(1);
    expect(comments).toHaveLength(1);
    expect(attempts).toBe(2);
  });

  it("does not retry non-retryable API errors", async () => {
    const { octokit, listComments } = fakeOctokit([[{ id: 1, body: "x" }]]);
    listComments.mockImplementation(async () => {
      throw Object.assign(new Error("validation failed"), { status: 422 });
    });
    const api = createBotApi(octokit, { owner: "o", repo: "r" }, {
      attempts: 3,
      sleep: async () => {}
    });
    await expect(api.listComments(1)).rejects.toThrow("validation failed");
    expect(listComments).toHaveBeenCalledTimes(1);
  });
});
