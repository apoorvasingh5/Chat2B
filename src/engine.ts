import { defaultConfig, type CxbotConfig } from "./config.js";
import type { BotApi } from "./github.js";
import { classifyActor, type IdentityVerdict } from "./identity.js";
import type { Finding } from "./findings.js";
import type { Provenance } from "./publisher.js";
import {
  CHECK_RUN_NAME,
  findingMarker,
  findLock,
  LOCK_TTL_MS,
  provenanceLine,
  renderInlineComment,
  renderLockComment,
  severityRollup,
  SUMMARY_END,
  SUMMARY_START,
  truncateForComment
} from "./publisher.js";
import type { LLMProvider } from "./provider.js";
import { sanitizeModelText } from "./sanitize.js";
import { triageFindings, type Verdict } from "./triage.js";
import {
  commandMarker,
  HANDLE,
  isPullRequestCommentEvent,
  parseCommand,
  prNumber,
  type IssueCommentLike,
  type ParsedCommand,
  type ReviewCommand
} from "./trigger.js";

export type RouteResult =
  | { action: "skip"; reason: string }
  | { action: "auto-review"; reason: string }
  | { action: "comment"; verdict: IdentityVerdict; command: ParsedCommand | null; reason: string };

interface PullRequestEventPayload {
  action?: string;
  pull_request?: {
    draft?: boolean;
    author_association?: string;
    user?: { login?: string };
    base?: { ref?: string };
    head?: { repo?: { full_name?: string } | null } | null;
  };
  repository?: { full_name?: string };
}

function matchesAnyBranch(ref: string, patterns: string[]): boolean {
  return patterns.some((pattern) => {
    try {
      return new RegExp(pattern).test(ref);
    } catch {
      return false;
    }
  });
}

function autoReviewGate(
  payload: PullRequestEventPayload,
  config: CxbotConfig
): string | undefined {
  const auto = config.auto_review;
  if (!auto.enabled) return "auto-review disabled in config";
  const pr = payload.pull_request;
  if (!pr) return undefined;

  const baseFullName = payload.repository?.full_name;
  const headRepo = pr.head?.repo;
  if (headRepo === null) {
    return "fork PR: head repo unavailable (maintainer gate)";
  }
  if (headRepo?.full_name && baseFullName && headRepo.full_name !== baseFullName) {
    return `fork PR: head ${headRepo.full_name} != base ${baseFullName} (maintainer gate)`;
  }
  if (pr.draft === true && !auto.drafts) {
    return "draft PR: auto_review.drafts is false";
  }
  const ref = pr.base?.ref;
  if (ref !== undefined && auto.base_branches.length > 0 && !matchesAnyBranch(ref, auto.base_branches)) {
    return `base branch \`${ref}\` not matched by auto_review.base_branches`;
  }
  const login = pr.user?.login;
  if (login && auto.ignore_usernames.some((u) => u.toLowerCase() === login.toLowerCase())) {
    return `author @${login} listed in auto_review.ignore_usernames`;
  }
  const association = pr.author_association;
  if (association && auto.ignore_author_associations.includes(association)) {
    return `author association ${association} listed in auto_review.ignore_author_associations`;
  }
  return undefined;
}

export function routeEvent(
  eventName: string,
  payload: unknown,
  config: CxbotConfig = defaultConfig()
): RouteResult {
  if (eventName === "pull_request") {
    const pr = payload as PullRequestEventPayload;
    const gateReason = autoReviewGate(pr, config);
    if (gateReason) return { action: "skip", reason: gateReason };
    if (pr.action === "synchronize") {
      return { action: "auto-review", reason: "new commits pushed (incremental review)" };
    }
    return { action: "auto-review", reason: `pull_request event: ${pr.action ?? "unknown"}` };
  }

  if (eventName === "issue_comment" || eventName === "pull_request_review_comment") {
    const event = payload as IssueCommentLike;
    if (eventName === "issue_comment" && !isPullRequestCommentEvent(event)) {
      return { action: "skip", reason: "comment on issue, not pull request" };
    }
    const comment = event.comment;
    if (!comment?.user?.login) {
      return { action: "skip", reason: "malformed comment payload" };
    }
    const verdict = classifyActor({
      login: comment.user.login,
      type: comment.user.type,
      authorAssociation: comment.author_association,
      body: comment.body
    });
    if (verdict === "self") {
      return { action: "skip", reason: "self-authored or cxbot-marked comment" };
    }
    if (verdict === "ignore") {
      return { action: "skip", reason: "identity not permitted to trigger" };
    }
    const command = parseCommand(comment.body ?? "");
    if (verdict === "scanner") {
      return {
        action: "comment",
        verdict,
        command,
        reason: "scanner-of-interest comment detected; ingest results"
      };
    }
    if (!command) {
      return { action: "skip", reason: "human comment without @cxbot command" };
    }
    return { action: "comment", verdict, command, reason: `command: ${command.command}` };
  }

  return { action: "skip", reason: `unhandled event: ${eventName}` };
}

export type EngineOutcome =
  | { replied: false; reason: string }
  | { replied: true; commentId: number; reason: string };

export interface EngineDeps {
  api: BotApi;
  provenance: Provenance;
  findings?: Finding[];
  evidence?: Map<string, string>;
  provider?: LLMProvider;
  config?: CxbotConfig;
  prContext?: { title: string; body: string; headSha?: string };
}

export const HELP_TABLE = [
  "| Command | What it does |",
  "|---|---|",
  "| `@cxbot review` | Triage all scanner findings (TruffleHog, Checkmarx One) on this PR |",
  "| `@cxbot explain <finding-id>` | Explain one finding with evidence from current code |",
  "| `@cxbot fix <finding-id>` | Propose a minimal fix as a GitHub suggestion |",
  "| `@cxbot help` | Show this help |",
  "",
  "Scanner inputs come from workflow artifacts. Review rules live in `.cxbot.yaml`."
].join("\n");

export function buildCommandReply(args: {
  login: string;
  command: ParsedCommand;
  marker: string;
  provenance: Provenance;
}): string {
  const { login, command, marker, provenance } = args;
  const suffix = provenanceLine(provenance);
  if (command.command === "help") {
    return [marker, `@${login} CxPRBot commands:`, HELP_TABLE, suffix].join("\n\n");
  }
  const invoked = `@${HANDLE} ${command.command}${
    command.args.length > 0 ? ` ${command.args.join(" ")}` : ""
  }`;
  return [marker, `@${login} received \`${invoked}\` — queued.`, suffix].join("\n\n");
}

export const MAX_TRIAGE_LINES = 20;

export function buildTriageReply(args: {
  login: string;
  findings: Finding[];
  verdicts: Verdict[];
  profile: CxbotConfig["profile"];
  provenance: Provenance;
  dropped?: { unknownIds: number; invalidItems: number };
}): string {
  const { login, findings, verdicts, profile, provenance, dropped } = args;
  const byId = new Map(verdicts.map((v) => [v.id, v]));
  const counts = { confirmed: 0, stale: 0, uncertain: 0 };
  for (const verdict of verdicts) counts[verdict.verdict] += 1;
  const untriaged = findings.length - verdicts.length;

  const gate =
    profile === "quiet"
      ? (f: Finding) => f.severity === "critical" || f.severity === "high"
      : (_f: Finding) => true;
  const shown = findings.filter(gate);
  const hidden = findings.length - shown.length;

  const header =
    `@${login} **Triage complete:** ${findings.length} findings → ` +
    `${counts.confirmed} confirmed · ${counts.stale} stale · ${counts.uncertain} uncertain` +
    (untriaged > 0 ? ` · ${untriaged} untriaged` : "") +
    (hidden > 0 ? ` (${hidden} hidden by profile \`${profile}\`)` : "") +
    ".";

  const rollup = findings.length > 0 ? severityRollup(findings) : undefined;

  const lines = shown.slice(0, MAX_TRIAGE_LINES).map((finding) => {
    const verdict = byId.get(finding.id);
    const details = truncateForComment(verdict?.details ?? finding.details).split("\n")[0] ?? "";
    const shortDetails = details.length > 300 ? `${details.slice(0, 300)}…` : details;
    return [
      findingMarker(finding.id),
      `**[${finding.severity}] ${finding.title}** — \`${finding.file}:${finding.line}\` (${finding.scanner}) → **${verdict?.verdict ?? "untriaged"}**${verdict ? ` [${verdict.confidence}]` : ""}`,
      shortDetails
    ].join("\n\n");
  });
  if (shown.length > MAX_TRIAGE_LINES) {
    lines.push(`… ${shown.length - MAX_TRIAGE_LINES} more findings omitted.`);
  }

  const droppedLine =
    dropped && dropped.unknownIds + dropped.invalidItems > 0
      ? `_${dropped.unknownIds} unknown and ${dropped.invalidItems} invalid model items dropped._`
      : undefined;

  return [
    header,
    rollup,
    ...lines,
    droppedLine,
    provenanceLine(provenance)
  ]
    .filter((part): part is string => Boolean(part))
    .join("\n\n");
}

interface ReviewOutcome {
  body: string;
  isSummary: boolean;
  verdicts?: Verdict[];
}

async function runReview(args: {
  login: string;
  marker: string;
  deps: EngineDeps;
}): Promise<ReviewOutcome> {
  const { login, marker, deps } = args;
  const suffix = provenanceLine(deps.provenance);
  const config = deps.config ?? defaultConfig();
  const findings = deps.findings ?? [];

  if (!deps.provider) {
    return {
      isSummary: false,
      body: [
        marker,
        `@${login} \`@cxbot review\` — found ${findings.length} scanner finding(s), but the LLM provider is not configured. Set the \`CXBOT_MODELS_TOKEN\` secret to enable triage.`,
        suffix
      ].join("\n\n")
    };
  }
  if (findings.length === 0) {
    return {
      isSummary: false,
      body: [
        marker,
        `@${login} \`@cxbot review\` — no scanner findings available in this run (TruffleHog rescan produced none, or the scan has not run on this PR).`,
        suffix
      ].join("\n\n")
    };
  }

  try {
    const result = await triageFindings(
      findings,
      deps.prContext ?? { title: "(PR title unavailable)", body: "" },
      { provider: deps.provider, config, evidence: deps.evidence }
    );
    const reply = buildTriageReply({
      login,
      findings,
      verdicts: result.verdicts,
      profile: config.profile,
      provenance: deps.provenance,
      dropped: result.dropped
    });
    return {
      isSummary: true,
      verdicts: result.verdicts,
      body: [marker, SUMMARY_START, reply, SUMMARY_END].join("\n\n")
    };
  } catch (error) {
    const message = sanitizeModelText(
      error instanceof Error ? error.message : String(error)
    );
    return {
      isSummary: false,
      body: [
        marker,
        `@${login} \`@cxbot review\` — triage failed: ${message}. Scanner findings were not altered; re-run the command.`,
        suffix
      ].join("\n\n")
    };
  }
}

async function publishReviewSideEffects(args: {
  api: BotApi;
  pullNumber: number;
  headSha?: string;
  findings: Finding[];
  verdicts: Verdict[];
  provenance: Provenance;
}): Promise<string> {
  const { api, pullNumber, headSha, findings, verdicts, provenance } = args;
  if (!headSha) return "inline=skipped (no head sha); check=skipped";

  const byId = new Map(findings.map((f) => [f.id, f]));
  let posted = 0;
  let dupes = 0;
  let errors = 0;
  try {
    const existingInline = await api.listReviewComments(pullNumber);
    for (const verdict of verdicts) {
      if (verdict.verdict !== "confirmed" || !verdict.fix?.patch) continue;
      const finding = byId.get(verdict.id);
      if (!finding) continue;
      if (existingInline.some((c) => c.body.includes(findingMarker(finding.id)))) {
        dupes += 1;
        continue;
      }
      const body = renderInlineComment(finding, verdict.details, {
        suggestion: verdict.fix.patch,
        provenance
      });
      try {
        await api.createReviewComment(pullNumber, {
          commitId: headSha,
          path: finding.file,
          line: finding.line,
          body
        });
        posted += 1;
      } catch {
        errors += 1;
      }
    }
  } catch {
    errors += 1;
  }
  const inlinePart = `inline=posted ${posted} (dupes ${dupes}, errors ${errors})`;

  const confirmed = verdicts.filter((v) => v.verdict === "confirmed").length;
  try {
    const summary = [
      severityRollup(findings),
      "",
      `Triage: ${confirmed} confirmed / ${verdicts.length} verdicts across ${findings.length} findings.`
    ].join("\n");
    const { id } = await api.upsertCheckRun({
      name: CHECK_RUN_NAME,
      headSha,
      status: "completed",
      conclusion: "success",
      summary
    });
    return `${inlinePart}; check=${id}`;
  } catch (error) {
    const message = sanitizeModelText(
      error instanceof Error ? error.message : String(error)
    ).slice(0, 120);
    return `${inlinePart}; check=error: ${message}`;
  }
}

async function buildReplyForCommand(args: {
  login: string;
  command: ParsedCommand;
  marker: string;
  deps: EngineDeps;
}): Promise<string> {
  const { login, command, marker, deps } = args;
  if (command.command === "review") {
    const review = await runReview({ login, marker, deps });
    return review.body;
  }
  return buildCommandReply({ login, command, marker, provenance: deps.provenance });
}

type LockState = { id?: number };

async function acquireLock(
  api: BotApi,
  issueNumber: number,
  existing: Array<{ id: number; body: string }>,
  runId: string
): Promise<LockState | "held"> {
  const lock = findLock(existing);
  const now = Date.now();
  if (lock && Number.isFinite(lock.atMs) && now - lock.atMs < LOCK_TTL_MS) {
    return "held";
  }
  const body = renderLockComment(now, runId);
  try {
    if (lock) {
      await api.updateComment(lock.commentId, body);
      return { id: lock.commentId };
    }
    const created = await api.createComment(issueNumber, body);
    return { id: created.id };
  } catch {
    return {};
  }
}

async function releaseLock(api: BotApi, lock: LockState | undefined): Promise<void> {
  if (lock?.id === undefined) return;
  try {
    await api.deleteComment(lock.id);
  } catch {
    // fail-open: a leaked lock expires via LOCK_TTL_MS
  }
}

export async function handleCommentEvent(
  eventName: string,
  payload: IssueCommentLike,
  deps: EngineDeps
): Promise<EngineOutcome> {
  const route = routeEvent(eventName, payload, deps.config ?? defaultConfig());
  if (route.action === "skip") return { replied: false, reason: route.reason };
  if (route.action === "auto-review") {
    return { replied: false, reason: "auto-review path (scan job), no comment reply" };
  }

  const comment = payload.comment;
  if (!comment || comment.id === undefined) {
    return { replied: false, reason: "comment without id" };
  }
  const commentId = comment.id;

  const number = prNumber(payload);
  if (number === undefined) return { replied: false, reason: "no pull request number" };

  if (route.verdict === "scanner") {
    return { replied: false, reason: "scanner comment detected; ingestion lands in Phase 3" };
  }

  const command = route.command;
  if (!command) return { replied: false, reason: "no command to execute" };

  const marker = commandMarker(commentId);
  const existing = await deps.api.listComments(number);
  if (existing.some((c) => c.body.includes(marker))) {
    return { replied: false, reason: "already replied to this comment (dedup)" };
  }

  const login = comment.user?.login ?? "user";

  if (command.command === "review") {
    const lock = await acquireLock(deps.api, number, existing, deps.provenance.runId);
    if (lock === "held") {
      return { replied: false, reason: "per-PR lock held: another cxbot review is in progress" };
    }
    try {
      const review = await runReview({ login, marker, deps });
      if (!review.isSummary) {
        const created = await deps.api.createComment(number, review.body);
        return { replied: true, commentId: created.id, reason: route.reason };
      }

      const target = existing.find((c) => c.body.includes(SUMMARY_START));
      const summaryBody = truncateForComment(review.body);
      let savedId: number;
      if (target) {
        await deps.api.updateComment(target.id, summaryBody);
        savedId = target.id;
      } else {
        savedId = (await deps.api.createComment(number, summaryBody)).id;
      }
      const publish = await publishReviewSideEffects({
        api: deps.api,
        pullNumber: number,
        headSha: deps.prContext?.headSha,
        findings: deps.findings ?? [],
        verdicts: review.verdicts ?? [],
        provenance: deps.provenance
      });
      return {
        replied: true,
        commentId: savedId,
        reason: `${route.reason}; summary ${target ? "updated" : "created"}; ${publish}`
      };
    } finally {
      await releaseLock(deps.api, lock);
    }
  }

  const body = await buildReplyForCommand({
    login,
    command,
    marker,
    deps
  });
  const created = await deps.api.createComment(number, body);
  return { replied: true, commentId: created.id, reason: route.reason };
}

export type { ReviewCommand };
