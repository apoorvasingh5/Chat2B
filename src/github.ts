import type { getOctokit } from "@actions/github";
import { withRetry, type RetryOptions } from "./retry.js";

export interface RepoRef {
  owner: string;
  repo: string;
}

export interface IssueCommentRecord {
  id: number;
  body: string;
}

export interface PullRequestRecord {
  title: string;
  body: string;
  headSha?: string;
}

export interface ReviewCommentRecord {
  id: number;
  body: string;
}

export interface CreateReviewCommentInput {
  commitId: string;
  path: string;
  line: number;
  body: string;
}

export interface CheckRunInput {
  name: string;
  headSha: string;
  status: "queued" | "in_progress" | "completed";
  conclusion?: "success" | "neutral" | "failure" | "action_required" | "cancelled";
  summary: string;
  detailsUrl?: string;
}

export interface BotApi {
  listComments(issueNumber: number): Promise<IssueCommentRecord[]>;
  createComment(issueNumber: number, body: string): Promise<{ id: number }>;
  updateComment(commentId: number, body: string): Promise<void>;
  deleteComment(commentId: number): Promise<void>;
  getPull(pullNumber: number): Promise<PullRequestRecord>;
  listReviewComments(pullNumber: number): Promise<ReviewCommentRecord[]>;
  createReviewComment(pullNumber: number, input: CreateReviewCommentInput): Promise<{ id: number }>;
  listCheckRuns(headSha: string, name: string): Promise<number[]>;
  upsertCheckRun(input: CheckRunInput): Promise<{ id: number }>;
}

export type Octokit = ReturnType<typeof getOctokit>;

const MAX_COMMENT_PAGES = 10;

export function createBotApi(
  octokit: Octokit,
  repo: RepoRef,
  retry: RetryOptions = {}
): BotApi {
  return {
    async listComments(issueNumber: number): Promise<IssueCommentRecord[]> {
      return withRetry(async () => {
        const comments: IssueCommentRecord[] = [];
        for (let page = 1; page <= MAX_COMMENT_PAGES; page++) {
          const { data } = await octokit.rest.issues.listComments({
            owner: repo.owner,
            repo: repo.repo,
            issue_number: issueNumber,
            per_page: 100,
            page
          });
          for (const comment of data) {
            comments.push({ id: comment.id, body: comment.body ?? "" });
          }
          if (data.length < 100) break;
        }
        return comments;
      }, retry);
    },

    async createComment(issueNumber: number, body: string): Promise<{ id: number }> {
      return withRetry(async () => {
        const { data } = await octokit.rest.issues.createComment({
          owner: repo.owner,
          repo: repo.repo,
          issue_number: issueNumber,
          body
        });
        return { id: data.id };
      }, retry);
    },

    async updateComment(commentId: number, body: string): Promise<void> {
      await withRetry(
        () =>
          octokit.rest.issues.updateComment({
            owner: repo.owner,
            repo: repo.repo,
            comment_id: commentId,
            body
          }),
        retry
      );
    },

    async deleteComment(commentId: number): Promise<void> {
      await withRetry(
        () =>
          octokit.rest.issues.deleteComment({
            owner: repo.owner,
            repo: repo.repo,
            comment_id: commentId
          }),
        retry
      );
    },

    async getPull(pullNumber: number): Promise<PullRequestRecord> {
      return withRetry(async () => {
        const { data } = await octokit.rest.pulls.get({
          owner: repo.owner,
          repo: repo.repo,
          pull_number: pullNumber
        });
        return { title: data.title, body: data.body ?? "", headSha: data.head.sha };
      }, retry);
    },

    async listReviewComments(pullNumber: number): Promise<ReviewCommentRecord[]> {
      return withRetry(async () => {
        const comments: ReviewCommentRecord[] = [];
        for (let page = 1; page <= MAX_COMMENT_PAGES; page++) {
          const { data } = await octokit.rest.pulls.listReviewComments({
            owner: repo.owner,
            repo: repo.repo,
            pull_number: pullNumber,
            per_page: 100,
            page
          });
          for (const comment of data) {
            comments.push({ id: comment.id, body: comment.body ?? "" });
          }
          if (data.length < 100) break;
        }
        return comments;
      }, retry);
    },

    async createReviewComment(
      pullNumber: number,
      input: CreateReviewCommentInput
    ): Promise<{ id: number }> {
      return withRetry(async () => {
        const { data } = await octokit.rest.pulls.createReviewComment({
          owner: repo.owner,
          repo: repo.repo,
          pull_number: pullNumber,
          commit_id: input.commitId,
          path: input.path,
          line: input.line,
          body: input.body
        });
        return { id: data.id };
      }, retry);
    },

    async listCheckRuns(headSha: string, name: string): Promise<number[]> {
      return withRetry(async () => {
        const { data } = await octokit.rest.checks.listForRef({
          owner: repo.owner,
          repo: repo.repo,
          ref: headSha,
          check_name: name,
          per_page: 100
        });
        return (data.check_runs ?? []).map((run) => run.id);
      }, retry);
    },

    async upsertCheckRun(input: CheckRunInput): Promise<{ id: number }> {
      const existing = await this.listCheckRuns(input.headSha, input.name);
      const output = { title: input.name, summary: input.summary };
      const first = existing[0];
      if (first !== undefined) {
        await withRetry(
          () =>
            octokit.rest.checks.update({
              owner: repo.owner,
              repo: repo.repo,
              check_run_id: first,
              status: input.status,
              conclusion: input.conclusion,
              output
            }),
          retry
        );
        return { id: first };
      }
      return withRetry(async () => {
        const { data } = await octokit.rest.checks.create({
          owner: repo.owner,
          repo: repo.repo,
          name: input.name,
          head_sha: input.headSha,
          status: input.status,
          conclusion: input.conclusion,
          output,
          details_url: input.detailsUrl
        });
        return { id: data.id };
      }, retry);
    }
  };
}
