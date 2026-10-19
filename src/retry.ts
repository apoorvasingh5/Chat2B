export interface RetryOptions {
  attempts?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  sleep?: (ms: number) => Promise<void>;
  isRetryable?: (error: unknown) => boolean;
}

export const RETRYABLE_STATUSES = new Set([408, 425, 429, 500, 502, 503, 504]);

interface ErrorWithStatus {
  status?: number;
  retryable?: boolean;
  retryAfterMs?: number;
}

export function statusOf(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null) {
    const status = (error as ErrorWithStatus).status;
    if (typeof status === "number") return status;
  }
  return undefined;
}

export function retryAfterMsOf(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null) {
    const hint = (error as ErrorWithStatus).retryAfterMs;
    if (typeof hint === "number" && Number.isFinite(hint) && hint >= 0) return hint;
  }
  return undefined;
}

export function isRetryableError(error: unknown): boolean {
  if (typeof error === "object" && error !== null && (error as ErrorWithStatus).retryable === true) {
    return true;
  }
  const status = statusOf(error);
  return status !== undefined && RETRYABLE_STATUSES.has(status);
}

function defaultSleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function withRetry<T>(fn: () => Promise<T>, options: RetryOptions = {}): Promise<T> {
  const attempts = Math.max(1, options.attempts ?? 3);
  const baseDelayMs = options.baseDelayMs ?? 300;
  const maxDelayMs = options.maxDelayMs ?? 5000;
  const sleep = options.sleep ?? defaultSleep;
  const isRetryable = options.isRetryable ?? isRetryableError;

  let lastError: unknown;
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (!isRetryable(error) || attempt === attempts) throw error;
      const hint = retryAfterMsOf(error);
      const backoff = Math.min(maxDelayMs, baseDelayMs * 2 ** (attempt - 1));
      await sleep(hint === undefined ? backoff : Math.min(maxDelayMs, hint));
    }
  }
  throw lastError;
}
