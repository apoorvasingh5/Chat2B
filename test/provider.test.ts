import { describe, expect, it, vi } from "vitest";
import {
  createGitHubModelsProvider,
  DEFAULT_GITHUB_MODEL,
  GITHUB_API_VERSION,
  GITHUB_MODELS_ENDPOINT,
  providerFromEnv,
  ProviderNotConfiguredError
} from "../src/provider.js";

function fakeResponse(body: unknown, ok = true, status = 200) {
  const text = typeof body === "string" ? body : JSON.stringify(body);
  return {
    ok,
    status,
    headers: {
      get: (name: string) => (name.toLowerCase() === "content-type" ? "application/json" : null)
    },
    text: async () => text,
    json: async () => body
  } as unknown as Response;
}

describe("providerFromEnv", () => {
  it("returns undefined without a token", () => {
    expect(providerFromEnv({} as NodeJS.ProcessEnv)).toBeUndefined();
    expect(providerFromEnv({ CXBOT_MODEL: "x/y" } as NodeJS.ProcessEnv)).toBeUndefined();
  });

  it("builds a provider with default and overridden models", () => {
    const defaultProvider = providerFromEnv({
      CXBOT_MODELS_TOKEN: "tok"
    } as NodeJS.ProcessEnv);
    expect(defaultProvider?.model).toBe(DEFAULT_GITHUB_MODEL);

    const custom = providerFromEnv({
      CXBOT_MODELS_TOKEN: "tok",
      CXBOT_MODEL: "openai/gpt-4o"
    } as NodeJS.ProcessEnv);
    expect(custom?.model).toBe("openai/gpt-4o");
  });

  it("throws at construction without api key", () => {
    expect(() => createGitHubModelsProvider({})).toThrow(ProviderNotConfiguredError);
  });
});

describe("createGitHubModelsProvider.complete", () => {
  it("POSTs to the GitHub Models endpoint with bearer auth and both messages", async () => {
    const fetchMock = vi.fn(
      async (_url: string, _init: RequestInit) =>
        fakeResponse({ choices: [{ message: { content: "[] " } }] })
    );
    const provider = createGitHubModelsProvider(
      { apiKey: "tok123", model: "openai/gpt-4o-mini" },
      fetchMock
    );
    const out = await provider.complete({ system: "sys", user: "usr" });
    expect(out).toBe("[] ");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] ?? [];
    expect(url).toBe(GITHUB_MODELS_ENDPOINT);
    const headers = init?.headers as Record<string, string>;
    expect(headers.authorization).toBe("Bearer tok123");
    expect(headers.accept).toBe("application/vnd.github+json");
    expect(headers["x-github-api-version"]).toBe(GITHUB_API_VERSION);
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    expect(body.model).toBe("openai/gpt-4o-mini");
    expect(body.messages).toEqual([
      { role: "system", content: "sys" },
      { role: "user", content: "usr" }
    ]);
  });

  it("uses a custom endpoint when provided", async () => {
    const fetchMock = vi.fn(async (_url: string, _init: RequestInit) =>
      fakeResponse({ choices: [{ message: { content: "x" } }] })
    );
    const provider = createGitHubModelsProvider(
      { apiKey: "t", endpoint: "https://example.test/chat" },
      fetchMock
    );
    await provider.complete({ system: "s", user: "u" });
    expect(fetchMock.mock.calls[0]?.[0]).toBe("https://example.test/chat");
  });

  it("throws on non-2xx responses", async () => {
    const provider = createGitHubModelsProvider(
      { apiKey: "t" },
      async () => fakeResponse({}, false, 401)
    );
    await expect(provider.complete({ system: "s", user: "u" })).rejects.toThrow(
      "HTTP 401"
    );
  });

  it("throws when the response has no content", async () => {
    const provider = createGitHubModelsProvider({ apiKey: "t" }, async () =>
      fakeResponse({ choices: [] })
    );
    await expect(provider.complete({ system: "s", user: "u" })).rejects.toThrow(
      "no content"
    );
  });

  it("throws a clear error when the response body is not JSON", async () => {
    const provider = createGitHubModelsProvider({ apiKey: "t" }, async () =>
      ({
        ok: true,
        status: 200,
        headers: { get: () => "text/plain" },
        text: async () => "OK"
      }) as unknown as Response
    );
    await expect(provider.complete({ system: "s", user: "u" })).rejects.toThrow(
      "non-JSON response (content-type: text/plain): OK"
    );
  });
});

describe("createGitHubModelsProvider resilience", () => {
  it("retries a 429 and succeeds on the next attempt", async () => {
    let calls = 0;
    const fetchMock = vi.fn(async (_url: string, _init: RequestInit) => {
      calls += 1;
      if (calls === 1) return fakeResponse({}, false, 429);
      return fakeResponse({ choices: [{ message: { content: "recovered" } }] });
    });
    const provider = createGitHubModelsProvider(
      { apiKey: "t", retries: 3, retryBaseDelayMs: 0 },
      fetchMock
    );
    await expect(provider.complete({ system: "s", user: "u" })).resolves.toBe("recovered");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("gives up once retries are exhausted", async () => {
    const fetchMock = vi.fn(async (_url: string, _init: RequestInit) =>
      fakeResponse({}, false, 503)
    );
    const provider = createGitHubModelsProvider(
      { apiKey: "t", retries: 2, retryBaseDelayMs: 0 },
      fetchMock
    );
    await expect(provider.complete({ system: "s", user: "u" })).rejects.toThrow("HTTP 503");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("aborts a slow request at the timeout and retries", async () => {
    const fetchMock = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => {
            const error = new Error("This operation was aborted");
            error.name = "AbortError";
            reject(error);
          });
        })
    );
    const provider = createGitHubModelsProvider(
      { apiKey: "t", timeoutMs: 5, retries: 2, retryBaseDelayMs: 0 },
      fetchMock
    );
    await expect(provider.complete({ system: "s", user: "u" })).rejects.toThrow(
      "timed out after 5ms"
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.signal).toBeInstanceOf(AbortSignal);
  });
});
