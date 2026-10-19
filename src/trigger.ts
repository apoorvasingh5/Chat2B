import { createHash } from "node:crypto";

export const HANDLE = "cxbot";

export type ReviewCommand = "review" | "explain" | "fix" | "help";

export interface ParsedCommand {
  command: ReviewCommand;
  args: string[];
}

export interface IssueCommentLike {
  issue?: {
    number?: number;
    pull_request?: unknown;
  };
  pull_request?: {
    number?: number;
  };
  comment?: {
    id?: number;
    body?: string;
    user?: { login?: string; type?: string };
    author_association?: string;
  };
}

export function isPullRequestCommentEvent(payload: IssueCommentLike): boolean {
  return payload.issue?.pull_request != null;
}

export function prNumber(payload: IssueCommentLike): number | undefined {
  return payload.issue?.number ?? payload.pull_request?.number;
}

export function parseCommand(body: string, handle: string = HANDLE): ParsedCommand | null {
  const escaped = handle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`@${escaped}\\s+(review|explain|fix|help)\\b([\\s\\S]*)`, "i");
  const match = pattern.exec(body);
  if (!match?.[1]) return null;
  const command = match[1].toLowerCase() as ReviewCommand;
  const rest = (match[2] ?? "").trim();
  const args = rest.length > 0 ? rest.split(/\s+/) : [];
  return { command, args };
}

export function commandMarker(commentId: number): string {
  const digest = createHash("sha256").update(String(commentId)).digest("hex").slice(0, 16);
  return `<!-- cxbot:cmd:${digest} -->`;
}

export function markerOf(body: string): string | null {
  const match = /<!-- cxbot:cmd:([a-f0-9]{8,64}) -->/.exec(body);
  return match?.[1] ?? null;
}

export function isDuplicateInvocation(
  commentId: number,
  alreadyProcessed: ReadonlySet<number>
): boolean {
  return alreadyProcessed.has(commentId);
}
