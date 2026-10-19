# threat-modelling

A Claude Code skill that turns architecture artifacts — and, within strict bounds, a source repository — into a structured, evidence-cited, repeatable threat model: a security knowledge graph, STRIDE/OWASP-based threats *and* business-logic/abuse-case threats no scanner catalog covers, attack paths, mitigations, and concrete SAST/DAST guidance, rendered as a single self-contained HTML report.

[SKILL.md](SKILL.md) is the actual operating manual the model reads (orchestration phases, sub-agent prompts, guardrails). This document is the design map: what the pieces are, why they're shaped this way, and how to extend them. Start here if you want to understand the system; go to `SKILL.md` for the literal instructions it follows.

## Why this exists

Most "AI threat modeling" is one unstructured pass: read some docs, maybe read some code, output a threat list. That has two failure modes this skill is built to avoid:

1. **Guessing instead of knowing.** An LLM asked to map a CWE to a Checkmarx query, or an ATT&CK technique, or a regex over a 300-file repo, will produce something *plausible* — not something *correct*. Anywhere a fact can be looked up or computed instead of inferred, this skill does that in a deterministic script, not in the model's head.
2. **Unbounded, unauditable exploration.** Pointing an agent at a repository and saying "look around" works, but it's unreproducible (a second run touches different files), uncapped in cost, and produces no record of what was actually read versus assumed. Every piece of repo-derived evidence here is either a structured script output with a `file:line` citation, or a logged, bounded, reason-justified snippet read — never a silent, untracked file open.

## Core design principles

- **Scripts find candidates; the model judges what they mean.** A script never gets the final word on severity or exploitability — it surfaces a structural fact (a risk pattern, an unenforced invariant, a security-relevant config toggle) and the model reasons about whether it's real, in context. Neither side does the other's job.
- **Extend behavior with data, not code.** Supporting a new web framework, RPC protocol, or insecure-config pattern means adding a row to a JSON registry (`references/repo-patterns/*.json`), never adding `if repo uses X` branching to a Python script. The engines (`scan_repo_surface.py`, `map_attack_techniques.py`, `recommend_sast_queries.py`) are permanently generic.
- **Facts carry their own confidence, always.** Every extracted entity has a `confidence` and `source_refs`. Every heuristic result says so in its own `note` field (`"authorization_check": "Unknown"` means *the heuristic found nothing*, not *there is no check*). Nothing silently gets upgraded to certainty.
- **Never read a repository directly.** Not `Read`, not `Grep`, not `Glob` — see [The Repo Context Agent](#the-repo-context-agent-bounded-repo-analysis) below. This is the one guardrail the design spends the most effort on, because it's the one most tempting to quietly relax.
- **One source of truth, two renderings.** `threat-model-output.json` (schema in `references/output-schemas/`) is authoritative; the HTML report is *rendered from it*, never hand-authored — so the two can never drift apart, and the JSON is just as usable as input to another agent or tool.
- **Missing information is not a reason to stop.** If evidence runs out, the skill produces the fullest report the available evidence supports, with everything unknown listed as an explicit open question in the same output — never a blocking question with no report attached.

## Architecture overview

### Nine-phase pipeline

| Phase | What happens |
|---|---|
| 1. Intake | Identify objective, inputs (including whether a repo path was given), scope, technology domains |
| 2. Artifact Parsing | Deterministically parse each document (`parse_markdown/html/pdf.py`) and/or run the repo deep dive (see below) |
| 3. Architecture Extraction | Extract components, data flows, trust boundaries, security controls, **and business workflows**; `normalize_entities.py` dedupes and assigns canonical IDs |
| 4. Graph Construction | `build_graph.py` turns normalized entities into a schema-valid graph and runs 15 algorithmic high-risk pattern detectors |
| 5. Questionnaire Application | Domain questionnaires (cloud/web/mobile/api) **plus** the always-loaded cross-cutting `business-logic.yaml` |
| 6. Threat Analysis | **Tier 1** (catalog-driven: STRIDE/OWASP/CWE) and **Tier 2** (business-logic/abuse-case) — see below |
| 7. Attack Path Analysis | Chain threats into realistic, graph-grounded attack paths |
| 8. Recommendations | Mitigations, SAST config (`recommend_sast_queries.py` against a real Checkmarx query catalog), DAST guidance, prioritized action items |
| 9. Final Report | Assemble `threat-model-output.json`, render it to HTML via `export_report.py` |

### Thirteen sub-agents (logical roles within one model, `SKILL.md` §8)

Intake Coordinator → Artifact Ingestion (→ **Repo Context Agent**, §2.1) → Architecture Extraction → Technology Fingerprinting → Graph Builder → Questionnaire Mapping → Dynamic Question Generator → Threat Identification (Tier 1) → Attack Path → Mitigation Recommendation → SAST Recommendation → DAST Recommendation → **Business Logic & Abuse Case Agent** (Tier 2, §13).

### Two-tier threat identification

The single most important split in the design:

- **Tier 1 — catalog-driven.** STRIDE/OWASP/CWE-mappable threats: the kind a SAST/DAST scanner would also find (missing auth, injection, weak crypto). Backed by `build_graph.py`'s deterministic graph-risk-pattern detectors.
- **Tier 2 — business logic & abuse case.** Threats that exist only in the *sequence and intent* of a multi-step process — every individual request involved is syntactically valid, so no scanner catalog entry applies. Backed by an explicit `business_workflows` model (ordered steps, client-trusted fields, invariants) and `analyze_workflows.py`'s structural detectors (step reachable out of order, missing idempotency, a client-supplied completion flag trusted as fact, an invariant with no enforcement point, missing compensation on partial failure).

A report that only runs Tier 1 is re-deriving what Checkmarx/a DAST scanner already tells you. Tier 2 is what justifies doing this as a distinct exercise.

## The Repo Context Agent: bounded repo analysis

### The guardrail

The model must never `Read`/`Grep`/`Glob` a target repository, even at a filename level, even when a repo path is the explicit input (`SKILL.md` §5). The one exception is a fixed set of scripts, run only when the user explicitly hands over a repo path — never on the agent's own initiative.

### The harness (`scripts/repo_deep_dive.py`)

```
repo_deep_dive.py
 ├─ scan_repo_manifest.py   → languages / frameworks from dependency manifests
 ├─ scan_repo_surface.py    → generic, registry-driven entry-point + config-risk scan (below)
 └─ scan_repo_infra.py      → Dockerfile / compose / Kubernetes config line patterns
 → consolidated repo_insights.json, with an explicit coverage_report.gaps list
```

`coverage_report.gaps` exists so "found nothing" and "didn't know where to look" are never indistinguishable — a zero-manifest, zero-entry-point, or zero-infra-file result is a *named* gap, not a silent thin report.

### `scan_repo_surface.py`: the generic engine, zero framework-specific code

This script has no knowledge of any particular framework. Everything it recognizes is a row in one of two data registries:

- **`references/repo-patterns/entrypoint-patterns.json`** — "what an external caller invokes": REST routes (Flask/FastAPI/Django/Express/Spring/ASP.NET/Go web frameworks/Rails/Laravel), MCP tool registrations (Go/Python/TS SDKs), gRPC methods, GraphQL resolvers, message consumers, CLI commands, scheduled jobs, serverless handlers.
- **`references/repo-patterns/code-risk-patterns.json`** — insecure, flaggable configuration toggles: `InsecureSkipVerify: true`, a `*_TLS_SKIP_VERIFY` / `JWT_VERIFY`-shaped env var, CORS wildcards, debug-mode flags — plus a best-effort capture of the literal default value sitting next to them.

Supporting gRPC today and a new queue library tomorrow means adding a JSON entry to one of these files. The Python engine does not change. Every match carries a `needs_deep_dive` heuristic (sensitive-sounding name/action + no authorization keyword found nearby) that prioritizes it for the next step.

### `read_repo_snippet.py`: the bounded, audited "AI-native" half

Deterministic pattern matching can locate *where* something interesting is but can't judge *what it means* — that still needs the model's actual reasoning. This script is the one narrow, controlled channel for that:

- Returns a small window of real source text (default ≤60 lines, hard-capped at 200) around one already-cited `file:line`.
- Refuses any path that resolves outside `--repo-root` (blocks `../` escapes) and any secret-shaped filename (`.env`, `*.pem`, `id_rsa`, `credentials.*`) outright.
- Requires a `--reason` on every call and appends it to a persistent audit log — a complete, reviewable record of every piece of source text the model ever looked at and why.

This is deliberately *not* general file access. It is how the model follows up on a specific flagged candidate, one call at a time, with the full trail kept.

### Token efficiency: measured, not estimated

An earlier, unstructured run of this skill against a real ~300-file Go MCP server repository (`security-mcp`) did a genuinely unrestricted agentic deep dive — reading files directly, no bound on how much. Re-running the current harness against the same repository and measuring the actual bytes involved:

| What has to enter the model's context | Size |
|---|---|
| `repo_insights.json` (the consolidated harness output) | ~36 KB |
| ~10 targeted `read_repo_snippet.py` calls (≤60 lines each) | ~15–20 KB |
| **Total, current design** | **~55 KB (≈ 16,000 tokens at ~3.5 chars/token)** |
| Reading only the 30 files that patterns actually matched, in full | ~590 KB (≈ 170,000 tokens) |
| Reading the full non-vendor, non-test source tree (a realistic unrestricted-dive upper bound) | ~1.15 MB (≈ 335,000 tokens) |

That's a measured **~90–95% reduction** in repo-derived tokens, depending on how much of the repository an unrestricted pass would actually have touched (the two baselines above bound that range; there's no logged token count from the earlier run to compare against directly, so this is a transparent proxy calculation from real file sizes, not a vendor-reported number). The token saving isn't incidental — it's the direct consequence of the design principle above: a cheap deterministic pass narrows "600 KB of code" down to "36 KB of structured facts plus a handful of 60-line, purpose-justified reads."

The one real cost of this bound: things a human-written architecture doc states in prose (a named third-party vendor, a cache's existence) can be missed if the registries don't yet have a pattern for the code shape that reveals it. `code-risk-patterns.json` and `entrypoint-patterns.json` are living files for exactly this reason — each gap found in practice becomes a new row, not a reason to loosen the guardrail.

## Business workflow model (Tier 2's input)

A `data_flow` is point-to-point ("Mobile App CALLS Payment API"). A `business_workflow` is an ordered, multi-step process with state and rules that only exist across several flows. Schema (`references/output-schemas/threat-model-output.json`, `$defs.workflow`):

- **Steps**, each with: the component performing it, `client_supplied_fields` (the single highest-value field — what does this step trust from the caller instead of deriving server-side), `state_change`, `authorization_check`, `idempotency_required`, `reversible`, `rate_limited`, `confirms_or_reviews`.
- **Invariants** — business rules that must hold across the whole workflow, each with an `enforced_by_step` (or `"Unknown"`, which is itself a finding).

`analyze_workflows.py` runs nine structural detectors over this model: a step reachable without its prerequisite, a state-changing step with no idempotency evidence, a client-supplied field trusted without an authorization re-check, an irreversible step with no confirmation gate, a sensitive repeatable step with no rate limit, a client-declared completion/status flag trusted as fact, an unverified async callback finalizing state, an invariant with no enforcement point, a multi-step process with no compensation/rollback step.

## MITRE ATT&CK / CAPEC mapping

`scripts/map_attack_techniques.py` looks up CWEs and graph-risk-pattern keys against `references/threat-frameworks/attack-technique-map.json` — a small, explicitly-labeled **seed** table (`"confidence": "seed-unverified"` on every entry), not a claim of completeness. It deliberately returns *no* technique for threats that don't have a clean match (most application-logic weaknesses don't) rather than forcing one — see `mitre-attack.md` / `capec.md` for the reasoning on when a citation is and isn't appropriate.

## Output: one source of truth, one rendering

- **`threat-model-output.json`** (schema: `references/output-schemas/threat-model-output.json`) — the structured result: metadata, executive summary, architecture summary, `business_workflows`, technology profile, questionnaire results, threats (Tier 1 and Tier 2 together, distinguished by `category`), attack paths, mitigations, SAST/DAST recommendations, action items, residual risk, and an appendix carrying the full graph.
- **The HTML report** (`assets/report-template.html`, rendered via `export_report.py`) is generated *from* that JSON — architecture and attack-path diagrams are Mermaid.js source computed deterministically from the graph, never hand-drawn.
- **`scripts/diff_threat_reports.py`** compares two of this skill's own HTML reports (components/threats added or removed, category/severity shifts) so re-running after new evidence or a skill change is a repeatable command instead of reading two reports side by side by eye.

## Directory structure

```
SKILL.md                         # the actual operating instructions the model follows
scripts/                         # every deterministic pipeline step
  parse_markdown.py / parse_html.py / parse_pdf.py      # Phase 2: document ingestion
  repo_deep_dive.py                                     # Phase 2: repo harness (orchestrates the three below)
  scan_repo_manifest.py / scan_repo_surface.py / scan_repo_infra.py
  read_repo_snippet.py                                  # Phase 2: bounded, audited follow-up reads
  normalize_entities.py / build_graph.py                # Phase 3/4: entity + graph construction
  analyze_workflows.py                                  # Phase 6 Tier 2: business-logic structural checks
  recommend_sast_queries.py / map_attack_techniques.py  # Phase 6-8: deterministic lookups
  export_report.py                                      # Phase 9: JSON -> HTML
  diff_threat_reports.py                                # compare two reports
  common.py                                             # shared utilities, zero required dependencies
references/
  output-schemas/        # graph-schema.json, threat-model-output.json (JSON Schema)
  questionnaires/        # cloud/web/mobile/api.yaml + the always-loaded business-logic.yaml
  threat-frameworks/     # STRIDE, OWASP (web/api/mobile/LLM/agentic-AI), SANS-25, MITRE ATT&CK, CAPEC
  repo-patterns/         # entrypoint-patterns.json, code-risk-patterns.json -- the extensible registries
  cx-presets-queries/    # Checkmarx's SAST query/preset catalog (internal; private repo only)
assets/report-template.html      # the HTML report template
examples/                        # a worked walkthrough and sample outputs
artifacts/                       # sample intermediate pipeline outputs
```

## Extending the skill

- **New framework/protocol for repo scanning** → add an entry to `entrypoint-patterns.json`. New insecure-config pattern → add one to `code-risk-patterns.json`. Never add branching logic to `scan_repo_surface.py`.
- **New questionnaire item** → add to the relevant `references/questionnaires/*.yaml` (same `id`/`question`/`intent` shape).
- **New graph-level risk pattern** → add a detector function in `build_graph.py`'s `detect_risk_patterns`, give it a stable `pattern_key`.
- **New business-logic structural check** → add a detector in `analyze_workflows.py`, following the existing `pattern_key`/severity/evidence shape.
- **Better CWE/CAPEC/ATT&CK coverage** → extend `attack-technique-map.json`; it's explicitly a seed table meant to grow, ideally eventually replaced with data pulled from the authoritative MITRE sources rather than hand-curated entries.

## What this intentionally does not do

- It does not clone, browse, or read a repository outside the Repo Context Agent's fixed scripts — see the guardrail above.
- It does not perform a general SAST-style code review. `read_repo_snippet.py` follows up on specific flagged candidates; it is not a substitute for actually running SAST/DAST.
- It does not produce any final-report format other than the self-contained HTML (rendered from the JSON) — no Markdown, PDF, Jira, or CSV export of the final deliverable.
- It does not assert certainty it doesn't have: every heuristic result, every seed-table lookup, and every repo-derived fact says so explicitly rather than being silently upgraded.
