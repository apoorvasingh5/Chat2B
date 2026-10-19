import { describe, expect, it, vi } from "vitest";
import {
  isRetryableError,
  RETRYABLE_STATUSES,
  statusOf,
  withRetry
} from "../src/retry.js";

const noSleep = async (): Promise<void> => {};

function httpError(status: number): Error & { status: number } {
  const error = new Error(`HTTP ${status}`) as Error & { status: number };
  error.status = status;
  return error;
}

describe("withRetry", () => {
  it("returns the first success without sleeping", async () => {
    const fn = vi.fn(async () => "ok");
    const sleep = vi.fn(noSleep);
    await expect(withRetry(fn, { sleep })).resolves.toBe("ok");
    expect(fn).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it("retries retryable failures and then succeeds", async () => {
    let calls = 0;
    const fn = vi.fn(async () => {
      calls += 1;
      if (calls < 3) throw httpError(429);
      return "done";
    });
    const sleep = vi.fn(noSleep);
    await expect(withRetry(fn, { attempts: 3, sleep })).resolves.toBe("done");
    expect(fn).toHaveBeenCalledTimes(3);
    expect(sleep).toHaveBeenCalledTimes(2);
  });

  it("does not retry non-retryable errors", async () => {
    const fn = vi.fn(async () => {
      throw httpError(400);
    });
    const sleep = vi.fn(noSleep);
    await expect(withRetry(fn, { sleep })).rejects.toThrow("HTTP 400");
    expect(fn).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it("throws the last error once attempts are exhausted", async () => {
    const fn = vi.fn(async () => {
      throw httpError(503);
    });
    const sleep = vi.fn(noSleep);
    await expect(withRetry(fn, { attempts: 3, sleep })).rejects.toThrow("HTTP 503");
    expect(fn).toHaveBeenCalledTimes(3);
    expect(sleep).toHaveBeenCalledTimes(2);
  });

  it("backs off exponentially and caps at maxDelayMs", async () => {
    const fn = vi.fn(async () => {
      throw httpError(502);
    });
    const delays: number[] = [];
    await withRetry(fn, {
      attempts: 4,
      baseDelayMs: 100,
      maxDelayMs: 250,
      sleep: async (ms) => {
        delays.push(ms);
      }
    }).catch(() => undefined);
    expect(delays).toEqual([100, 200, 250]);
  });

  it("honors a retry-after hint over the backoff", async () => {
    const fn = vi.fn(async () => {
      const error = new Error("slow down") as Error & {
        status: number;
        retryAfterMs?: number;
      };
      error.status = 429;
      error.retryAfterMs = 1234;
      throw error;
    });
    const delays: number[] = [];
    await withRetry(fn, {
      attempts: 2,
      baseDelayMs: 10,
      sleep: async (ms) => {
        delays.push(ms);
      }
    }).catch(() => undefined);
    expect(delays).toEqual([1234]);
  });

  it("retries errors flagged retryable regardless of status", async () => {
    let calls = 0;
    const fn = vi.fn(async () => {
      calls += 1;
      if (calls === 1) {
        const error = new Error("aborted") as Error & { retryable?: boolean };
        error.retryable = true;
        throw error;
      }
      return "recovered";
    });
    await expect(withRetry(fn, { attempts: 2, sleep: noSleep })).resolves.toBe("recovered");
  });
});

describe("isRetryableError", () => {
  it("classifies statuses", () => {
    for (const status of RETRYABLE_STATUSES) {
      expect(isRetryableError({ status })).toBe(true);
    }
    expect(isRetryableError({ status: 404 })).toBe(false);
    expect(isRetryableError(new Error("plain"))).toBe(false);
  });

  it("treats explicitly flagged errors as retryable", () => {
    expect(isRetryableError({ retryable: true })).toBe(true);
    expect(statusOf({ status: 429 })).toBe(429);
    expect(statusOf(new Error("x"))).toBeUndefined();
  });
});
