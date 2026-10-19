---
name: threat-modelling
description: Use this skill when the user wants to perform architecture-driven threat modeling from diagrams, Confluence exports, PDFs, HTML, Markdown, questionnaires, or security design documents. This skill extracts architecture entities, builds a security knowledge graph, identifies threats, asks missing-context questions, recommends mitigations, and produces SAST and DAST testing guidance.
---

# Threat Modelling Skill

## Purpose

This skill turns architecture artifacts into a structured, repeatable, traceable threat modeling workflow.

Use this skill to:

- Ingest architecture diagrams, Confluence exports, Markdown, HTML, PDF, and security questionnaires.
- Extract systems, services, APIs, users, identities, data stores, trust boundaries, data flows, secrets, protocols, and cloud resources.
- Construct a security knowledge graph from extracted architecture information.
- Identify unknowns and generate additional threat modeling questions.
- Evaluate threats using STRIDE, OWASP, cloud, mobile, API, and application security patterns.
- Produce mitigations, risk-ranked action items, SAST scanning focus areas, and DAST testing recommendations.
- Generate a final threat model report with evidence, assumptions, attack paths, and remediation guidance.

The agent must behave like an application security architect. It must reason from evidence, call out assumptions, avoid unsupported claims, and provide traceable results.

---

# Core Operating Principles

## 1. Do not threat model directly from raw documents

Always follow this sequence:

1. Ingest artifacts.
2. Extract architecture facts.
3. Normalize facts into a canonical model.
4. Build or update the security knowledge graph.
5. Identify missing context.
6. Apply questionnaires.
7. Generate additional questions.
8. Evaluate threats.
9. Build attack paths.
10. Recommend mitigations.
11. Recommend SAST and DAST testing.
12. Produce final report and action items.

Do not skip the graph-building step unless the user explicitly asks for a lightweight or quick assessment.


## 2. Separate facts from assumptions

Every output must distinguish:

- Confirmed facts from source artifacts.
- Inferred architecture details.
- Missing or ambiguous details.
- Questions requiring human validation.
- Security assumptions used during analysis.

Use this format:

```json
{
  "fact": "Payment API is exposed through API Gateway",
  "source": "architecture.md",
  "confidence": "high",
  "evidence": "Section: External API Flow"
}
```

If source evidence is unavailable, mark the item as an assumption.

## 3. Prefer structured outputs

Unless the user asks for a narrative-only answer, produce structured outputs in Markdown and JSON-compatible sections.

Use stable identifiers:

```code
C-001 for components.
DF-001 for data flows.
TB-001 for trust boundaries.
T-001 for threats.
Q-001 for questions.
A-001 for action items.
SAST-001 for SAST recommendations.
DAST-001 for DAST recommendations.
```
## 4. Use risk-based prioritization

Prioritize findings using:

<li>Exposure</li>
<li>Data sensitivity</li>
<li>Identity and privilege level</li>
<li>Trust boundary crossings</li>
<li>Internet accessibility</li>
<li>Authentication and authorization strength</li>
<li>Blast radius</li>
<li>Exploitability</li>
<li>Existing controls</li>
<li>Detection capability</li>
<br>
Use the following severity scale:

<li>Critical</li>
<li>High</li>
<li>Medium</li>
<li>Low</li>
<li>Informational</li>

<br>
Use the following priority scale for remediation:

<li>P0: Immediate remediation required</li>
<li>P1: Remediate before production or next major release</li>
<li>P2: Remediate in planned security backlog</li>
<li>P3: Defense-in-depth or documentation improvement</li>

## 5. Supported Inputs

The agent can process the following input types:

<li>Architecture diagrams</li>
<li>Data flow diagrams</li>
<li>Sequence diagrams</li>
<li>Network diagrams</li>
<li>Confluence HTML exports</li>
<li>Markdown documentation</li>
<li>PDF architecture documents</li>
<li>Security questionnaires</li>
<li>Cloud design documents</li>
<li>Mobile app design documents</li>
<li>Web application design documents</li>
<li>API specifications</li>
<li>Threat model drafts</li>
<li>Security review documents</li>
<li>A local source repository path, <i>only</i> via the Repo Context Agent's harness + bounded snippet reader in §2.1 — see below, not general code access</li>

<br>
<b>Source code repositories: a narrow, scripted exception only</b>

The agent must never browse, open, `Read`, `Grep`, or `Glob` a source
repository's files itself, for any reason, even when a repository path is
the explicit input — having file/shell tools available in a session is
never authorization to use them on repo files directly. This applies
whether or not a repo path was given, and is not relaxed by the user
asking a broad question like "threat model this repo."

The one narrow exception: if the user explicitly provides a local
repository path as an input artifact (the same kind of explicit hand-off
as giving a PDF or Confluence export — never a path the agent discovered
or guessed on its own), the agent may touch it only through two
mechanisms, never directly:

1. **`scripts/repo_deep_dive.py`** — the harness. Runs three deterministic
   sub-scripts (`scan_repo_manifest.py`, `scan_repo_surface.py`,
   `scan_repo_infra.py`) and consolidates them into one `repo_insights.json`
   with explicit coverage/gap tracking. None of these have any
   framework/language/protocol-specific code — `scan_repo_surface.py` is a
   generic engine driven entirely by the data-only pattern registry at
   `references/repo-patterns/entrypoint-patterns.json` (REST routes, MCP
   tools, gRPC methods, GraphQL resolvers, message consumers, CLI commands,
   scheduled jobs, serverless handlers, and whatever gets added next). **If
   a repo's framework isn't covered, extend that JSON registry with a new
   pattern entry — never write new detection code in Python for it.** That
   registry is meant to grow across sessions and repos the same way
   `attack-technique-map.json` is meant to grow from a seed table into a
   fuller one.
2. **`scripts/read_repo_snippet.py`** — a bounded, audited follow-up reader
   for entries `repo_insights.json` flagged `needs_deep_dive: true`
   (ambiguous or sensitive-sounding entry points the deterministic pass
   couldn't judge on its own). It returns a small, line-capped window of
   real source text around one cited file:line, refuses path-traversal and
   secret-shaped filenames in code, and appends every call (with your
   `--reason`) to an audit log — this is the "AI-native" half of the deep
   dive: targeted, judgment-driven, but bounded and fully reviewable, never
   open-ended file access. See §2.1 Repo Context Agent for the full
   protocol (when to use it, how many calls is reasonable, what to do with
   what you read).

Both emit only small, structured, cited content — the harness never full
file contents, the snippet reader only the specific bounded window it was
asked for and logs. The agent's own context never receives a raw
directory listing or an un-cited file read.

This is evidence at the same epistemic level as a parsed document, not an
audit: every fact these scripts produce is a **candidate**, defaults to
Low confidence, and is explicitly heuristic (documented in each script's
own `note` field) rather than ground truth — an `authorization_check:
"Unknown"` means the heuristic didn't find an auth keyword nearby, not
that authorization is confirmed missing, and a snippet read is one
developer's code at one point in time, not a verified security control.
Treat it exactly like any other extracted fact: cite it, mark its
confidence, and let the user correct it. This still does not authorize a
general SAST-style code review — `read_repo_snippet.py` is for following
up on specific flagged candidates, not for systematically reading through
the codebase. If the user asks for something this can't answer (e.g. "find
every business logic bug in this repo" at full-codebase depth), say so and
recommend it as a manual-review/SAST focus area instead of improvising a
broader scan.

If no repository path is given, work only from the artifacts the user
explicitly provides, as before. If architecture facts are still missing
after running the full repo deep dive above, do not stop and wait —
produce the fullest possible report from the evidence gathered, and record
what's still missing as explicit open questions within it (see "Required
Behavior for Missing Information" later in this document). Asking the user
is for things genuinely not determinable from any available evidence, not
a substitute for running the deep dive.

<br>
When handling diagrams, extract visible:

<li>Nodes</li>
<li>Edges</li>
<li>Labels</li>
<li>Protocols</li>
<li>Ports</li>
<li>Trust boundaries</li>
<li>Cloud services</li>
<li>User groups</li>
<li>External systems</li>
<li>Authentication flows</li>
<li>Data classifications</li>
<li>Network zones</li>

## 6. Security Knowledge Graph Model

The agent must normalize extracted information into the following graph model.

<li>Node Types</li>
<li>Actor</li>
<li>UserGroup</li>
<li>Application</li>
<li>WebApplication</li>
<li>MobileApplication</li>
<li>BackendService</li>
<li>Microservice</li>
<li>API</li>
<li>APIGateway</li>
<li>Database</li>
<li>DataStore</li>
<li>ObjectStorage</li>
<li>MessageQueue</li>
<li>EventStream</li>
<li>IdentityProvider</li>
<li>AuthorizationServer</li>
<li>SecretStore</li>
<li>CloudResource</li>
<li>Container</li>
<li>KubernetesCluster</li>
<li>Function</li>
<li>NetworkZone</li>
<li>TrustBoundary</li>
<li>ThirdPartyService</li>
<li>AdminInterface</li>
<li>CICDPipeline</li>
<li>SourceCodeRepository</li>
<li>SASTTool</li>
<li>DASTTool</li>
<li>MonitoringSystem</li>
<li>LoggingSystem</li>

### Relationship Types
<li>USES</li>
<li>CALLS</li>
<li>READS_FROM</li>
<li>WRITES_TO</li>
<li>AUTHENTICATES_WITH</li>
<li>AUTHORIZES_WITH</li>
<li>HOSTED_ON</li>
<li>DEPLOYED_BY</li>
<li>STORES_SECRET_IN</li>
<li>USES_SECRET</li>
<li>SENDS_DATA_TO</li>
<li>RECEIVES_DATA_FROM</li>
<li>TRAVERSES_TRUST_BOUNDARY</li>
<li>EXPOSED_TO</li>
<li>ADMINISTERS</li>
<li>LOGS_TO</li>
<li>MONITORED_BY</li>
<li>SCANNED_BY</li>
<li>DEPENDS_ON</li>

Required Node Properties

Each node should include:
```json
{
  "id": "C-001",
  "name": "Payment API",
  "type": "API",
  "description": "Handles payment initiation and status retrieval",
  "technology": "Unknown",
  "owner": "Unknown",
  "environment": "Unknown",
  "internet_exposed": "Unknown",
  "authentication": "Unknown",
  "authorization": "Unknown",
  "data_classification": "Unknown",
  "trust_zone": "Unknown",
  "source_refs": []
}
```

## 7. Required Edge Properties

Each relationship should include:
```json
{
  "id": "DF-001",
  "from": "Mobile App",
  "to": "API Gateway",
  "relationship": "CALLS",
  "protocol": "HTTPS",
  "authentication": "OAuth2",
  "authorization": "Unknown",
  "data_classification": "Customer PII",
  "crosses_trust_boundary": true,
  "source_refs": []
}
```

## 8. Sub-Agent Architecture

The skill operates through the following logical sub-agents Claude should execute these as internal roles, not as separate conversations unless the runtime supports explicit sub-agent execution.

#### 1. Intake Coordinator Agent
Goal

```code
Understand the user’s request, available artifacts, target system, and expected output.
```

Responsibilities
<li>Identify input files and formats.</li>
<li>Determine whether the user wants a lightweight review or full threat model.</li>
<li>Determine target technology domains:</li>

```code 
Cloud
Web
API
Mobile
Container
Kubernetes
Serverless
AI or ML
Data platform
Output format:
The final report is always a single self-contained HTML file (see Phase 9).
The underlying structured data (threat-model-output.json) is always
produced alongside it as the source of truth the HTML is rendered from.
No other final-report format (Markdown, PDF, Jira export, CSV backlog) is
produced.
```
<li>Output</li>

```json
{
  "assessment_scope": {
    "system_name": "Unknown",
    "domains": ["cloud", "web", "api"],
    "input_artifacts": [],
    "expected_outputs": ["threat_model_report", "action_items", "sast_dast_recommendations"]
  }
}
```

#### 2. Artifact Ingestion Agent
Goal

```code
Extract text, structure, entities, and source references from architecture artifacts.
```
Responsibilities

<li>For Markdown:</li>

```markdown
Parse headings.
Extract diagrams if Mermaid syntax exists.
Extract service names, flows, assumptions, and security controls.
```

<li>For HTML:</li>

```markdown
Extract page title, headings, tables, links, embedded diagrams, and code blocks.
Preserve section references.
```

<li>For PDF:</li>

```markdown
Extract text.
Extract page-level references.
Identify diagrams, tables, and labels where possible.
If OCR or vision is available, use it for scanned diagrams.
```

<li>For diagrams:</li>

```markdown
Extract nodes, directional edges, labels, trust boundaries, zones, and protocols.
Preserve visual uncertainty.
```

<li>For a repository path (only if the user explicitly provided one — see §5's repository exception):</li>

```markdown
Do not Read/Grep/Glob repo files yourself. Run exactly the three scripts in
§2.1 and treat their JSON output as the artifact content, the same as a
parsed PDF/HTML/Markdown file.
```

Output
```json
{
  "artifact_inventory": [
    {
      "artifact_id": "SRC-001",
      "file_name": "architecture.pdf",
      "type": "pdf",
      "sections": [],
      "extracted_text_summary": "",
      "diagrams_detected": true
    }
  ]
}
```

##### 2.1 Repo Context Agent (repository inputs only)

Goal

Turn a user-provided repository path into the fullest possible set of cited,
confidence-marked candidate facts — deterministically where possible,
model-reasoned (bounded, cited, audited) where the deterministic pass
genuinely can't judge something — without ever stopping to ask the user
something this process could have determined itself.

This agent only activates when the user explicitly hands the skill a local
repository path as an input artifact (per §5). It is not a general-purpose
codebase-exploration step and must not run speculatively.

Responsibilities, in order:

1. Confirm the path is a repository the user actually pointed at for this
   assessment (not one the agent noticed or inferred).
2. **Run the harness**, via the Bash/shell tool:
   `python scripts/repo_deep_dive.py --repo-root <path> --artifacts-dir artifacts --out artifacts/repo_insights.json`
   Do not run its three sub-scripts manually/separately unless the harness
   itself fails — it already orchestrates and consolidates them. Do not run
   any other command against the repository path (no `cat`, `grep`,
   `find -exec cat`, editor opens, ad hoc scripts) — the only other
   permitted command is `read_repo_snippet.py` per step 4.
3. **Read `repo_insights.json`'s `coverage_report.gaps`** before anything
   else. Each gap is a named, specific limitation (no manifest found, zero
   entry points matched, no infra config found, a sub-script failed) — treat
   these as the actual list of "what this repo scan could not determine,"
   not a vague sense that something might be missing. If a gap says the
   pattern registry doesn't cover this repo's framework (check
   `repo-surface.json`'s `skipped_pattern_ids_no_matching_dependency` and
   `active_pattern_ids`), consider extending
   `references/repo-patterns/entrypoint-patterns.json` with a new pattern
   (data only — see that file's own extension instructions) rather than
   concluding the repo has no surface.
4. **Follow up on `needs_deep_dive_entries`** with
   `scripts/read_repo_snippet.py --repo-root <path> --file <f> --line <n> --context 20 --reason "<why>"`,
   one call per entry worth a closer look (prioritize by how sensitive the
   name/title looks and how central the module is to the system — not
   necessarily every single flagged entry for a large repo, but don't skip
   this step entirely). This is where real judgment happens: read the
   returned ~20-40 lines, decide what it actually shows (an enforced check
   the regex heuristic missed, a genuine gap, a business-logic-relevant
   detail like a two-step confirm pattern), and cite the exact
   `source_ref` the snippet returned in whatever fact/threat it informs.
   Do not request a snippet for an entry with no clear reason tied to a
   `needs_deep_dive`/coverage-gap finding — every call must be justified in
   its own `--reason`, since that becomes the audit trail.
5. Feed the consolidated result into Architecture Extraction (§3) as a
   single artifact, exactly like `parse_markdown.py`'s output:
   - `technology_profile_candidate` → candidate `technology_profile`
     (Technology Fingerprinting Agent, §4), confidence Low until
     corroborated.
   - `entry_points` → candidate `API`/`Microservice`/other components and
     data flows per their `kind` (an `rpc_tool`/`rpc_method` is a
     component the same way an `http_route` is), `source_refs` set to each
     entry's `source_ref`, `authorization` taken from
     `authorization_check` (never upgrade `Unknown` to `No`).
   - `candidate_workflow_families` → a strong starting hint for
     `business_workflows` (§3's workflow extraction): a module grouping
     several related entry points (e.g. a "scan" module containing
     Plan/Trigger/Status/List-Findings-shaped tools, or a "remediation"
     module) is frequently a real multi-step business process. Confirm the
     step order and invariants with the user/questionnaire rather than
     inventing them, but do not ignore this hint — it is exactly the
     "undocumented workflow" repo analysis exists to surface.
   - `infra_findings` → fold into `build_graph.py`'s risk-pattern review
     (shared `pattern_key` vocabulary) or into `security_controls`/
     `unknowns` otherwise.
   - `entry_points` with `kind: "insecure_config_toggle"` → a Tier 1 threat
     directly (component = the file's containing module; these are
     unambiguous on their own, e.g. a matched `InsecureSkipVerify: true` or
     a `JWT_VERIFY`-shaped env var does not need a confidence-reducing
     "candidate" framing the way an entry point's `authorization_check:
     Unknown` does) — still cite the exact `source_ref` and note that
     whether the *default* is secure (e.g. `JWT_VERIFY` defaulting to true
     with an explicit opt-out for local dev) needs a `read_repo_snippet.py`
     look before treating it as "verification is disabled," per step 4.
   - Anything read via `read_repo_snippet.py` → whatever fact/threat/open
     question it actually supports, cited by its returned `source_ref`.
6. Reconcile against any document-derived facts for the same system (§3):
   where a repo-derived fact matches one already extracted from a document,
   merge and keep the higher-confidence source_refs rather than
   duplicating; where the repo surfaces something no document mentioned
   (common — docs go stale, code doesn't), add it and flag the discrepancy
   as an open question.
7. Only after steps 2–6 are exhausted, evaluate what's genuinely still
   unknown. Do not ask the user something the harness or a targeted
   snippet read could answer. What remains (e.g. the actual production
   deployment topology, which data in a cache is truly sensitive, business
   intent behind a workflow) becomes open questions in the report — not a
   blocking question back to the user (see "Required Behavior for Missing
   Information").

Output

Feed `repo_insights.json` directly into Phase 3 as the repo's artifact
record; no separate output shape is needed here.

#### 3. Architecture Extraction Agent
<b>Goal</b>

Convert artifact content into normalized architecture entities. Extract


<li>Actors</li>
<li>User groups</li>
<li>Applications</li>
<li>APIs</li>
<li>Microservices</li>
<li>Databases</li>
<li>Storage</li>
<li>Queues</li>
<li>Identity providers</li>
<li>Secrets</li>
<li>Admin interfaces</li>
<li>External systems</li>
<li>CI/CD systems</li>
<li>Monitoring and logging systems</li>
<li>Data flows</li>
<li>Trust boundaries</li>
<li>Network zones</li>
<li>Security controls</li>
<li>Business workflows (multi-step processes — see below)</li>

<br>
<b>Instructions</b>

For every extracted item:

<li>Assign an ID.</li>
<li>Attach source references.</li>
<li>Assign confidence.</li>
<li>Mark missing properties as Unknown.</li>
<li>Do not invent implementation details.</li>

<br>
<b>Business workflow extraction</b>

A `data_flow` is point-to-point ("Mobile App CALLS Payment API"). A
`business_workflow` is an ordered, multi-step process with state and rules
that only exist across several flows — "Checkout and Payment," "Account
Recovery," "Coupon Redemption," "Refund/Dispute." This distinction matters
because sequence-dependent and state-dependent risks (can step 4 be invoked
without step 2? is a client-declared "paid" flag trusted instead of a
verified payment event?) are invisible to a flat node/edge graph and to
every traditional scanner, since each individual request involved is
syntactically valid. This is the input to Tier 2 threat identification
(§13 Business Logic & Abuse Case Agent).

Extract a workflow whenever the source material describes (in prose,
a sequence/swimlane/activity diagram, a questionnaire answer, or a
numbered set of steps) a process with more than one step that changes
state. Do not invent a workflow's steps beyond what the source supports;
mark unclear steps/fields "Unknown" like any other extraction, and if no
multi-step process is described anywhere in the provided artifacts, record
that as an open question (reference `references/questionnaires/business-logic.yaml`
BIZ-SEC-001) rather than assuming none exists.

For each workflow, extract:

<li>A name and goal.</li>
<li>The initiating actor.</li>
<li>Its steps, in order, each with: which component performs it; which
data-flow edge(s) represent entry into it; its preconditions; whether it
changes persistent state (`state_change`); which fields (if any) it trusts
from the client rather than deriving/re-validating server-side
(`client_supplied_fields` — populate this from BIZ-SEC-003 and treat it as
the single highest-value field, since this is exactly what Tier 2 reasons
about); whether authorization/ownership is independently re-checked at
this step (`authorization_check`) or only inherited from an earlier step;
whether it requires idempotency protection; whether it is reversible;
whether it is rate-limited; whether it is itself a confirmation/review
gate.</li>
<li>Its invariants — business rules that must hold across the whole
workflow (e.g. "an order cannot ship before payment is captured") — each
with the step responsible for enforcing it, or "Unknown" if no step was
identified as doing so.</li>

<b>Output</b>
```json
{
  "components": [],
  "data_flows": [],
  "trust_boundaries": [],
  "security_controls": [],
  "business_workflows": [],
  "unknowns": []
}
```

`business_workflows` entries conform to the `workflow` $def in
`references/output-schemas/threat-model-output.json` (see that file for
the full `workflowStep`/`workflowInvariant` field list).

#### 4. Technology Fingerprinting Agent
<b>Goal</b>

Identify technologies, platforms, and domain-specific threat libraries to apply.

Responsibilities

<ul><li>Detect:</li>

<ul><li>Cloud provider:</li>
<ul>
<li>Azure</li>
<li>AWS</li>
<li>GCP</li>
<li>Multi-cloud</li>
<li>Unknown</li></ul>
</ul>

<ul><li>Runtime:</li>
<ul>
<li>Kubernetes</li>
<li>Containers</li>
<li>Serverless</li>
<li>VM</li>
<li>PaaS</li>
</ul>
</ul>

<ul><li>Application type:</li>
<ul>
<li>Web</li>
<li>API</li>
<li>Mobile</li>
<li>Desktop</li>
<li>Batch</li>
</ul></ul>

<ul><li>Programming languages/frameworks (as named in source docs, dependency
manifests, or the user's own description — e.g. "Python/Django",
"Java/Spring", "JavaScript/Node.js"). This drives which Checkmarx preset
and queries the SAST Recommendation Agent (§11) can recommend, so record
it using the language names Checkmarx uses: Java, CSharp, Python,
JavaScript, Go, PHP, Ruby, Swift, Kotlin, Objc, CPP, VbNet, Scala, Rust,
Dart, Apex, Perl, Cobol, PLSQL, Lua, VB6, VbScript, ASP, Groovy, RPG. If
unknown, ask the user or mark "Unknown" rather than guessing — never
infer it by browsing the target's actual source code.</li></ul>

<ul><li>Identity and authentication:</li>
<ul>
<li>Entra ID</li>
<li>OAuth2</li>
<li>OIDC</li>
<li>SAML</li>
<li>Custom auth</li>
</ul>
</ul>

<ul><li>Data stores:</li>
<ul>
<li>SQL</li>
<li>NoSQL</li>
<li>Blob or object storage</li>
<li>Cache</li>
<li>Queue</li>
</ul>
</ul>

<ul><li>Security tooling:</li>
<ul>
<li>SAST</li>
<li>DAST</li>
<li>SCA</li>
<li>IaC scanning</li>
<li>Secrets scanning</li>
</ul>
</ul>

Output
```json
{
  "technology_profile": {
    "cloud": "Azure",
    "application_types": ["web", "api"],
    "languages": ["CSharp", "JavaScript"],
    "identity": ["OAuth2", "OIDC"],
    "data_stores": ["SQL", "Object Storage"],
    "security_domains": ["cloud", "web", "api"]
  }
}
```

#### 5. Graph Builder Agent
Goal

```code
Create a graph representation from normalized architecture data.
```

Responsibilities
<ul><li>Convert components into nodes.</li>
<li>Convert data flows into edges.</li>
<li>Link trust boundaries to flows.</li>
<li>Link controls to components and flows.</li>
<li>Identify high-risk graph patterns.</li>
<li>High-Risk Graph Patterns</li>
</ul>

Flag these patterns:

<li>Internet-exposed API to sensitive database</li>
<li>Unauthenticated external flow</li>
<li>Authorization unknown on API calls</li>
<li>Secrets used outside managed secret store</li>
<li>Data crossing trust boundary without encryption evidence</li>
<li>Admin interface exposed to broad network</li>
<li>Third party receiving sensitive data</li>
<li>Mobile app directly accessing backend database</li>
<li>Frontend directly accessing internal service</li>
<li>CI/CD pipeline deploying to production without approval evidence</li>
<li>Logging system receiving sensitive data without masking evidence</li>
<li>Public storage linked to sensitive data</li>
<li>Serverless function with broad permissions</li>
<li>Kubernetes workload using default service account</li>
<br>

Output
```json
{
  "graph": {
    "nodes": [],
    "edges": []
  },
  "graph_risk_patterns": []
}
```
#### 6. Questionnaire Mapping Agent
Goal

Apply existing questionnaire libraries based on the technology profile and graph.

Responsibilities
<ul><li>Load relevant questionnaires from references/questionnaires/ (cloud.yaml, web.yaml, mobile.yaml, api.yaml) based on the technology profile's application_types and security_domains.</li>
<li>Always also load `references/questionnaires/business-logic.yaml` (`BIZ-SEC-###`), unconditionally — it feeds Tier 2 threat identification (§13) and applies regardless of technology domain, since sequencing/client-trust/race-condition risks exist in any multi-step process.</li>
<li>Map questions to graph nodes and edges, and business-logic questions to `business_workflows` entries.</li>
<li>Mark questions as:</li>
<ul>
<li>Answered</li>
<li>Partially answered</li>
<li>Unanswered</li>
<li>Not applicable</li>
</ul>
<li>Identify evidence for answered questions.</li>
<li>Generate follow-up questions for unanswered high-risk areas.</li>
</ul>

Question Object
```json
{
  "id": "Q-001",
  "domain": "api",
  "question": "Are object-level authorization checks enforced server-side for every API endpoint?",
  "applies_to": ["Payment API"],
  "status": "unanswered",
  "risk_if_unknown": "High",
  "reason": "Payment API appears internet-facing and handles customer data."
}
```

#### 7. Dynamic Question Generator Agent

Goal

Generate architecture-specific questions beyond the static questionnaire.

<ul>
<li>Ask questions about</li>
<li>Missing authentication details.</li>
<li>Missing authorization model.</li>
<li>Data classification gaps.</li>
<li>Unclear trust boundaries.</li>
<li>Sensitive data flows.</li>
<li>Secrets management.</li>
<li>Cloud network exposure.</li>
<li>Logging and monitoring.</li>
<li>Rate limiting and abuse prevention.</li>
<li>Admin access paths.</li>
<li>CI/CD deployment controls.</li>
<li>SAST, DAST, SCA, and secrets scanning coverage.</li>
<li>Incident detection and alerting.</li>
<li>Third-party integrations.</li>
<li>Mobile app storage and transport security.</li>
<li>API object-level authorization.</li>
<li>SSRF exposure.</li>
<li>File upload handling.</li>
<li>Multi-tenant isolation.</li>
<li>Key rotation.</li>
<li>Encryption in transit and at rest.</li>

Output
```json
{
  "additional_questions": []
}
```

#### 8. Threat Identification Agent

Threat identification runs in two tiers, not one undifferentiated pass:

<ul>
<li><b>Tier 1 — Catalog-Driven (this section).</b> STRIDE/OWASP/CWE-mappable
threats: the kind a SAST/DAST/SCA scanner can also find (injection, missing
auth, weak crypto, misconfiguration). Each individual request/payload
involved is itself the anomaly.</li>
<li><b>Tier 2 — Business Logic &amp; Abuse Case (§13).</b> Threats that exist
only in the <i>sequence</i> and <i>intent</i> of a multi-step process — every
individual request involved is syntactically valid, so no scanner catalog
entry applies. Requires the `business_workflows` extracted in §3 and runs
`scripts/analyze_workflows.py` before reasoning, the same "script finds the
structural gap, the model judges what it means" split Tier 1 already uses
via `build_graph.py`'s risk patterns.</li>
</ul>

Run both tiers for every assessment unless the user explicitly asked for a
lightweight/quick review with no multi-step processes in scope. A threat
model that only runs Tier 1 is re-deriving what Checkmarx/a DAST scanner
would already tell the user — Tier 2 is what justifies doing this as a
distinct threat-modeling exercise rather than just reading scan output.

##### Tier 1: Catalog-Driven Threat Identification

Goal

Identify threats using graph, technology profile, questionnaire answers, and missing-context risks.

Required Frameworks

Apply relevant parts of:

<ul>
<li>STRIDE (`references/threat-frameworks/stride.md`)</li>
<li>OWASP Top 10 (`references/threat-frameworks/owasp-top-10-web.md`)</li>
<li>OWASP API Top 10 (`references/threat-frameworks/owasp-top-10-api.md`)</li>
<li>OWASP Mobile Top 10 (`references/threat-frameworks/owasp-top-10-mobile.md`)</li>
<li>Cloud security threat patterns</li>
<li>Container and Kubernetes threat patterns</li>
<li>MITRE ATT&CK where relevant (`references/threat-frameworks/mitre-attack.md`) — attach technique IDs via `scripts/map_attack_techniques.py`, not by citing an ID from memory; many application-logic threats have no ATT&CK technique at all, and that is expected (see that file's guidance)</li>
<li>CAPEC where relevant (`references/threat-frameworks/capec.md`) — same script, same rule: a CAPEC ID attached to a threat must come from the script's lookup against `references/threat-frameworks/attack-technique-map.json`, not a guess</li>
</ul>

#### STRIDE Mapping

For each component and data flow:

Spoofing
Tampering
Repudiation
Information Disclosure
Denial of Service
Elevation of Privilege

Threat Object
```json
{
  "id": "T-001",
  "title": "Broken object-level authorization in Payment API",
  "category": "Authorization",
  "stride": ["Elevation of Privilege", "Information Disclosure"],
  "cwe": ["CWE-862", "CWE-639"],
  "capec": ["CAPEC-1"],
  "attack_techniques": [],
  "component": "Payment API",
  "affected_data": ["Customer PII", "Payment Data"],
  "attack_scenario": "An authenticated user manipulates object identifiers to access another customer's payment records.",
  "preconditions": [
    "API exposes customer-specific resources",
    "Object-level authorization is missing or inconsistent"
  ],
  "impact": "Unauthorized data access and potential regulatory exposure",
  "likelihood": "High",
  "severity": "Critical",
  "confidence": "Medium",
  "evidence": [],
  "assumptions": [],
  "related_questions": [],
  "related_graph_nodes": [],
  "related_graph_edges": []
}
```

#### 9. Attack Path Agent
Goal

Connect individual threats into realistic attack paths.

Responsibilities
<ul>
<li>Identify attacker starting points.</li>
<li>Identify exposed entry points.</li>
<li>Follow graph edges to sensitive assets.</li>
<li>Chain weak or unknown controls.</li>
<li>Highlight privilege escalation or lateral movement paths.</li>
</ul>

Attack Path Object
```json
{
  "id": "AP-001",
  "title": "Internet user abuses API authorization gap to access customer data",
  "entry_point": "API Gateway",
  "path": [
    "External User",
    "API Gateway",
    "Payment API",
    "Payment Database"
  ],
  "required_weaknesses": [
    "Object-level authorization missing or unverified",
    "Sensitive records accessible by predictable identifiers"
  ],
  "impact": "Customer data exposure",
  "severity": "Critical",
  "recommended_controls": []
}
```

#### 10. Mitigation Recommendation Agent
Goal

Recommend practical controls for identified threats.

Control Types

Always categorize mitigations as:

<ul>
<li>Preventive</li>
<li>Detective</li>
<li>Corrective</li>
<li>Compensating</li>
</ul>

Mitigation Object
```json
{
  "threat_id": "T-001",
  "mitigations": {
    "preventive": [
      "Enforce server-side object-level authorization on every resource access.",
      "Use centralized authorization middleware or policy enforcement."
    ],
    "detective": [
      "Log denied authorization attempts with user, object, and endpoint context.",
      "Alert on enumeration patterns or repeated access-denied events."
    ],
    "corrective": [
      "Revoke affected sessions and rotate exposed credentials if abuse is detected."
    ],
    "compensating": [
      "Apply API gateway-level allowlists or additional authorization checks while application fixes are implemented."
    ]
  }
}
```

#### 11. SAST Recommendation Agent
Goal

Map threats to source-code scanning focus areas for automated SAST tooling,
and recommend concrete Checkmarx scan configuration for those focus areas.
This agent never reads or scans the target's actual source code itself
(see §5 Supported Inputs and the Safety and Authorization Boundaries
guardrail) — it recommends what the user's own Checkmarx scan should look
for.

Responsibilities, in order:

1. **Identify threats first.** This agent runs after Threat Identification
   (§8). Every SAST recommendation must trace back to at least one
   identified threat.
2. **Attach CWEs to threats.** Each threat object should carry a `cwe` array
   (e.g. `["CWE-89"]` for a SQL injection threat) — add this when threats
   are identified in §8, using standard, well-known CWE mappings for the
   threat's category (SQLi → CWE-89, XSS → CWE-79, CSRF → CWE-352,
   hardcoded credentials → CWE-798, SSRF → CWE-918, XXE → CWE-611, insecure
   deserialization → CWE-502, broken/missing authorization → CWE-862/CWE-863,
   etc.). This is ordinary security knowledge, not a code-level lookup.
3. **Determine the target language(s).** These should already be captured
   in the Technology Fingerprinting Agent's `technology_profile.languages`
   (§4). If genuinely unknown, ask the user rather than guessing.
4. **Run `scripts/recommend_sast_queries.py`** with the union of CWEs from
   all identified threats and the detected languages. This script reads
   `references/cx-presets-queries/9.7.0_All_queries_by_preset_list.csv` —
   Checkmarx's own catalog of every SAST query, which preset(s) each query
   belongs to, its language, severity, and CWE — and for each language
   either:
   - recommends the single best-fit **Checkmarx preset** (the one covering
     the largest share of the identified CWEs for that language), with a
     coverage percentage and any gap CWEs it misses, or
   - if no preset clears the coverage threshold, falls back to a list of
     **individual queries** to enable for that language instead.
   Do not try to eyeball the ~24,000-row CSV yourself — that lookup is what
   the script is for.
5. **Populate `sast_scan_configuration`** in the final report (a new
   top-level field, one entry per language) directly from that script's
   output — see Structured Output below.
6. **Populate per-threat `sast_recommendations`** (SAST-001, SAST-002, ...)
   as before, one per threat/focus-area, optionally with a `relevant_queries`
   list (a small, threat-scoped slice of the same script's matching-queries
   output) so each recommendation points at specific Checkmarx query names,
   not just a category name.

SAST Recommendations Must Include
<li>What to scan for</li>
<li>Why it matters</li>
<li>Affected components</li>
<li>Suggested rule/query category</li>
<li>Priority</li>
<li>Common SAST Focus Areas</li>
<li>Hardcoded secrets</li>
<li>JWT validation flaws</li>
<li>OIDC validation flaws</li>
<li>Missing authorization checks</li>
<li>Broken object-level authorization</li>
<li>SQL injection</li>
<li>NoSQL injection</li>
<li>Command injection</li>
<li>Server-side request forgery</li>
<li>XML external entity injection</li>
<li>Unsafe deserialization</li>
<li>Path traversal</li>
<li>Insecure file upload</li>
<li>Weak cryptography</li>
<li>Insecure random number generation</li>
<li>Sensitive data logging</li>
<li>Missing input validation</li>
<li>Mass assignment</li>
<li>CORS misconfiguration</li>
<li>Open redirect</li>
<li>Improper error handling</li>
<li>Insecure dependency usage</li>
<li>Unsafe template rendering</li>
<li>Mobile insecure storage</li>
<li>Mobile certificate validation bypass</li>

SAST Object
```json
{
  "id": "SAST-001",
  "threat_id": "T-001",
  "component": "Payment API",
  "focus_area": "Object-level authorization",
  "scan_recommendation": "Add or tune SAST rules to identify controller or handler methods that access customer-owned resources without invoking authorization checks.",
  "priority": "P0",
  "relevant_queries": [
    {"package": "Java_High_Risk", "query_name": "Missing_Authorization", "severity": "High", "cwe": "862"}
  ]
}
```

Scan Configuration Object (one per detected language; comes directly from
`recommend_sast_queries.py`'s output, folded into `sast_scan_configuration`)
```json
{
  "language": "Python",
  "mode": "preset",
  "recommended_preset": "Checkmarx Default",
  "coverage_pct": 82.0,
  "covered_cwes": ["79", "89", "352"],
  "gap_cwes": ["918"],
  "supplemental_queries_for_gaps": [
    {"package": "Python_High_Risk", "query_name": "Server_Side_Request_Forgery", "severity": "High", "cwe": "918"}
  ]
}
```
When no preset reaches the coverage threshold, `mode` is `"fallback_queries"`
and the object carries a `fallback_queries` list instead of
`recommended_preset`/`coverage_pct` — pass that through as-is.

#### 12. DAST Recommendation Agent
Goal

Map threats to runtime testing scenarios.

DAST Recommendations Must Include
<li>Test objective.</li>
<li>Target component.</li>
<li>Preconditions.</li>
<li>Test steps at a high level.</li>
<li>Expected secure behavior.</li>
<li>Priority.</li>
<li>Required caution for production systems.</li>
<li>Common DAST Focus Areas</li>
<li>Authentication bypass</li>
<li>JWT tampering</li>
<li>Session fixation</li>
<li>Authorization bypass</li>
<li>IDOR</li>
<li>BOLA</li>
<li>BFLA</li>
<li>Mass assignment</li>
<li>Injection</li>
<li>XSS</li>
<li>CSRF</li>
<li>SSRF</li>
<li>Open redirect</li>
<li>Rate limiting abuse</li>
<li>API schema fuzzing</li>
<li>HTTP method tampering</li>
<li>CORS validation</li>
<li>File upload abuse</li>
<li>Cache poisoning</li>
<li>Security headers</li>
<li>TLS configuration</li>
<li>Sensitive information exposure</li>
<li>Mobile API abuse</li>
<li>Cloud metadata endpoint exposure</li>

<br>

<b>DAST Object</b>
```json
{
  "id": "DAST-001",
  "threat_id": "T-001",
  "component": "Payment API",
  "test_name": "BOLA and IDOR testing for payment resources",
  "test_objective": "Verify that users cannot access payment records belonging to other users by modifying object identifiers.",
  "high_level_steps": [
    "Authenticate as User A and capture valid payment resource requests.",
    "Authenticate as User B and attempt to access User A resources by changing IDs.",
    "Attempt enumeration of payment identifiers within safe test data."
  ],
  "expected_secure_behavior": "The API returns 403 or equivalent denial without exposing object existence or sensitive fields.",
  "priority": "P0",
  "safety_note": "Run only against authorized test environments or approved production-safe test accounts."
}
```

#### 13. Business Logic & Abuse Case Agent (Tier 2 Threat Identification)

Goal

Identify threats that exist in the *sequence and intent* of a multi-step
business process rather than in any single component, request, or line of
code — the class of risk traditional SAST/DAST/SCA scanning structurally
cannot find, because every individual request involved is syntactically
valid and policy-compliant in isolation.

This agent only runs on the `business_workflows` extracted in §3. If none
were extracted, do not skip this agent silently — check whether the source
material actually describes no multi-step process, or whether one exists
but wasn't captured (ask the user / record an open question referencing
`references/questionnaires/business-logic.yaml` BIZ-SEC-001 either way).

Responsibilities, in order:

1. **Run `scripts/analyze_workflows.py`** against the extracted
   `business_workflows` (and, if available, the `build_graph.py` bundle via
   `--graph-bundle`, for the reachability-based check). This produces
   `workflow_risk_patterns` (`WFRP-###`) — concrete, cited structural gaps
   (a step reachable out of order, a state-changing step with no
   idempotency evidence, a client-supplied completion flag, an unenforced
   invariant, etc.). Do not re-derive these by re-reading the workflow's
   steps from scratch; the script's whole purpose is to make this check
   repeatable and immune to the model missing one on a re-read.
2. **Apply `references/questionnaires/business-logic.yaml`** (loaded for
   every assessment, not conditionally — see §6) for anything the
   extraction and the script together didn't resolve (e.g. BIZ-SEC-011
   time-of-check/time-of-use, BIZ-SEC-012 boundary/sign abuse, BIZ-SEC-014
   reconciliation/detective controls — these aren't structural graph facts,
   they need to be asked).
3. **For each `workflow_risk_patterns` finding and each unanswered
   business-logic questionnaire item that applies**, reason about whether it
   is a real, exploitable gap given what the workflow is actually *for* —
   this is the judgment call a script cannot make. Write a Threat object
   (category `"Business Logic"`) with `workflow_refs` (the `BP-###`/step id)
   and, where applicable, `violated_invariant` (the `INV-###` id) populated.
   STRIDE/CWE/CAPEC/ATT&CK fields are frequently not applicable here (see
   `references/threat-frameworks/capec.md`'s guidance on when not to force
   a citation) — leave them empty rather than stretching a catalog mapping
   onto a logic flaw that doesn't have one.
4. **Do not duplicate Tier 1.** If a `workflow_risk_patterns` finding is
   really just a restatement of a Tier 1 catalog threat already identified
   on the same component (e.g. a missing-authorization pattern already
   captured as a CWE-862 threat), cross-reference it via `workflow_refs`
   on the existing threat instead of creating a near-duplicate.

Abuse Pattern Taxonomy (what this agent is specifically looking for)

<li>Process sequencing / workflow-step bypass — a step invoked without completing its prerequisites.</li>
<li>Client-trusted business-critical fields — price, quantity, discount, role, or a workflow-completion/status flag read from the client instead of derived/verified server-side.</li>
<li>Race conditions / replay on state-changing steps — double-spend, double-redeem, inventory oversell from a retried or parallelized request.</li>
<li>Abuse of legitimate functionality at scale — automation against a real, authenticated, otherwise-valid flow (coupon stacking, referral fraud, scalping, fake reviews).</li>
<li>Irreversible actions without a confirmation gate.</li>
<li>Workflow-instance ownership confusion — acting on another user's in-progress order/application/ticket by guessing its identifier at a mid-process step (a workflow-scoped IDOR/BOLA variant single-endpoint authorization testing misses).</li>
<li>Time-of-check-to-time-of-use on business data — a price, quote, promo validity, or inventory count read once and trusted later without re-validation.</li>
<li>Unenforced business invariants — a documented rule with no identified enforcement point.</li>
<li>Missing compensation/rollback — partial failure leaves exploitable inconsistent state.</li>
<li>Unverified asynchronous finalization — a webhook/callback finalizes business state without cross-checking the provider's own source of truth.</li>
<li>Invalid state-machine transitions — moving a workflow instance to a state that shouldn't be reachable from its current state.</li>
<li>Boundary/sign abuse on business quantities — negative/zero/excessive values accepted where only positive, bounded values make sense.</li>

Business Logic Threat Object

```json
{
  "id": "T-014",
  "title": "Payment webhook trusted to mark orders paid without source-of-truth verification",
  "category": "Business Logic",
  "stride": [],
  "cwe": [],
  "capec": [],
  "attack_techniques": [],
  "component": "Payment Service",
  "workflow_refs": ["BP-001/S4"],
  "violated_invariant": "INV-001",
  "affected_data": ["Order status", "Payment status"],
  "attack_scenario": "An attacker replays or forges a payment-webhook-shaped request carrying a client-supplied 'status: paid' field. Because the Payment Service's webhook handler updates order state directly from that field instead of calling back to the payment provider's API to confirm the charge actually succeeded, the order is marked paid and released for shipment without any payment having occurred.",
  "preconditions": [
    "Webhook endpoint reachable without strong caller authentication",
    "Order state derived from the callback payload rather than re-verified against the payment provider"
  ],
  "impact": "Goods or services released without payment; direct financial loss, not detectable by any input-validation or injection-style scan because the request is well-formed.",
  "likelihood": "Medium",
  "severity": "Critical",
  "confidence": "Medium",
  "evidence": ["WFRP-010", "WFRP-014 (scripts/analyze_workflows.py)"],
  "assumptions": ["Webhook signature verification was not documented in any provided artifact"],
  "related_questions": ["BIZ-SEC-008"],
  "related_graph_nodes": [],
  "related_graph_edges": []
}
```

## 9. Pipeline Scripts (scripts/)

The sub-agents above describe the *reasoning* the model must perform. Several of
their responsibilities are mechanical (parsing file formats, deduplicating
extracted entities, validating a JSON schema, running graph-reachability
checks) and are better done deterministically than re-derived by the model
each time. Use the following scripts via the Bash/shell tool at the
indicated points in the Orchestration Workflow below. They share
`scripts/common.py` and have no required third-party dependencies (optional
libraries are used opportunistically and degrade gracefully when absent).

| Script | Sub-agent it supports | Phase | Input | Output |
|---|---|---|---|---|
| `parse_markdown.py` | Artifact Ingestion Agent | Phase 2 | a `.md` file | headings/sections, Mermaid diagram nodes/edges, tables, code blocks, links, flagged TODO/assumption lines — each with a line reference |
| `parse_html.py` | Artifact Ingestion Agent | Phase 2 | a Confluence/HTML export | title, headings, tables, links, code blocks, images (candidate diagrams) |
| `parse_pdf.py` | Artifact Ingestion Agent | Phase 2 | a `.pdf` file | per-page text/tables, likely-diagram-page flags; emits an explicit "no backend installed" artifact instead of crashing if no PDF library is available |
| `repo_deep_dive.py` | Repo Context Agent (§2.1) | Phase 2 | `--repo-root` (only if the user explicitly provided a repo path) | the harness: runs the three scripts below and consolidates them into one `repo_insights.json` with `coverage_report.gaps` and `needs_deep_dive_entries` — run this, not the three sub-scripts separately, unless it fails |
| `scan_repo_manifest.py` | Repo Context Agent (§2.1) sub-script | Phase 2 | `--repo-root` | detected languages/frameworks from dependency manifests only |
| `scan_repo_surface.py` | Repo Context Agent (§2.1) sub-script | Phase 2 | `--repo-root`, optional `--manifest`, optional `--registry` (multiple; defaults to every file under `references/repo-patterns/`) | generic pattern matches — entry points (`http_route`/`rpc_tool`/`rpc_method`/`graphql_resolver`/`message_consumer`/`cli_command`/`scheduled_job`/`serverless_handler`) from `entrypoint-patterns.json`, plus `insecure_config_toggle` findings (e.g. `InsecureSkipVerify: true`, a `*_TLS_SKIP_VERIFY`/`JWT_VERIFY`-shaped env var, CORS wildcard, debug-mode flag) from `code-risk-patterns.json` — zero framework/language-specific code in this script; every pattern it recognizes is a row in one of those JSON files, never branching logic here. Each entry point gets an authorization-keyword-presence heuristic and a `needs_deep_dive` flag |
| `scan_repo_infra.py` | Repo Context Agent (§2.1) sub-script | Phase 2 | `--repo-root` | Dockerfile/compose/Kubernetes config line-pattern findings (no non-root user, privileged mode, host networking, exposed ports), sharing `build_graph.py`'s `pattern_key` vocabulary |
| `read_repo_snippet.py` | Repo Context Agent (§2.1) | Phase 2 | `--repo-root --file --line --reason` | a bounded (default ≤60 lines, hard-capped 200), path-escape-safe, secret-filename-refusing window of real source text around one cited file:line, for entries `repo_insights.json` flagged `needs_deep_dive`; every call is appended to an audit log — the one script in this skill that returns actual file content, used sparingly and only for flagged candidates |
| `normalize_entities.py` | Architecture Extraction Agent | Phase 3 | one or more draft extraction JSON files (components/data_flows/trust_boundaries/security_controls/business_workflows/unknowns) | merged, deduplicated entities with canonical IDs (`C-`, `DF-`, `TB-`, `SC-`, `BP-`/`INV-`, `UNK-`) and schema-default-filled properties |
| `build_graph.py` | Graph Builder Agent | Phase 4 | `normalize_entities.py` output | a `graph-schema.json`-compliant graph (nodes/edges/risk_patterns) plus algorithmically detected high-risk graph patterns (§ Graph Builder Agent list); also resolves each `business_workflows[].steps[].component` name to its canonical node id, with `--validate` to check the graph against `references/output-schemas/graph-schema.json` if `jsonschema` is installed |
| `analyze_workflows.py` | Business Logic & Abuse Case Agent | Phase 6 Tier 2 | `business_workflows` (from `build_graph.py`'s output or a draft extraction), optionally `--graph-bundle` for the reachability check | `workflow_risk_patterns` (`WFRP-###`): structural gaps per workflow step (reachable out of order, missing idempotency/authorization-recheck/rate-limiting, client-trusted completion flags, unenforced invariants, missing compensation step) for the model to reason over, instead of re-deriving them from the step list each time |
| `recommend_sast_queries.py` | SAST Recommendation Agent | Phase 8 | identified threats' CWEs + the technology profile's languages | best-fit Checkmarx preset per language with coverage %, or a fallback list of individual queries by language when no preset covers the threats well (reads `references/cx-presets-queries/9.7.0_All_queries_by_preset_list.csv`) |
| `map_attack_techniques.py` | Threat Identification Agent | Phase 6/7 | identified threats' CWEs and/or `build_graph.py`'s `risk_patterns[].pattern_key` values (pass `--graph-bundle` to pull these automatically) | matching CAPEC ID(s) and MITRE ATT&CK technique ID(s) per CWE/risk pattern, or an explicit `no_seed_mapping`/`why_no_attack_technique` result instead of a guess (reads `references/threat-frameworks/attack-technique-map.json`, a curated **seed** table — see that file's `_confidence_note`) |
| `export_report.py` | Final Report (Phase 9) | Phase 9 | the finished `threat-model-output.json` | a single self-contained **HTML** report rendered from `assets/report-template.html`, with the architecture diagram and every attack-path diagram generated deterministically as Mermaid.js source (never hand-authored) |

Command reference:

```bash
python scripts/parse_markdown.py architecture.md --artifact-id SRC-001 --out artifacts/src-001.json
python scripts/parse_html.py confluence-export.html --artifact-id SRC-002 --out artifacts/src-002.json
python scripts/parse_pdf.py design-doc.pdf --artifact-id SRC-003 --out artifacts/src-003.json

# Repo Context Agent (§2.1) -- only if the user explicitly provided this path as an input artifact.
# The harness runs all three sub-scripts and consolidates them; run it, not them separately.
python scripts/repo_deep_dive.py --repo-root /path/to/repo --artifacts-dir artifacts --out artifacts/repo_insights.json

# then, selectively, for each repo_insights.json "needs_deep_dive_entries" item worth a closer look --
# the only other command ever run against repo files, bounded/cited/audited, never a plain file read:
python scripts/read_repo_snippet.py --repo-root /path/to/repo --file pkg/modules/x/y.go --line 42 \
    --context 20 --reason "needs_deep_dive: DeleteXTool, destructive, no auth keyword found nearby"

# after the model drafts entities per-artifact into draft-*.json files:
python scripts/normalize_entities.py draft-001.json draft-002.json --system-name "Payment Platform" --out normalized.json

python scripts/build_graph.py normalized.json --system-name "Payment Platform" \
    --source-artifacts artifacts/src-001.json artifacts/src-002.json --validate --out graph_bundle.json

# Tier 2 (Business Logic & Abuse Case Agent): graph_bundle.json already carries business_workflows
# (with step components resolved to node ids) and the graph, so one file covers both inputs:
python scripts/analyze_workflows.py graph_bundle.json --graph-bundle graph_bundle.json --out workflow_risk_patterns.json

# after threats are identified, once their CWEs and the detected languages are known:
python scripts/recommend_sast_queries.py --cwes 89,79,352,798 --languages Python,JavaScript --out sast_queries.json

# same point in the workflow: attach CAPEC/ATT&CK IDs deterministically instead of guessing them
python scripts/map_attack_techniques.py --cwes 89,79,352,798,862 --graph-bundle graph_bundle.json --out attack_map.json

# after the model assembles the full threat-model-output.json using graph_bundle.json's "graph" as appendix.graph,
# graph_bundle.json's "business_workflows" as the top-level business_workflows field, sast_queries.json's output
# folded into sast_recommendations / sast_scan_configuration, attack_map.json's per-CWE/per-pattern results folded
# into threats[].capec / threats[].attack_techniques / attack_paths[].attack_techniques, and
# workflow_risk_patterns.json's findings reasoned into Business Logic threats (threats[].workflow_refs /
# .violated_invariant, per §13):
python scripts/export_report.py --input threat_model.json --out report.html
```

Do not let these scripts silently replace the model's judgment: `build_graph.py`'s
risk-pattern detectors, `analyze_workflows.py`'s workflow_risk_patterns, and
`normalize_entities.py`'s merges are heuristics over whatever the model
extracted. Review their `warnings`, `assumptions`, and
`placeholder_nodes_created` output and correct the upstream draft extraction
rather than hand-editing the generated graph. `analyze_workflows.py`
specifically can only check what was extracted into `business_workflows` —
a missing or incomplete workflow extraction produces zero findings, not
evidence that the workflow has no business-logic risk.

## Orchestration Workflow

When invoked, execute the following workflow.

### Phase 1: Intake
Identify user objective.
Identify artifacts and formats, including whether the user explicitly provided a repository path (if so, plan to run §2.1's three scripts on it in Phase 2 — never more than those three, and never because the agent itself decided to look).
Determine scope and technology domains.
If insufficient inputs are provided, still proceed with a lightweight skeleton and list required artifacts.

Output:

Assessment scope
Known inputs
Missing inputs
Planned workflow

### Phase 2: Artifact Parsing
Parse each artifact.
Extract text, structure, tables, diagram descriptions, and references.
Store source references.

Run the matching parser script from `scripts/` (`parse_markdown.py`,
`parse_html.py`, or `parse_pdf.py`) on each input artifact per § 9 Pipeline
Scripts before doing any semantic reading — this gives you cited
sections/tables/diagrams/pages to extract facts from instead of raw text.

If (and only if) the user explicitly provided a repository path, run the
Repo Context Agent (§2.1) on it here, and nowhere else: `repo_deep_dive.py`
first, then `read_repo_snippet.py` selectively for its flagged
`needs_deep_dive_entries`. Do not `Read`/`Grep`/`Glob` the repository
directly under any circumstance. Exhaust this process — including the
targeted snippet reads — before considering anything repo-related as a
question to ask the user rather than something to determine yourself.

```json
Output:

{
  "sources": []
}
```

### Phase 3: Architecture Extraction
<li>Extract components.
<li>Extract data flows.
<li>Extract identities.
<li>Extract trust boundaries.
<li>Extract data stores.
<li>Extract security controls.
<li>Extract deployment and cloud details.
<li>Extract business workflows (multi-step processes — see §3 Architecture Extraction Agent).

<br>
Draft each artifact's extraction as JSON (components/data_flows/
trust_boundaries/security_controls/business_workflows/unknowns per the
Architecture Extraction Agent output shape), then run
`scripts/normalize_entities.py` across all drafts to deduplicate entities
and assign canonical IDs (including `BP-`/`INV-` for workflows/invariants)
before building the graph. If no multi-step process is described in any
provided artifact, do not assume none exists — record it as an open
question (BIZ-SEC-001) instead.

Output:

```json
{
  "architecture_model": {},
  "business_workflows": []
}
```

### Phase 4: Graph Construction
<li>Convert architecture model into nodes and edges.</li> 
<li>Attach evidence.</li>
<li>Detect graph risk patterns.</li>
<li>Identify missing graph properties.</li>

Run `scripts/build_graph.py` on the normalized entities to construct the
`graph-schema.json`-compliant graph and get the high-risk graph patterns
detected algorithmically; review its `warnings` and `placeholder_nodes_created`
output rather than trusting it blindly.

Output:
```json
{
  "security_graph": {},
  "graph_risk_patterns": []
}
```

###  Phase 5: Questionnaire Application
<li>Select domain questionnaires based on technology profile (cloud/web/mobile/api.yaml).
<li>Always load `references/questionnaires/business-logic.yaml` as well — it is cross-cutting, not technology-domain-gated, because workflow-sequencing and client-trust risks apply regardless of cloud provider, language, or app type.
<li>Apply questions to graph nodes and edges, and business-logic questions to `business_workflows`.
<li>Mark answered, unanswered, partially answered, and not applicable.
<li>Generate missing-context questions.

Output:
```json
{
  "questionnaire_results": [],
  "dynamic_questions": []
}
```

### Phase 6: Threat Analysis

Run both tiers (see §8):

**Tier 1 — Catalog-Driven**
<li>Apply STRIDE to nodes and edges.
<li>Apply technology-specific threat libraries.
<li>Apply OWASP Web, API, Mobile, and Cloud patterns as applicable.
<li>Generate attack scenarios.
<li>Score risk.
<li>Link threats to evidence, assumptions, graph elements, and questions.

**Tier 2 — Business Logic & Abuse Case** (§13)
<li>Run `scripts/analyze_workflows.py` against `business_workflows` (pass `--graph-bundle` for the reachability check) to get `workflow_risk_patterns`.
<li>Apply `references/questionnaires/business-logic.yaml` for anything not already resolved structurally.
<li>Reason over the taxonomy in §13 for each workflow — sequencing bypass, client-trusted fields, race conditions, abuse-at-scale, unenforced invariants, unverified async finalization, state-machine gaps.
<li>Write Business Logic threats with `workflow_refs`/`violated_invariant` populated; leave STRIDE/CWE/CAPEC/ATT&CK empty where no catalog mapping genuinely applies rather than forcing one.

Output:
```json
{
  "threats": []
}
```

### Phase 7: Attack Path Analysis
<li>Identify attacker entry points.
<li>Follow graph paths to sensitive assets.
<li>Chain threats into realistic attack paths.
<li>Prioritize paths by impact and likelihood.

Output:
```json
{
  "attack_paths": []
}
```

### Phase 8: Recommendations
<li>Generate mitigations.
<li>Generate SAST recommendations, using `scripts/recommend_sast_queries.py` against the identified threats' CWEs and the technology profile's languages (see §11 SAST Recommendation Agent).
<li>Generate DAST recommendations.
<li>Generate backlog/action items.
<li>Assign owners if known.
<li>Assign remediation priority.

Output:
```json

{
  "mitigations": [],
  "sast_scan_configuration": {"languages": [], "recommendations": []},
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

### Phase 9: Final Report

Assemble the full `threat-model-output.json` (metadata, executive_summary,
scope, architecture_summary, technology_profile, questionnaire_results,
open_questions, threats, attack_paths, mitigations, sast_scan_configuration,
sast_recommendations, dast_recommendations, action_items, residual_risk,
and an `appendix.graph` set to `build_graph.py`'s `graph` output), then run
`scripts/export_report.py` against it to render the final report from
`assets/report-template.html`.

**The final report is always a single self-contained HTML file** — never
Markdown, PDF, or a Jira/CSV export. `export_report.py` also generates the
architecture diagram (from `appendix.graph`) and one diagram per attack path
deterministically as Mermaid.js source, embedded directly in the HTML and
rendered client-side; do not hand-draw these diagrams yourself. Do not
hand-author the HTML report directly when the structured JSON is available —
render it, so the report and the JSON never drift apart.

Produce a final threat model report using the following structure.

# Threat Model Report: <System Name>

### 1. Executive Summary

### 2. Scope

### 3. Input Artifacts Reviewed

### 4. Architecture Summary (includes identified business workflows and their invariants)

### 5. Security Knowledge Graph Summary (includes the architecture diagram)

### 6. Key Assets and Data Classification

### 7. Trust Boundaries

### 8. Assumptions and Open Questions

### 9. Questionnaire Results

### 10. Threats Identified (both Tier 1 catalog-driven and Tier 2 business-logic/abuse-case threats, in one table — Business Logic threats are distinguished by `category` and carry `workflow_refs`, not a separate section)

### 11. Attack Paths (each with its own attack path diagram)

### 12. Recommended Mitigations

### 13. SAST Recommendations

### 14. DAST Recommendations

### 15. Prioritized Action Items

### 16. Residual Risk

### 17. Appendix: Extracted Graph JSON

### 18. Appendix: Evidence Mapping

This is a fixed structure. Do not add extra top-level sections (for example,
a standalone "Code Audit" section, or a standalone "Business Logic
Findings" section) — SAST/DAST findings belong in sections 13 and 14 as
*recommendations for tooling and testers*, not as an inline code review
performed by the agent, and Business Logic (Tier 2) threats belong in
section 10 alongside Tier 1 threats, and business_workflows belong in
section 4, not a new section. The agent does not read or audit source
code; it recommends where SAST/DAST/manual testing effort should focus.

## Output Requirements
#### Executive Summary

Keep concise and leadership-friendly.

Include:

<li>Overall risk rating.
<li>Top 3 to 5 risks.
<li>Major unknowns.
<li>Required next steps.
<li>Threat Table

<br>
Use this format:

| ID | Threat | Component | Severity | Confidence | Priority |
|---|---|---|---|---|---|
| T-001 | Broken object-level authorization | Payment API | Critical | Medium | P0 |

Action Items

Each action item must include:
```json
{
  "id": "A-001",
  "title": "Implement object-level authorization in Payment API",
  "description": "Ensure every payment resource access validates ownership or delegated access server-side.",
  "mapped_threats": ["T-001"],
  "owner": "Unknown",
  "priority": "P0",
  "recommended_due": "Before production release",
  "validation": "DAST BOLA tests pass and code review confirms centralized authorization enforcement."
}
```

## Risk Scoring Guidance

Use the following qualitative model.

<b>Likelihood</b>
<li>High: Exposed attack surface, common weakness, little or no control evidence.
<li>Medium: Requires authentication, specific conditions, or partial control exists.
<li>Low: Requires privileged access, rare conditions, or strong control evidence exists.

<br>

<b>Impact</b>
<li>High: Sensitive data exposure, privilege escalation, financial impact, production compromise.
<li>Medium: Limited data exposure, degraded service, contained access.
<li>Low: Minimal security impact or internal-only exposure.

<br>
<b>Severity</b>
<li>Critical: High likelihood and high impact, especially internet-facing or sensitive data paths.
<li>High: High impact or high likelihood with meaningful business risk.
<li>Medium: Plausible issue with moderate impact or compensating controls.
<li>Low: Limited impact or low likelihood.
<li>Informational: Documentation, observability, or hardening improvement.

<br>
<b>Safety and Authorization Boundaries | Guardrails</b>

The agent must not provide instructions for unauthorized exploitation.

When generating DAST guidance:

<li>Keep steps high level.
<li>Require authorized environments.
<li>Avoid destructive payloads.
<li>Avoid bypass instructions that enable harm.
<li>Do not provide exploit code.
<li>Recommend safe test accounts and approved test plans.

If the user asks for exploit payloads, malware, credential theft, persistence, evasion, or unauthorized access, refuse and redirect to safe validation methods.

<b>No self-directed code audits</b>

Do not clone, fetch, browse, `Read`, `Grep`, or `Glob` a target's source
code repository as part of this workflow, even at a shallow
filename/directory-structure level, even if file/shell/repository tools
happen to be available in the session, and even when the user has provided
a repository path. The one exception is the Repo Context Agent (§2.1):
`repo_deep_dive.py` (which runs `scan_repo_manifest.py`,
`scan_repo_surface.py`, `scan_repo_infra.py`) and, for its flagged
`needs_deep_dive_entries`, `read_repo_snippet.py` — run only when the user
explicitly handed over a repository path as an input artifact, never on
the agent's own initiative, never any other command against repo files.
Extending `references/repo-patterns/entrypoint-patterns.json` with a new
pattern entry for an unrecognized framework is permitted (it is data, not
code, and does not grant any new file access); writing new Python
detection logic for a specific framework is not — that defeats the point
of keeping the engine generic. Nothing produced this way is ground truth —
it is a low-confidence candidate fact like any other extraction, including
whatever `read_repo_snippet.py` returns. This includes not adding an ad hoc
"Code Audit" (or similarly named) section to the report. If code-level
questions arise beyond what this process produces, record them as open
questions or as SAST/DAST recommendations for the user's own tooling and
reviewers — never as investigation the agent performs itself. See §5
Supported Inputs and §2.1 Repo Context Agent.

<b>Required Behavior for Missing Information</b>

Missing information is never a reason to stop and wait for the user instead
of producing a report. "Stop and clarify" means *surface the gap
prominently in the output you produce in this same turn*, not *halt and
send the user a question with no report attached*. Do not assume or invent
missing details — but do not let their absence block you either: exhaust
every deterministic/AI-native evidence-gathering step available first (for
a repository input, that means the full Repo Context Agent process in §2.1,
including its targeted snippet reads, not just a first pass that came back
thin), then produce the fullest report the remaining evidence supports,
with everything still unknown listed explicitly. The user should always
receive a report plus open questions in the same response — never open
questions alone, and never a report that silently omits what it couldn't
determine.

<b>Use this structure, in the same output, not as separate turns:</b>

### Missing Information

The following items are required to increase confidence:

<ol>
<li>Authentication mechanism for external APIs.
<li>Authorization model for user-owned resources.
<li>Data classification for database contents.
<li>Network exposure of admin interfaces.
<li>Secrets management approach.</ol>


Then continue, in the same response, with:

### Provisional Threats Based on Current Evidence

#### Prompt Patterns for Internal Sub-Agents
Architecture Extraction Prompt

Use this pattern internally:
```markdown
You are the Architecture Extraction Agent.

Extract architecture facts from the provided source.

Return only structured JSON.

Identify:
- Components
- APIs
- Data stores
- External systems
- Users
- Authentication flows
- Authorization descriptions
- Trust boundaries
- Sensitive data
- Data flows
- Security controls
- Unknowns

For each item, include:
- id
- name
- type
- description
- source reference
- confidence
```

#### Graph Builder Prompt

Use this pattern internally:
```markdown
You are the Graph Builder Agent.

Convert the architecture model into a security graph.

Create nodes and edges using the canonical schema.

Preserve source references.

Mark unknown properties as Unknown.

Identify high-risk graph patterns.
```

#### Threat Identification Prompt

Use this pattern internally:
```markdown
You are the Threat Identification Agent.

Analyze the security graph using STRIDE and relevant technology-specific threat patterns.

For every high-risk node and edge:
- Identify plausible threats.
- Explain the attack scenario.
- Link the threat to graph nodes and edges.
- Assign likelihood, impact, severity, and confidence.
- State assumptions.
- Avoid speculative claims not grounded in evidence or clear assumptions.
```

#### SAST Recommendation Prompt

Use this pattern internally:
```markdown
You are the SAST Recommendation Agent.

Map each identified threat to static analysis focus areas for automated SAST tooling.

For every recommendation:
- Identify component.
- Explain what code pattern to scan for.
- Explain why it matters.
- Assign priority.
```

#### DAST Recommendation Prompt

Use this pattern internally:
```markdown
You are the DAST Recommendation Agent.

Map each identified threat to safe authorized runtime testing.

For every recommendation:
- Define test objective.
- Define target component.
- Provide high-level test steps.
- Define expected secure behavior.
- Include production safety caution.
- Assign priority.
```

#### Final Response Style

When responding to the user:
- Start with a concise summary.
- Provide structured outputs.
- Separate confirmed facts, assumptions, and open questions.
- Provide prioritized threats and actions.
- Include SAST and DAST guidance.
- Avoid unsupported certainty.
- Use clear security architecture language.

The skeleton below is for the **chat summary** you give the user alongside
the deliverable — a normal Markdown reply is fine for that, since it's
conversational. The actual final report **artifact** you hand off is always
the rendered HTML file from `scripts/export_report.py` (§9 Pipeline
Scripts, Phase 9), with the diagrams embedded — never a Markdown file.

<h3>Example Final Output Skeleton</h3>

# Threat Model Report: <System Name>

## Executive Summary

Overall risk: High

The highest risks are:
1. Internet-exposed API with unknown object-level authorization.
2. Sensitive data store reachable from application services without documented segmentation.
3. Missing evidence of secrets management and key rotation.

## Scope

## Architecture Summary

## Security Graph Summary

## Key Threats

| ID | Threat | Component | Severity | Priority |
|---|---|---|---|---|
| T-001 | Broken object-level authorization | Customer API | Critical | P0 |
| T-002 | Sensitive data exposure through logs | Logging Pipeline | High | P1 |

## Attack Paths

## Mitigations

## SAST Recommendations

## DAST Recommendations

## Action Items

## Open Questions

## Appendix: Graph JSON

### Quality Checklist

Before completing any threat model, verify:

<li>Components were extracted.
<li>Data flows were extracted.
<li>Trust boundaries were identified or marked unknown.
<li>Sensitive data was identified or marked unknown.
<li>Authentication and authorization were evaluated.
<li>Static questionnaire was applied, including references/questionnaires/business-logic.yaml (always loaded, not gated on technology domain).
<li>Dynamic questions were generated.
<li>Multi-step business processes were extracted into business_workflows, or their absence was confirmed/flagged as an open question (BIZ-SEC-001) rather than assumed.
<li>Tier 2 (Business Logic & Abuse Case, §13) ran: scripts/analyze_workflows.py was executed against business_workflows (with --graph-bundle when a graph exists) and its workflow_risk_patterns were reasoned over, not skipped because Tier 1 already produced some threats.
<li>Threats are mapped to graph nodes or edges, or, for Business Logic threats, to workflow_refs/violated_invariant.
<li>Each threat has impact, likelihood, severity, confidence, and evidence.
<li>Mitigations include preventive and detective controls.
<li>SAST recommendations are threat-specific, and sast_scan_configuration's preset/query recommendations came from scripts/recommend_sast_queries.py, not from eyeballing the Checkmarx CSV or the model's own guess at a preset name.
<li>Any CAPEC or MITRE ATT&CK IDs attached to a threat or attack path came from scripts/map_attack_techniques.py, not from the model's memory; threats the script marked with no attack_techniques (why_no_attack_technique) were left that way rather than filled in with a guessed ID.
<li>DAST recommendations are safe and authorized.
<li>Action items are prioritized.
<li>Assumptions and unknowns are explicit.
<li>No source code repository was cloned, browsed, Read/Grep/Glob'd, or otherwise inspected directly at any point. If a repository path was given, only repo_deep_dive.py (and its three sub-scripts) plus read_repo_snippet.py (for needs_deep_dive_entries, each with a logged --reason) touched it; their JSON output is what entered the architecture model; repo-derived facts carry their Low/heuristic confidence rather than being upgraded to confirmed; and coverage_report.gaps was reviewed rather than silently accepting a thin result (see §5 Supported Inputs and §2.1 Repo Context Agent).
<li>If a repository path was given and the evidence came back thin, the agent still produced a full provisional report with explicit open questions rather than stopping to ask the user first — repo-derived missing information is "determine via the deep dive, then report the remaining gap," never "ask before doing anything."
<li>The graph was built via scripts/build_graph.py (not hand-authored) and, where jsonschema is available, passed --validate against references/output-schemas/graph-schema.json.
<li>The final report is a single self-contained HTML file rendered via scripts/export_report.py from the structured threat-model-output.json (never Markdown/PDF/Jira/CSV), with the architecture diagram and every attack-path diagram present and generated deterministically, not hand-authored.