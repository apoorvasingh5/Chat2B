import { resolve } from "node:path";
import {
  buildBundle,
  loadScannerFindings,
  summarizeFindings,
  writeBundle
} from "./artifacts.js";
import { loadWorkspaceConfig } from "./config.js";

const root = process.env.GITHUB_WORKSPACE ?? process.cwd();
const { config, source } = loadWorkspaceConfig(root);

const findings = loadScannerFindings(
  {
    trufflehog: resolve(root, "trufflehog.json"),
    cxone: resolve(root, "cxone.sarif")
  },
  config
);

const summary = summarizeFindings(findings);
writeBundle(buildBundle(findings, summary, source), resolve(root, "findings.json"));

console.log(
  `cxbot analyze [${source}]: ${summary.total} findings; ` +
    `byScanner=${JSON.stringify(summary.byScanner)}; ` +
    `bySeverity=${JSON.stringify(summary.bySeverity)}`
);
