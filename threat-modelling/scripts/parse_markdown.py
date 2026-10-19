#!/usr/bin/env python3
"""
Artifact Ingestion Agent helper: Markdown parser.

Mechanically extracts structure from a Markdown architecture document so the
model can do semantic extraction on top of *cited* material instead of raw
text. This script does not infer architecture facts -- it only extracts
headings/sections, Mermaid diagrams (best-effort nodes/edges), tables, code
blocks, links, and lines worth double-checking (TODO/assumption/unknown
markers). Every extracted item carries a line reference back to the source
file so downstream agents can cite evidence.

Usage:
    python parse_markdown.py <file.md> [--artifact-id SRC-001] [--out out.json]

Output shape feeds `metadata.source_artifacts[]` (graph-schema.json) and the
`sources[]` / `artifact_inventory[]` structures described in SKILL.md Phase 2.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import read_text_file, sha256_of_file, slugify, save_json, eprint

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_RE = re.compile(r"^(```|~~~)\s*([A-Za-z0-9_+\-]*)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BARE_URL_RE = re.compile(r"(?<![(\[])\bhttps?://[^\s)>\]]+")
FLAG_KEYWORDS = (
    "todo", "tbd", "assume", "assumption", "unknown", "n/a",
    "not documented", "out of scope", "tbc", "fixme", "placeholder",
)

MERMAID_NODE_RE = re.compile(
    r"([A-Za-z0-9_\-]+)\s*"
    r"(\[\(|\(\(|\[\[|\{\{|\[|\(|\{)"
    r"([^\]\)\}]{1,120}?)"
    r"(\)\]|\)\)|\]\]|\}\}|\]|\)|\})"
)
MERMAID_NODE_SHAPE_PAIRS = {
    "[(": ")]", "((": "))", "[[": "]]", "{{": "}}", "[": "]", "(": ")", "{": "}",
}
# Optional inline shape/label on a node (e.g. "Mobile[Mobile App]") that can sit
# between an edge endpoint's bare ID and the arrow -- must be skippable so an
# edge like "Mobile[Mobile App] --> Gateway(API Gateway)" still matches; the
# label content itself is re-extracted separately by MERMAID_NODE_RE.
_SHAPE_SKIP = r"(?:(?:\[\(|\(\(|\[\[|\{\{|\[|\(|\{)[^\]\)\}]{0,120}?(?:\)\]|\)\)|\]\]|\}\}|\]|\)|\}))?"
MERMAID_EDGE_RE = re.compile(
    r"([A-Za-z0-9_\-]+)\s*" + _SHAPE_SKIP + r"\s*"
    r"(-{1,3}>|={1,3}>|-\.-{1,2}>|<-{1,3}>|--x|--o)\s*"
    r"(?:\|([^|]{1,160})\|\s*)?"
    r"([A-Za-z0-9_\-]+)"
)
MERMAID_EDGE_INLINE_LABEL_RE = re.compile(
    r"([A-Za-z0-9_\-]+)\s*" + _SHAPE_SKIP + r"\s*--\s*([^->][^-]{0,120}?)\s*-{1,2}>\s*([A-Za-z0-9_\-]+)"
)
SEQUENCE_EDGE_RE = re.compile(
    r"([A-Za-z0-9_\-]+)\s*(->>|-->>|->|-->|-x|--x)\s*([A-Za-z0-9_\-]+)\s*:\s*(.*)"
)


def github_slug(text: str, seen: dict) -> str:
    slug = slugify(text)
    if slug not in seen:
        seen[slug] = 0
        return slug
    seen[slug] += 1
    return f"{slug}-{seen[slug]}"


def parse_mermaid(block_text: str) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    is_sequence = bool(re.search(r"\bsequenceDiagram\b", block_text))

    for raw_line in block_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("%%"):
            continue
        if re.match(r"^(graph|flowchart|sequenceDiagram|subgraph|end|classDef|class|style|direction)\b", line, re.I):
            continue

        for m in MERMAID_NODE_RE.finditer(line):
            node_id, opener, label, closer = m.groups()
            if MERMAID_NODE_SHAPE_PAIRS.get(opener) != closer:
                continue  # mismatched bracket pair (e.g. stray ']' after a ')' close) - skip rather than mislabel
            nodes.setdefault(node_id, {"id": node_id, "label": label.strip()})

        if is_sequence:
            m = SEQUENCE_EDGE_RE.match(line)
            if m:
                src, arrow, dst, label = m.groups()
                nodes.setdefault(src, {"id": src, "label": src})
                nodes.setdefault(dst, {"id": dst, "label": dst})
                edges.append({"from": src, "to": dst, "label": label.strip(), "arrow": arrow})
            continue

        m = MERMAID_EDGE_INLINE_LABEL_RE.match(line)
        if m:
            src, label, dst = m.groups()
            nodes.setdefault(src, {"id": src, "label": src})
            nodes.setdefault(dst, {"id": dst, "label": dst})
            edges.append({"from": src, "to": dst, "label": label.strip(), "arrow": "-->"})
            continue

        m = MERMAID_EDGE_RE.match(line)
        if m:
            src, arrow, label, dst = m.groups()
            nodes.setdefault(src, {"id": src, "label": src})
            nodes.setdefault(dst, {"id": dst, "label": dst})
            edges.append({"from": src, "to": dst, "label": (label or "").strip(), "arrow": arrow})

    return {"nodes": list(nodes.values()), "edges": edges, "diagram_type": "sequence" if is_sequence else "flowchart"}


def parse_markdown(text: str) -> dict:
    lines = text.splitlines()
    sections = []
    stack: list[dict] = []  # open headings by level
    slug_seen: dict = {}
    code_blocks = []
    diagrams = []
    tables = []
    links = []
    flagged_lines = []

    in_fence = False
    fence_lang = ""
    fence_start = 0
    fence_buffer: list[str] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        lineno = i + 1

        fence_m = FENCE_RE.match(line)
        if fence_m:
            if not in_fence:
                in_fence = True
                fence_lang = fence_m.group(2).lower()
                fence_start = lineno
                fence_buffer = []
            else:
                content = "\n".join(fence_buffer)
                current_section = stack[-1]["path"] if stack else None
                if fence_lang == "mermaid":
                    parsed = parse_mermaid(content)
                    diagrams.append({
                        "type": "mermaid",
                        "diagram_type": parsed["diagram_type"],
                        "section": current_section,
                        "line_start": fence_start,
                        "line_end": lineno,
                        "raw": content,
                        "nodes": parsed["nodes"],
                        "edges": parsed["edges"],
                    })
                else:
                    code_blocks.append({
                        "language": fence_lang or "text",
                        "section": current_section,
                        "line_start": fence_start,
                        "line_end": lineno,
                        "content": content,
                    })
                in_fence = False
                fence_lang = ""
                fence_buffer = []
            i += 1
            continue

        if in_fence:
            fence_buffer.append(line)
            i += 1
            continue

        heading_m = HEADING_RE.match(line)
        if heading_m:
            level = len(heading_m.group(1))
            title = heading_m.group(2).strip()
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            anchor = github_slug(title, slug_seen)
            path = " > ".join([s["title"] for s in stack] + [title])
            section = {
                "heading": title,
                "level": level,
                "anchor": anchor,
                "path": path,
                "line_start": lineno,
                "line_end": None,
                "text": "",
            }
            sections.append(section)
            stack.append({"level": level, "title": title, "path": path, "ref": section})
            i += 1
            continue

        if TABLE_ROW_RE.match(line) and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            j = i + 2
            rows = []
            while j < n and TABLE_ROW_RE.match(lines[j]):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            current_section = stack[-1]["ref"]["path"] if stack else None
            tables.append({
                "section": current_section,
                "line_start": lineno,
                "line_end": j,
                "header": header,
                "rows": rows,
            })
            i = j
            continue

        for m in LINK_RE.finditer(line):
            links.append({"text": m.group(1), "url": m.group(2), "line": lineno})
        for m in BARE_URL_RE.finditer(line):
            links.append({"text": "", "url": m.group(0), "line": lineno})

        lower = line.lower()
        if any(kw in lower for kw in FLAG_KEYWORDS):
            flagged_lines.append({"line": lineno, "text": line.strip()})

        if stack:
            stack[-1]["ref"]["text"] += (line + "\n")
        i += 1

    for idx, section in enumerate(sections):
        if section["line_end"] is None:
            next_same_or_higher = None
            for later in sections[idx + 1:]:
                if later["level"] <= section["level"]:
                    next_same_or_higher = later["line_start"] - 1
                    break
            section["line_end"] = next_same_or_higher or n
        section["text"] = section["text"].strip()

    return {
        "sections": sections,
        "diagrams": diagrams,
        "tables": tables,
        "code_blocks": code_blocks,
        "links": links,
        "flagged_lines": flagged_lines,
        "line_count": n,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Path to the Markdown file to parse")
    parser.add_argument("--artifact-id", default="SRC-001", help="Source artifact ID (e.g. SRC-001)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        eprint(f"error: file not found: {path}")
        return 1

    text = read_text_file(path)
    parsed = parse_markdown(text)

    result = {
        "artifact": {
            "id": args.artifact_id,
            "file_name": path.name,
            "type": "markdown",
            "location": str(path),
            "hash": sha256_of_file(path),
        },
        "sections": parsed["sections"],
        "diagrams_detected": len(parsed["diagrams"]) > 0,
        "diagrams": parsed["diagrams"],
        "tables": parsed["tables"],
        "code_blocks": parsed["code_blocks"],
        "links": parsed["links"],
        "flagged_lines": parsed["flagged_lines"],
        "stats": {
            "line_count": parsed["line_count"],
            "section_count": len(parsed["sections"]),
            "diagram_count": len(parsed["diagrams"]),
            "table_count": len(parsed["tables"]),
            "code_block_count": len(parsed["code_blocks"]),
        },
    }

    save_json(result, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
