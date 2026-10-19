#!/usr/bin/env python3
"""
Final Report helper (SKILL.md Phase 9).

Renders assets/report-template.html against a finished
threat-model-output.json (as produced by the model per
references/output-schemas/threat-model-output.json) into a single
self-contained HTML report. The final report is always HTML -- this script
does not produce Markdown, Jira exports, or a CSV backlog.

Two diagrams are generated deterministically from the structured JSON
(never hand-authored by the model), so they can never drift out of sync
with the underlying data:

  - the architecture diagram, from appendix.graph (nodes/edges), grouped
    into subgraphs by trust_zone;
  - one diagram per attack path, from attack_paths[].path.

Both are emitted as Mermaid.js source text; the template loads Mermaid from
a CDN and renders them client-side when the HTML file is opened.

Templating uses a small, dependency-free Mustache-like syntax so this script
has no third-party requirements:

    {{field}}                 HTML-escaped scalar substitution (dotted paths supported)
    {{{field}}}               same, WITHOUT HTML-escaping (use only for pre-escaped/raw content)
    {{#list}} ... {{/list}}   repeat the block once per item (or once, if the
                               value is a truthy non-list) with that item
                               pushed onto the context stack
    {{^list}} ... {{/list}}   render the block only if the value is falsy/empty
    {{.}}                     the current item, inside a loop over scalars
    {{join list.path}}        render a list of strings as ", "-joined text
    {{path.length}}           render len() of a resolved list

Usage:
    python export_report.py --input threat_model.json --out report.html
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import load_json, eprint

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "report-template.html"

TOKEN_RE = re.compile(
    r"\{\{\{\s*(?P<raw>[^{}]+?)\s*\}\}\}"
    r"|\{\{(?P<type>[#^/]?)\s*(?P<name>[^{}]+?)\s*\}\}"
)

# Mustache "standalone lines": a section/inverted/close tag that is the only
# thing on its line (aside from whitespace) contributes no output itself, so
# its line -- including the trailing newline -- is dropped entirely rather
# than left as a blank line. Without this, every loop in the template leaves
# a stray blank line before/after each rendered item.
STANDALONE_TAG_RE = re.compile(r"^[ \t]*(\{\{[#^/][^{}]+\}\})[ \t]*\r?\n", re.MULTILINE)


def strip_standalone_tag_lines(template: str) -> str:
    return STANDALONE_TAG_RE.sub(r"\1", template)


# ---------------------------------------------------------------------------
# Minimal Mustache-like template engine (double braces = HTML-escaped,
# triple braces = raw)
# ---------------------------------------------------------------------------

def tokenize(template: str) -> list[tuple]:
    tokens = []
    pos = 0
    for m in TOKEN_RE.finditer(template):
        if m.start() > pos:
            tokens.append(("text", template[pos:m.start()]))
        if m.group("raw") is not None:
            tokens.append(("raw", m.group("raw")))
        else:
            ttype = m.group("type")
            name = m.group("name")
            if ttype == "#":
                tokens.append(("section", name))
            elif ttype == "^":
                tokens.append(("invert", name))
            elif ttype == "/":
                tokens.append(("close", name))
            else:
                tokens.append(("var", name))
        pos = m.end()
    if pos < len(template):
        tokens.append(("text", template[pos:]))
    return tokens


def parse(tokens: list[tuple]) -> list:
    root: list = []
    stack: list[list] = [root]
    for ttype, name in tokens:
        current = stack[-1]
        if ttype in ("section", "invert"):
            children: list = []
            current.append((ttype, name, children))
            stack.append(children)
        elif ttype == "close":
            if len(stack) > 1:
                stack.pop()
        else:
            current.append((ttype, name))
    return root


def _resolve(path: str, stack: list) -> Any:
    if path == ".":
        return stack[-1] if stack else None
    segments = path.split(".")
    for ctx in reversed(stack):
        value = ctx
        ok = True
        for seg in segments:
            if seg == "length":
                if isinstance(value, (list, dict, str)):
                    value = len(value)
                else:
                    ok = False
                    break
                continue
            if isinstance(value, dict) and seg in value:
                value = value[seg]
            else:
                ok = False
                break
        if ok:
            return value
    return None


def _is_truthy(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def _stringify(name: str, stack: list) -> str | None:
    if name.startswith("join "):
        value = _resolve(name[5:].strip(), stack)
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value) if value is not None else None
    value = _resolve(name, stack)
    return str(value) if value is not None else None


def render_nodes(nodes: list, stack: list) -> str:
    out = []
    for node in nodes:
        ttype = node[0]
        if ttype == "text":
            out.append(node[1])
        elif ttype == "var":
            text = _stringify(node[1], stack)
            if text is not None:
                out.append(html.escape(text))
        elif ttype == "raw":
            text = _stringify(node[1], stack)
            if text is not None:
                out.append(text)
        elif ttype in ("section", "invert"):
            name, children = node[1], node[2]
            value = _resolve(name, stack)
            truthy = _is_truthy(value)
            if ttype == "invert":
                if not truthy:
                    out.append(render_nodes(children, stack))
                continue
            if not truthy:
                continue
            if isinstance(value, list):
                for item in value:
                    stack.append(item)
                    out.append(render_nodes(children, stack))
                    stack.pop()
            else:
                stack.append(value)
                out.append(render_nodes(children, stack))
                stack.pop()
    return "".join(out)


def render_template(template_text: str, data: dict) -> str:
    tree = parse(tokenize(strip_standalone_tag_lines(template_text)))
    return render_nodes(tree, [data])


# ---------------------------------------------------------------------------
# Deterministic Mermaid diagram generation from the structured graph/paths
# ---------------------------------------------------------------------------

def _mermaid_id(raw_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", raw_id or "N")


def _mermaid_text(text: str, max_len: int = 70) -> str:
    """Sanitize text for use inside a Mermaid quoted label. Strips
    characters that are special to Mermaid's own grammar (quotes, pipes)
    *and* to HTML (<, >, &) -- the latter so this is safe to embed whether
    or not the HTML template's escaping and the Mermaid.js version's
    textContent/innerHTML handling line up, rather than relying on either."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = text.replace('"', "'").replace("|", "/")
    text = text.replace("&", "and").replace("<", "(").replace(">", ")")
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


def _node_style_class(node: dict) -> str:
    if node.get("internet_exposed") == "Yes":
        return "exposed"
    node_type = node.get("type", "")
    if node_type in ("SecretStore", "AdminInterface", "IdentityProvider", "AuthorizationServer"):
        return "control"
    if node_type in ("Database", "DataStore", "ObjectStorage", "MessageQueue", "EventStream"):
        return "datastore"
    return "internal"


def graph_to_mermaid(graph: dict) -> str:
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    if not nodes:
        return ""

    by_zone: dict[str, list] = {}
    for node in nodes:
        by_zone.setdefault(node.get("trust_zone") or "Unknown", []).append(node)

    lines = ["flowchart LR"]
    for zone_index, (zone, zone_nodes) in enumerate(by_zone.items(), start=1):
        lines.append(f'  subgraph Z{zone_index}["{_mermaid_text(zone, 40)}"]')
        for node in zone_nodes:
            node_id = _mermaid_id(node.get("id", ""))
            label = _mermaid_text(f"{node.get('id', '')} {node.get('name', '')} ({node.get('type', '')})")
            lines.append(f'    {node_id}["{label}"]:::{_node_style_class(node)}')
        lines.append("  end")

    for edge in edges:
        src = _mermaid_id(edge.get("from", ""))
        dst = _mermaid_id(edge.get("to", ""))
        label = _mermaid_text(f"{edge.get('relationship', '')} {edge.get('protocol', '')}".strip())
        arrow = "-.->" if edge.get("crosses_trust_boundary") == "Yes" else "-->"
        lines.append(f'  {src} {arrow}|"{label}"| {dst}')

    lines.append("  classDef exposed fill:#3a1518,stroke:#e5484d,color:#f3b4b6;")
    lines.append("  classDef control fill:#3a2c12,stroke:#f3a340,color:#f7cf9a;")
    lines.append("  classDef datastore fill:#12233a,stroke:#6f9cde,color:#a9c6ec;")
    lines.append("  classDef internal fill:#122a20,stroke:#4cc9a3,color:#a8e9d3;")
    return "\n".join(lines)


def attack_path_to_mermaid(attack_path: dict) -> str:
    steps = attack_path.get("path") or []
    if not steps:
        return ""

    step_ids = [f"S{i}" for i in range(len(steps))]
    lines = ["flowchart LR"]
    for step_id, step in zip(step_ids, steps):
        lines.append(f'  {step_id}["{_mermaid_text(step, 40)}"]')
    for a, b in zip(step_ids, step_ids[1:]):
        lines.append(f"  {a} --> {b}")

    lines.append("  classDef entry fill:#3a1518,stroke:#e5484d,color:#f3b4b6;")
    lines.append("  classDef target fill:#3a2c12,stroke:#f3a340,color:#f7cf9a;")
    lines.append(f"  class {step_ids[0]} entry;")
    lines.append(f"  class {step_ids[-1]} target;")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report-specific data prep
# ---------------------------------------------------------------------------

def prepare_report_data(threat_model: dict) -> dict:
    data = json.loads(json.dumps(threat_model))  # deep copy

    appendix = data.setdefault("appendix", {})
    graph = appendix.get("graph")
    if not isinstance(graph, dict):
        graph = {}
        appendix["graph"] = graph
    graph.setdefault("nodes", [])
    graph.setdefault("edges", [])
    graph.setdefault("risk_patterns", [])
    graph["json"] = json.dumps(
        {k: v for k, v in graph.items() if k != "json"}, indent=2, ensure_ascii=False
    )

    data["architecture_diagram_mermaid"] = graph_to_mermaid(graph)

    for attack_path in data.get("attack_paths", []):
        attack_path["mermaid"] = attack_path_to_mermaid(attack_path)

    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="Path to the final threat-model-output.json")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Path to the HTML report template")
    parser.add_argument("--out", default="-", help="Output HTML report path, or '-' for stdout")
    args = parser.parse_args()

    threat_model = load_json(args.input)

    template_path = Path(args.template)
    if not template_path.exists():
        eprint(f"error: template not found: {template_path}")
        return 1
    template_text = template_path.read_text(encoding="utf-8")

    report_data = prepare_report_data(threat_model)
    report_html = render_template(template_text, report_data)

    if args.out == "-":
        sys.stdout.write(report_html)
    else:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report_html, encoding="utf-8")
        eprint(f"wrote {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
