import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { parse as parseYaml } from "yaml";
import { z } from "zod";

export const configSchema = z.object({
  language: z.string().optional(),
  tone_instructions: z.string().max(250).optional(),
  profile: z.enum(["quiet", "balanced", "thorough"]).default("balanced"),
  scanners: z
    .object({
      trufflehog: z.boolean().default(true),
      cxone: z.boolean().default(true),
      require_verified: z.boolean().default(false)
    })
    .default({}),
  auto_review: z
    .object({
      enabled: z.boolean().default(true),
      drafts: z.boolean().default(false),
      base_branches: z.array(z.string()).default(["^main$"]),
      labels: z.array(z.string()).default([]),
      ignore_usernames: z.array(z.string()).default([]),
      ignore_author_associations: z.array(z.string()).default([])
    })
    .default({}),
  path_filters: z.array(z.string()).default([]),
  path_instructions: z
    .array(
      z.object({
        path: z.string(),
        instructions: z.string().max(20000)
      })
    )
    .default([]),
  deny_fix_paths: z
    .array(z.string())
    .default([".github/workflows/**", "**/*.lock", "package-lock.json", "pnpm-lock.yaml"])
});

export type CxbotConfig = z.infer<typeof configSchema>;

export function parseConfig(yamlText: string): CxbotConfig {
  const raw: unknown = parseYaml(yamlText) ?? {};
  return configSchema.parse(raw);
}

export function defaultConfig(): CxbotConfig {
  return configSchema.parse({});
}

export function loadWorkspaceConfig(
  workspaceRoot: string = process.env.GITHUB_WORKSPACE ?? process.cwd()
): { config: CxbotConfig; source: string } {
  const configPath = join(workspaceRoot, ".cxbot.yaml");
  if (existsSync(configPath)) {
    return { config: parseConfig(readFileSync(configPath, "utf8")), source: ".cxbot.yaml" };
  }
  return { config: defaultConfig(), source: "defaults" };
}
