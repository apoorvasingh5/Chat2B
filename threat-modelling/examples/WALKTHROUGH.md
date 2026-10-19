# Walkthrough: testing the pipeline scripts end-to-end

This machine has no Python interpreter installed, so none of the commands
below have been executed here. This file exists so you (with Python 3.10+
on your own machine) can run the full pipeline once and sanity-check that
`scripts/` behaves as documented. Everything here was worked out by hand
against the sample fixtures in this folder, so the expected results are
specific and checkable, not vague.

Run all commands from the skill's root folder (the one containing
`SKILL.md`, `scripts/`, `assets/`, `examples/`).

## 0. Optional dependencies

Everything works with zero extra installs (parse_pdf.py will just report
"no PDF backend available" if you try it without one). For the fullest
experience:

```bash
pip install beautifulsoup4 pdfplumber jsonschema
```

## 1. Parse the sample architecture document

```bash
python scripts/parse_markdown.py examples/sample-architecture.md --artifact-id SRC-001 --out /tmp/src-001.json
```

Expected: `stats.section_count` = 6 (Overview, Data Flow, Components, Third-Party
Integrations, Known Gaps, plus the H1 title section), `diagrams_detected`:
true with one Mermaid diagram containing 6 nodes (`Mobile`, `Gateway`,
`AccountAPI`, `DB`, `Notify`, `Admin`) and 6 edges, `table_count`: 1 (the
Components table, 6 rows), and `flagged_lines` with exactly 3 entries (the
two `TODO`/`TBD` lines and the `Assumption:` line under "Known Gaps" --
note the *second* "Assumption:" bullet about the Admin Portal will also be
flagged, so you should actually see 4 flagged lines in total).

## 2. Normalize the (already-drafted) architecture extraction

`examples/sample-draft-extraction.json` stands in for what the model would
produce after reading step 1's output -- in a real run you'd write this
JSON yourself based on the parsed artifact, then feed it in here:

```bash
python scripts/normalize_entities.py examples/sample-draft-extraction.json \
    --system-name "Mobile Banking Platform" --out /tmp/normalized.json
```

Expected: 6 components (`C-001`..`C-006`, in the order Mobile App, API
Gateway, Account API, Account Database, Notification Service, Admin
Portal), 6 data flows (`DF-001`..`DF-006`), 2 trust boundaries (`TB-001`,
`TB-002`), 1 security control (`SC-001`), 3 unknowns (`UNK-001`..`UNK-003`),
an empty `unresolved_data_flow_endpoints` list, and an empty `warnings` list
(the fixture was written with no duplicate names, so nothing gets merged).

## 3. Build the graph and run risk-pattern detection

```bash
python scripts/build_graph.py /tmp/normalized.json --system-name "Mobile Banking Platform" \
    --source-artifacts /tmp/src-001.json --validate --out /tmp/graph_bundle.json
```

Expected: `graph.nodes` has 6 entries, `graph.edges` has 6 entries,
`placeholder_nodes_created` is empty (every data-flow endpoint in the
fixture matches a known component), and `graph.risk_patterns` has **9**
entries, specifically:

| GRP | Pattern | Severity | Why |
|---|---|---|---|
| GRP-001 | Internet-exposed API Gateway reaches Account Database | Critical | Gateway -> Account API -> Account Database, 2 hops, PII at the end |
| GRP-002 | Trust-boundary crossing, unknown auth | High | Mobile App -> Account Database (legacy sync) |
| GRP-003 | Trust-boundary crossing, unknown auth | High | Account API -> Notification Service |
| GRP-004 | Authorization unknown on API call | High | Mobile App -> API Gateway |
| GRP-005 | Authorization unknown on API call | High | API Gateway -> Account API |
| GRP-006 | Trust boundary crossing without confirmed encryption | High | Mobile App -> Account Database (legacy sync) |
| GRP-007 | Admin interface may be broadly reachable | Medium | Admin Portal, internet_exposed=Unknown |
| GRP-008 | Third party receives classified data | High | Account API -> Notification Service |
| GRP-009 | Mobile app directly accesses a data store | Critical | Mobile App -> Account Database |

If `jsonschema` is installed, `validation.schema_checked` will be `true`
and `validation.valid` should be `true`; the graph was designed to be
schema-compliant.

The exact GRP numbering follows detector order in `detect_risk_patterns()`
(pattern 1, then 2, 3, ...), not severity -- don't be surprised that
Critical and High findings are interleaved.

## 4. Recommend a Checkmarx SAST scan configuration

The threats in `examples/sample-threat-model-output.json` carry `cwe` fields
(`CWE-862` on T-001, `CWE-306` on T-002) and the system's
`technology_profile.languages` is `["Java"]`. Feed those into the query
recommender:

```bash
python scripts/recommend_sast_queries.py --cwes 862,306 --languages Java --out /tmp/sast_queries.json
```

Expected: `mode` is `"fallback_queries"`, not `"preset"` -- CWE-306 (missing
authentication) has **zero** matching Java queries anywhere in the
Checkmarx catalog, so every preset caps out at 50% coverage (only CWE-862 is
coverable), below the default 60% threshold. `fallback_queries` lists
exactly 2 entries: `Java_Spring/Spring_Missing_Function_Level_Authorization`
and `Java_Spring/Spring_Missing_Object_Level_Authorization`, both CWE 862.
This is a genuine gap in the catalog, not a bug -- `sast_scan_configuration`
in the sample JSON already reflects this exact result.

## 5. Render the final report

`examples/sample-threat-model-output.json` is a hand-authored example of
the *finished* `threat-model-output.json` the model would assemble in
Phase 9 -- it references three of the nine risk patterns above (via T-001,
T-002, T-003), embeds the step-4 `sast_scan_configuration` result, and
embeds a trimmed 3-node excerpt of the graph in `appendix.graph` (not the
full 6-node graph from step 3) purely so the report template has something
concrete to render; a real run would set `appendix.graph` to step 3's
`graph` object in full.

```bash
python scripts/export_report.py --input examples/sample-threat-model-output.json --out /tmp/report.html
```

Expected: `/tmp/report.html` is a single self-contained HTML file with all
18 numbered sections populated (3 threats in section 10, 1 attack path in
section 11 with its own Mermaid diagram, 3 SAST focus areas plus the
`sast_scan_configuration` table in section 13, 3 DAST recommendations, 3
action items, 1 residual risk entry, and a pretty-printed graph JSON block
in section 17). Section 5 contains a Mermaid architecture diagram generated
from the 3-node graph excerpt. Open it in a browser with internet access
(for the Mermaid.js CDN script) to see both diagrams render. There is no
Jira export and no CSV backlog -- the HTML report is the only final-report
artifact this script produces.

## If something doesn't match

These scripts have been reviewed line-by-line but never executed (no
Python on this machine). If a real run disagrees with the expected output
above, that's a genuine bug to report/fix -- most likely in
`scripts/parse_markdown.py`'s Mermaid regexes, `build_graph.py`'s
pattern-detection conditionals, `scripts/recommend_sast_queries.py`'s CSV
header-skipping (the raw CSV has a stray `#TYPE System.Data.DataRow` line
before the real header), or `export_report.py`'s Mermaid diagram generation
--  since those are the least trivial parts of the pipeline.
