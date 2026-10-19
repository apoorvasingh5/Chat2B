import { withRetry } from "./retry.js";

export interface CompletionRequest {
  system: string;
  user: string;
}

export interface LLMProvider {
  readonly model: string;
  complete(request: CompletionRequest): Promise<string>;
}

export class ProviderNotConfiguredError extends Error {
  constructor(detail: string) {
    super(`LLM provider not configured: ${detail}`);
    this.name = "ProviderNotConfiguredError";
  }
}

export interface GitHubModelsEnv {
  apiKey?: string;
  model?: string;
  endpoint?: string;
  timeoutMs?: number;
  retries?: number;
  retryBaseDelayMs?: number;
}

export const DEFAULT_GITHUB_MODEL = "openai/gpt-4o-mini";
export const GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference/chat/completions";
export const GITHUB_API_VERSION = "2026-03-10";
export const DEFAULT_LLM_TIMEOUT_MS = 30_000;
export const DEFAULT_LLM_RETRIES = 3;

type FetchLike = (url: string, init: RequestInit) => Promise<Response>;

function positiveInt(raw: string | undefined): number | undefined {
  if (!raw) return undefined;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

export function providerFromEnv(
  env: NodeJS.ProcessEnv = process.env,
  fetchImpl?: FetchLike
): LLMProvider | undefined {
  const apiKey = env.CXBOT_MODELS_TOKEN || env.MODELS_API_KEY;
  if (!apiKey) return undefined;
  return createGitHubModelsProvider(
    {
      apiKey,
      model: env.CXBOT_MODEL,
      endpoint: env.CXBOT_MODELS_ENDPOINT,
      timeoutMs: positiveInt(env.CXBOT_TIMEOUT_MS),
      retries: positiveInt(env.CXBOT_RETRIES)
    },
    fetchImpl
  );
}

export function createGitHubModelsProvider(
  env: GitHubModelsEnv,
  fetchImpl: FetchLike = fetch
): LLMProvider {
  const apiKey = env.apiKey;
  if (!apiKey) throw new ProviderNotConfiguredError("missing GitHub Models API key");
  const model = env.model ?? DEFAULT_GITHUB_MODEL;
  const endpoint = env.endpoint ?? GITHUB_MODELS_ENDPOINT;
  const timeoutMs = env.timeoutMs ?? DEFAULT_LLM_TIMEOUT_MS;
  const attempts = Math.max(1, env.retries ?? DEFAULT_LLM_RETRIES);

  function parseRetryAfter(header: string | null): number | undefined {
    if (!header) return undefined;
    const seconds = Number.parseInt(header, 10);
    return Number.isFinite(seconds) && seconds >= 0 ? seconds * 1000 : undefined;
  }

  return {
    model,
    async complete(request: CompletionRequest): Promise<string> {
      return withRetry(
        async () => {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), timeoutMs);
          let response: Response;
          try {
            response = await fetchImpl(endpoint, {
              method: "POST",
              headers: {
                "content-type": "application/json",
                accept: "application/vnd.github+json",
                "x-github-api-version": GITHUB_API_VERSION,
                authorization: `Bearer ${apiKey}`
              },
              body: JSON.stringify({
                model,
                messages: [
                  { role: "system", content: request.system },
                  { role: "user", content: request.user }
                ],
                temperature: 0
              }),
              signal: controller.signal
            });
          } catch (error) {
            const aborted =
              typeof error === "object" && error !== null && (error as Error).name === "AbortError";
            const wrapped = aborted
              ? new Error(`GitHub Models request timed out after ${timeoutMs}ms`)
              : new Error(
                  `GitHub Models request failed: ${error instanceof Error ? error.message : String(error)}`
                );
            (wrapped as Error & { retryable?: boolean }).retryable = true;
            throw wrapped;
          } finally {
            clearTimeout(timer);
          }
          if (!response.ok) {
            const failure = new Error(
              `GitHub Models request failed: HTTP ${response.status}`
            ) as Error & { status?: number; retryAfterMs?: number };
            failure.status = response.status;
            const retryAfterMs = parseRetryAfter(response.headers.get("retry-after"));
            if (retryAfterMs !== undefined) failure.retryAfterMs = retryAfterMs;
            throw failure;
          }
          const text = await response.text();
          let payload: { choices?: Array<{ message?: { content?: string } }> };
          try {
            payload = JSON.parse(text) as typeof payload;
          } catch {
            const contentType = response.headers.get("content-type") ?? "unknown";
            throw new Error(
              `GitHub Models returned a non-JSON response (content-type: ${contentType}): ${text.slice(0, 160)}`
            );
          }
          const content = payload.choices?.[0]?.message?.content;
          if (!content) throw new Error("GitHub Models response contained no content");
          return content;
        },
        { attempts, baseDelayMs: env.retryBaseDelayMs ?? 300 }
      );
    }
  };
}
