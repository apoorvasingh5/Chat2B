import { z } from "zod";
import type { CxbotConfig } from "./config.js";
import type { Finding } from "./findings.js";
import { buildSystemPrompt, buildUserPrompt } from "./prompt.js";
import type { LLMProvider } from "./provider.js";
import { sanitizeModelText, sanitizePatchText } from "./sanitize.js";

export const verdictItemSchema = z.object({
  id: z.string(),
  verdict: z.enum(["confirmed", "stale", "uncertain"]),
  confidence: z.enum(["observed", "inferred", "proposed"]),
  title: z.string().max(500),
  details: z.string().max(4000),
  fix: z
    .object({
      explanation: z.string().max(2000),
      patch: z.string().max(8000)
    })
    .optional(),
  reason_if_skipped: z.string().max(1000).optional()
});

export type Verdict = z.infer<typeof verdictItemSchema>;

export class TriageParseError extends Error {
  constructor(detail: string) {
    super(`triage response unparseable: ${detail}`);
    this.name = "TriageParseError";
  }
}

export function parseModelJson(raw: string): unknown[] {
  let text = raw.trim();
  const fence = /^```(?:json)?\s*([\s\S]*?)\s*```$/m.exec(text);
  if (fence?.[1]) text = fence[1];
  const start = text.indexOf("[");
  const end = text.lastIndexOf("]");
  if (start < 0 || end <= start) {
    throw new TriageParseError("no JSON array found in model response");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(text.slice(start, end + 1));
  } catch (error) {
    throw new TriageParseError(error instanceof Error ? error.message : String(error));
  }
  if (!Array.isArray(parsed)) throw new TriageParseError("model response is not a JSON array");
  return parsed;
}

export interface TriageResult {
  verdicts: Verdict[];
  dropped: { unknownIds: number; invalidItems: number };
}

export interface TriageDeps {
  provider: LLMProvider;
  config: CxbotConfig;
  evidence?: Map<string, string>;
}

export async function triageFindings(
  findings: Finding[],
  pr: { title: string; body: string },
  deps: TriageDeps
): Promise<TriageResult> {
  const pathInstructions = deps.config.path_instructions
    .filter((entry) => findings.some((f) => f.file.startsWith(entry.path.replace(/\*\*$/, ""))))
    .map((entry) => `${entry.path}: ${entry.instructions}`);

  const system = buildSystemPrompt(deps.config);
  const user = buildUserPrompt({
    prTitle: pr.title,
    prBody: pr.body,
    findingsJson: JSON.stringify(
      findings.map((finding) => {
        const excerpt = deps.evidence?.get(finding.id);
        return excerpt === undefined ? finding : { ...finding, evidence: excerpt };
      }),
      null,
      2
    ),
    pathInstructions
  });

  const raw = await deps.provider.complete({ system, user });
  const items = parseModelJson(raw);

  const knownIds = new Set(findings.map((f) => f.id));
  const verdicts: Verdict[] = [];
  let unknownIds = 0;
  let invalidItems = 0;

  for (const item of items) {
    const parsed = verdictItemSchema.safeParse(item);
    if (!parsed.success) {
      invalidItems += 1;
      continue;
    }
    if (!knownIds.has(parsed.data.id)) {
      unknownIds += 1;
      continue;
    }
    const data = parsed.data;
    let fix: Verdict["fix"];
    if (data.fix) {
      const patch = sanitizePatchText(data.fix.patch);
      if (patch !== undefined) {
        fix = { explanation: sanitizeModelText(data.fix.explanation), patch };
      }
    }
    verdicts.push({
      ...data,
      title: sanitizeModelText(data.title),
      details: sanitizeModelText(data.details),
      reason_if_skipped:
        data.reason_if_skipped === undefined
          ? undefined
          : sanitizeModelText(data.reason_if_skipped),
      fix
    });
  }

  return { verdicts, dropped: { unknownIds, invalidItems } };
}
