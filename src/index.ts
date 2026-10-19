import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import * as core from "@actions/core";
import * as github from "@actions/github";
import { readBundle } from "./artifacts.js";
import { loadWorkspaceConfig } from "./config.js";
import { handleCommentEvent, routeEvent } from "./engine.js";
import { collectEvidence } from "./evidence.js";
import { createBotApi, type Octokit } from "./github.js";
import { providerFromEnv, type LLMProvider } from "./provider.js";
import { prNumber, type IssueCommentLike } from "./trigger.js";

export { routeEvent, handleCommentEvent, HELP_TABLE, buildTriageReply } from "./engine.js";
export type { RouteResult, EngineOutcome } from "./engine.js";
export { loadWorkspaceConfig } from "./config.js";

const FINDINGS_COMMANDS = new Set(["review", "explain", "fix"]);

function setRouteOutputs(
  route: ReturnType<typeof routeEvent>,
  payload: IssueCommentLike
): void {
  core.setOutput("action", route.action);
  const command = route.action === "comment" ? (route.command?.command ?? "") : "";
  core.setOutput("command", command);
  core.setOutput("needs-findings", FINDINGS_COMMANDS.has(command) ? "true" : "false");
  core.setOutput("pr", prNumber(payload)?.toString() ?? "");
}

async function fetchPrContext(
  octokit: Octokit,
  owner: string,
  repo: string,
  pullNumber: number
): Promise<{ title: string; body: string; headSha?: string } | undefined> {
  try {
    const { data } = await octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: pullNumber
    });
    return { title: data.title, body: data.body ?? "", headSha: data.head.sha };
  } catch (error) {
    core.warning(`cxbot: could not fetch PR context: ${error instanceof Error ? error.message : String(error)}`);
    return undefined;
  }
}

function evidenceRoot(workspace: string): string | undefined {
  const override = process.env.CXBOT_PR_ROOT;
  if (override) return override;
  const prDir = join(workspace, "pr");
  return existsSync(prDir) ? prDir : undefined;
}

export async function main(): Promise<void> {
  const routeOnly = process.argv.includes("--route-only");
  const eventName = process.env.GITHUB_EVENT_NAME ?? "";
  const payloadPath = process.env.GITHUB_EVENT_PATH;
  if (!payloadPath) {
    core.setOutput("action", "skip");
    core.info("cxbot: GITHUB_EVENT_PATH not set; nothing to do");
    return;
  }
  const payload = JSON.parse(readFileSync(payloadPath, "utf8")) as IssueCommentLike;

  const workspace = process.env.GITHUB_WORKSPACE ?? process.cwd();
  const { config, source } = loadWorkspaceConfig(workspace);

  const route = routeEvent(eventName, payload, config);
  core.info(`cxbot route: ${JSON.stringify(route)}`);
  setRouteOutputs(route, payload);
  if (routeOnly) {
    core.info("cxbot: route-only mode; stopping before reply");
    return;
  }

  if (route.action !== "comment") {
    core.setOutput("replied", false);
    return;
  }

  const token = core.getInput("github-token") || process.env.GITHUB_TOKEN;
  const repoName = process.env.GITHUB_REPOSITORY;
  if (!token || !repoName || !repoName.includes("/")) {
    core.warning("cxbot: missing token or GITHUB_REPOSITORY; skipping reply");
    core.setOutput("replied", false);
    return;
  }
  const [owner, repo] = repoName.split("/");
  if (!owner || !repo) {
    core.warning(`cxbot: malformed GITHUB_REPOSITORY: ${repoName}`);
    core.setOutput("replied", false);
    return;
  }

  const provider: LLMProvider | undefined = providerFromEnv(process.env);
  const findings = readBundle(join(workspace, "findings.json"))?.findings ?? [];
  const root = evidenceRoot(workspace);
  const evidence = collectEvidence(findings, root);
  core.info(`cxbot evidence: ${evidence.size}/${findings.length} excerpts from ${root ?? "(no PR checkout)"}`);

  const provenance = {
    runId: process.env.GITHUB_RUN_ID ?? "local",
    profile: config.profile,
    configSource: source,
    model: provider?.model ?? "n/a (LLM not configured)"
  };

  const octokit = github.getOctokit(token);
  const api = createBotApi(octokit, { owner, repo });

  let prContext: { title: string; body: string } | undefined;
  if (route.command && FINDINGS_COMMANDS.has(route.command.command)) {
    const number = prNumber(payload);
    if (number !== undefined) {
      prContext = await fetchPrContext(octokit, owner, repo, number);
    }
  }

  core.info(
    `cxbot context: findings=${findings.length} provider=${provider?.model ?? "none"} prContext=${prContext ? "fetched" : "none"}`
  );

  const outcome = await handleCommentEvent(eventName, payload, {
    api,
    provenance,
    findings,
    evidence,
    provider,
    config,
    prContext
  });

  core.info(`cxbot engine: ${JSON.stringify(outcome)}`);
  core.setOutput("replied", outcome.replied);
  core.setOutput("outcome", outcome.reason);
}

const invokedDirectly =
  process.argv[1] !== undefined && import.meta.url === pathToFileURL(process.argv[1]).href;
if (invokedDirectly) {
  main().catch((error: unknown) => {
    core.setFailed(error instanceof Error ? error.message : String(error));
  });
}
