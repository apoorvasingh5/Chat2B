#!/usr/bin/env python3
"""
Compares two Threat Modelling HTML reports (as produced by export_report.py
from report-template.html) and prints a structured diff: components added/
removed, threats added/removed (matched by normalized title), category and
severity distribution changes.

This exists so comparing two runs of the same system (before/after a skill
change, before/after new evidence, a re-run after answering open questions)
is a repeatable command instead of manually reading two ~100KB HTML files
side by side each time.

Only works on reports produced by this skill's own template (it parses the
known section/table structure); it is not a general HTML diff tool.

Usage:
    python diff_threat_reports.py --old "old-report.html" --new "new-report.html"
    python diff_threat_reports.py --old old.html --new new.html --out diff.json
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from common import save_json, normalize_key, eprint

THREAT_ROW_RE = re.compile(
    r'<tr><td>(T-\d+)</td><td>(.*?)</td><td>(.*?)</td>'
    r'<td><span class="badge (\w+)">\w+</span></td><td>(.*?)</td><td>(.*?)</td></tr>'
)
CATEGORY_RE = re.compile(r'<strong>Category:</strong>\s*(.*?)\s*&middot;')


def unescape(s: str) -> str:
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def extract_section(doc: str, section_id: str) -> str:
    m = re.search(rf'<section id="{re.escape(section_id)}">(.*?)</section>', doc, re.DOTALL)
    return m.group(1) if m else ""


def parse_report(path: Path) -> dict:
    doc = path.read_text(encoding="utf-8", errors="replace")

    threats_section = extract_section(doc, "threats")
    threats = []
    for tid, title, component, severity, confidence, stride in THREAT_ROW_RE.findall(threats_section):
        threats.append({
            "id": tid,
            "title": unescape(title),
            "component": unescape(component),
            "severity": severity,
            "confidence": unescape(confidence),
            "stride": unescape(stride),
        })
    categories = [unescape(c) for c in CATEGORY_RE.findall(doc)]

    arch_section = extract_section(doc, "arch")
    comp_match = re.search(r'<h3>Components</h3>\s*<ul>(.*?)</ul>', arch_section, re.DOTALL)
    components = [unescape(c) for c in re.findall(r'<li>(.*?)</li>', comp_match.group(1))] if comp_match else []
    has_workflows = "Key Business Workflows" in arch_section

    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', doc, re.DOTALL)

    return {
        "file": str(path),
        "title": unescape(title_match.group(1)) if title_match else "",
        "components": components,
        "has_business_workflows": has_workflows,
        "threats": threats,
        "categories": categories,
    }


COMPONENT_ID_PREFIX_RE = re.compile(r'^C-\d+\s+')
COMPONENT_TYPE_SUFFIX_RE = re.compile(r'\s*\([^)]*\)\s*$')

STOPWORDS = {
    "a", "an", "the", "is", "are", "and", "or", "to", "of", "in", "on", "for",
    "with", "without", "no", "not", "via", "from", "by", "when", "if", "may",
    "can", "allow", "allows", "into", "may", "at", "as", "be",
}


def normalize_component_name(name: str) -> str:
    """Strips a leading 'C-### ' id and a trailing '(Type)'/'(Vendor)' suffix
    so independently-generated reports' different ID numbering and
    type-vs-vendor framing (e.g. 'C-009 Checkmarx IAM (IdentityProvider)' vs
    'Checkmarx IAM (Keycloak)') can still match on the part that actually
    identifies the thing."""
    stripped = COMPONENT_ID_PREFIX_RE.sub("", name)
    stripped = COMPONENT_TYPE_SUFFIX_RE.sub("", stripped)
    return normalize_key(stripped)


def diff_lists(old_items: list[str], new_items: list[str]) -> dict:
    old_keys = {normalize_component_name(i): i for i in old_items}
    new_keys = {normalize_component_name(i): i for i in new_items}
    return {
        "only_in_old": [old_keys[k] for k in old_keys if k not in new_keys],
        "only_in_new": [new_keys[k] for k in new_keys if k not in old_keys],
        "in_both": [new_keys[k] for k in new_keys if k in old_keys],
    }


def title_words(title: str) -> set:
    words = re.findall(r'[a-z0-9]+', title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def diff_threats(old_threats: list[dict], new_threats: list[dict], fuzzy_threshold: float = 0.2) -> dict:
    """Threats are free-text titles with no stable cross-run ID, so this
    cannot do exact matching -- it scores every old/new pair by word-overlap
    (Jaccard over non-stopword tokens) and greedily pairs the best mutual
    matches above fuzzy_threshold. This is approximate (a human/model should
    confirm a 'probable match' actually describes the same underlying risk,
    not just similar wording) -- it is here to cut the two lists down to a
    manageable size for that review, not to replace it."""
    old_tokens = [title_words(t["title"]) for t in old_threats]
    new_tokens = [title_words(t["title"]) for t in new_threats]

    scores = []
    for i, ot in enumerate(old_tokens):
        for j, nt in enumerate(new_tokens):
            score = jaccard(ot, nt)
            if score >= fuzzy_threshold:
                scores.append((score, i, j))
    scores.sort(reverse=True)

    matched_old, matched_new, probable_matches = set(), set(), []
    for score, i, j in scores:
        if i in matched_old or j in matched_new:
            continue
        matched_old.add(i)
        matched_new.add(j)
        probable_matches.append({"old": old_threats[i], "new": new_threats[j], "similarity": round(score, 2)})

    only_old = [t for i, t in enumerate(old_threats) if i not in matched_old]
    only_new = [t for j, t in enumerate(new_threats) if j not in matched_new]

    return {
        "only_in_old": only_old,
        "only_in_new": only_new,
        "probable_matches": probable_matches,
        "matched_count": len(probable_matches),
    }


def category_counts(categories: list[str]) -> dict:
    counts: dict[str, int] = {}
    for c in categories:
        counts[c] = counts.get(c, 0) + 1
    return counts


def severity_counts(threats: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for t in threats:
        counts[t["severity"]] = counts.get(t["severity"], 0) + 1
    return counts


def print_human(old: dict, new: dict, comp_diff: dict, threat_diff: dict) -> None:
    print(f"OLD: {old['title']} ({len(old['threats'])} threats, {len(old['components'])} components)")
    print(f"NEW: {new['title']} ({len(new['threats'])} threats, {len(new['components'])} components)")
    print()
    print(f"Business workflows section: old={old['has_business_workflows']} new={new['has_business_workflows']}")
    print()
    print("=== Components ===")
    if comp_diff["only_in_old"]:
        print("Only in OLD:")
        for c in comp_diff["only_in_old"]:
            print(f"  - {c}")
    if comp_diff["only_in_new"]:
        print("Only in NEW:")
        for c in comp_diff["only_in_new"]:
            print(f"  - {c}")
    print()
    print(f"=== Threats: {threat_diff['matched_count']} probable matches (fuzzy title overlap, confirm by eye), "
          f"{len(threat_diff['only_in_old'])} only in OLD, {len(threat_diff['only_in_new'])} only in NEW ===")
    if threat_diff["probable_matches"]:
        print("\nProbable matches (similar wording -- verify these describe the same underlying risk):")
        for m in threat_diff["probable_matches"]:
            print(f"  [{m['similarity']}] OLD {m['old']['id']}: {m['old']['title']}")
            print(f"          NEW {m['new']['id']}: {m['new']['title']}")
    if threat_diff["only_in_old"]:
        print("\nOnly in OLD (regressions -- the new run should explain why, or these are real gaps to close):")
        for t in threat_diff["only_in_old"]:
            print(f"  {t['id']} [{t['severity']}] {t['title']} ({t['component']})")
    if threat_diff["only_in_new"]:
        print("\nOnly in NEW (new findings):")
        for t in threat_diff["only_in_new"]:
            print(f"  {t['id']} [{t['severity']}] {t['title']} ({t['component']})")
    print()
    print("=== Category distribution ===")
    old_cats = category_counts(old["categories"])
    new_cats = category_counts(new["categories"])
    all_cats = sorted(set(old_cats) | set(new_cats))
    for c in all_cats:
        print(f"  {c}: old={old_cats.get(c, 0)} new={new_cats.get(c, 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--old", required=True, help="Path to the earlier report HTML")
    parser.add_argument("--new", required=True, help="Path to the later report HTML")
    parser.add_argument("--out", default=None, help="Optional: write the full structured diff as JSON here")
    parser.add_argument("--fuzzy-threshold", type=float, default=0.2,
                         help="Minimum title word-overlap (Jaccard, 0-1) to call two threats a probable match "
                              "(default 0.2; security-finding titles are paraphrased enough across independent "
                              "runs that a strict threshold under-matches -- lower it further for very short "
                              "titles, raise it if you're getting false matches)")
    args = parser.parse_args()

    old_path, new_path = Path(args.old), Path(args.new)
    if not old_path.is_file() or not new_path.is_file():
        eprint("error: both --old and --new must be existing files")
        return 1

    old = parse_report(old_path)
    new = parse_report(new_path)
    comp_diff = diff_lists(old["components"], new["components"])
    threat_diff = diff_threats(old["threats"], new["threats"], fuzzy_threshold=args.fuzzy_threshold)

    print_human(old, new, comp_diff, threat_diff)

    if args.out:
        save_json({
            "old": old, "new": new,
            "component_diff": comp_diff,
            "threat_diff": threat_diff,
            "old_category_counts": category_counts(old["categories"]),
            "new_category_counts": category_counts(new["categories"]),
            "old_severity_counts": severity_counts(old["threats"]),
            "new_severity_counts": severity_counts(new["threats"]),
        }, args.out)
        eprint(f"\nwrote full structured diff to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
