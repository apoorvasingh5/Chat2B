#!/usr/bin/env python3
"""
SAST Recommendation Agent helper: Checkmarx preset/query mapping.

Threat identification (which CWEs matter, which languages are in play) is
the model's job -- reading the architecture and applying STRIDE/OWASP is
reasoning, not a lookup. Once that's decided, "which Checkmarx preset (or
individual queries) actually covers those CWEs" is a large, purely
mechanical table lookup against
references/cx-presets-queries/9.7.0_All_queries_by_preset_list.csv (~24k
rows) -- exactly the kind of thing that belongs in a script instead of the
model eyeballing a spreadsheet.

For each requested language, this script:
  1. Scores every Checkmarx preset by what fraction of the requested CWEs
     it has at least one query for, in that language.
  2. If the best preset clears --coverage-threshold, recommends that preset
     plus any gap CWEs it doesn't cover (with supplemental individual
     queries for those gaps).
  3. If no preset clears the threshold, skips the preset recommendation
     entirely and instead lists the individual queries (across all presets,
     i.e. equivalent to Checkmarx's "All" preset) that match the requested
     CWEs for that language -- "enable these specific queries" instead of
     "use this preset".

CWE "0" rows in the CSV mean the query has no assigned CWE (code-quality /
best-practice rules); they are never matched against requested CWEs.

Usage:
    python recommend_sast_queries.py --cwes 89,79,352,798 --languages Python,JavaScript
    python recommend_sast_queries.py --cwes 89,79 --languages Java --coverage-threshold 70 --out result.json
"""

from __future__ import annotations

import argparse
import csv as csv_module
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import save_json, utc_now_iso, eprint

DEFAULT_CSV = (
    Path(__file__).resolve().parent.parent
    / "references" / "cx-presets-queries" / "9.7.0_All_queries_by_preset_list.csv"
)

# Common aliases -> the exact "Language Name" values used in the CSV.
LANGUAGE_ALIASES = {
    "js": "JavaScript", "node": "JavaScript", "nodejs": "JavaScript", "typescript": "JavaScript", "ts": "JavaScript",
    "c#": "CSharp", "csharp": "CSharp", ".net": "VbNet",
    "c++": "CPP", "cpp": "CPP",
    "objective-c": "Objc", "objectivec": "Objc",
    "vb.net": "VbNet", "vbnet": "VbNet",
    "vb6": "VB6", "vbscript": "VbScript",
    "pl/sql": "PLSQL", "plsql": "PLSQL",
    "golang": "Go",
}

UNMAPPED_CWE = "0"


def normalize_language(raw: str) -> str:
    key = raw.strip().lower()
    return LANGUAGE_ALIASES.get(key, raw.strip())


def normalize_cwe(raw: str) -> str:
    return raw.strip().upper().replace("CWE-", "").replace("CWE", "").strip()


def load_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        first_line = f.readline()
        if not first_line.lstrip().startswith("#TYPE"):
            f.seek(0)
        reader = csv_module.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "preset": (row.get("Preset Name") or "").strip(),
                "language": (row.get("Language Name") or "").strip(),
                "package": (row.get("Package Name") or "").strip(),
                "query_name": (row.get("Query Name") or "").strip(),
                "severity": (row.get("Query Severity") or "").strip(),
                "cwe": normalize_cwe(row.get("CWE") or "0"),
            })
        return rows


def available_languages(rows: list[dict]) -> list[str]:
    return sorted({r["language"] for r in rows if r["language"]})


def _query_key(row: dict) -> tuple:
    return (row["package"], row["query_name"])


def score_presets_for_language(rows: list[dict], language: str, target_cwes: set[str]) -> list[dict]:
    by_preset: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["language"] == language:
            by_preset[row["preset"]].append(row)

    scored = []
    for preset, preset_rows in by_preset.items():
        covered = {r["cwe"] for r in preset_rows if r["cwe"] in target_cwes}
        coverage_pct = round(100.0 * len(covered) / len(target_cwes), 1) if target_cwes else 0.0
        scored.append({
            "preset": preset,
            "coverage_pct": coverage_pct,
            "covered_cwes": sorted(covered, key=lambda x: (len(x), x)),
            "query_count": len(preset_rows),
        })
    scored.sort(key=lambda s: (s["coverage_pct"], s["query_count"]), reverse=True)
    return scored


def matching_queries(rows: list[dict], language: str, cwes: set[str], limit: int = 50) -> tuple[list[dict], int]:
    seen: dict[tuple, dict] = {}
    for row in rows:
        if row["language"] != language or row["cwe"] not in cwes or row["cwe"] == UNMAPPED_CWE:
            continue
        key = _query_key(row)
        if key not in seen:
            seen[key] = {
                "package": row["package"],
                "query_name": row["query_name"],
                "severity": row["severity"],
                "cwe": row["cwe"],
            }
    all_matches = sorted(seen.values(), key=lambda q: (q["cwe"], q["package"], q["query_name"]))
    return all_matches[:limit], max(0, len(all_matches) - limit)


def recommend_for_language(rows: list[dict], language: str, target_cwes: set[str],
                            coverage_threshold: float, query_limit: int) -> dict:
    langs = available_languages(rows)
    if language not in langs:
        return {
            "language": language,
            "error": "language_not_found_in_catalog",
            "available_languages": langs,
        }

    scored = score_presets_for_language(rows, language, target_cwes)
    best = scored[0] if scored else None

    if best and best["coverage_pct"] >= coverage_threshold:
        gap_cwes = sorted(target_cwes - set(best["covered_cwes"]), key=lambda x: (len(x), x))
        supplemental, truncated = matching_queries(rows, language, set(gap_cwes), query_limit) if gap_cwes else ([], 0)
        return {
            "language": language,
            "mode": "preset",
            "recommended_preset": best["preset"],
            "coverage_pct": best["coverage_pct"],
            "covered_cwes": best["covered_cwes"],
            "gap_cwes": gap_cwes,
            "supplemental_queries_for_gaps": supplemental,
            "supplemental_queries_truncated_count": truncated,
            "top_alternative_presets": scored[1:4],
        }

    fallback, truncated = matching_queries(rows, language, target_cwes, query_limit)
    return {
        "language": language,
        "mode": "fallback_queries",
        "reason": (
            f"No preset reaches the {coverage_threshold}% coverage threshold "
            f"for the requested CWEs in {language}"
            + (f" (best was '{best['preset']}' at {best['coverage_pct']}%)" if best else " (no presets found)")
            + "."
        ),
        "fallback_queries": fallback,
        "fallback_queries_truncated_count": truncated,
        "top_presets_considered": scored[:4],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to the Checkmarx preset/query CSV export")
    parser.add_argument("--cwes", required=True, help="Comma-separated CWE numbers (e.g. 89,79,352), with or without a 'CWE-' prefix")
    parser.add_argument("--languages", required=True, help="Comma-separated language names (e.g. Python,JavaScript,Java)")
    parser.add_argument("--coverage-threshold", type=float, default=60.0,
                         help="Minimum preset CWE-coverage %% required to recommend a preset instead of individual queries (default 60)")
    parser.add_argument("--query-limit", type=int, default=50, help="Max individual queries to list per language (default 50)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        eprint(f"error: CSV not found: {csv_path}")
        return 1

    target_cwes = {normalize_cwe(c) for c in args.cwes.split(",") if c.strip()}
    languages = [normalize_language(lang) for lang in args.languages.split(",") if lang.strip()]

    rows = load_rows(csv_path)

    results: list[dict] = []
    for language in languages:
        results.append(recommend_for_language(rows, language, target_cwes, args.coverage_threshold, args.query_limit))

    output = {
        "generated_at": utc_now_iso(),
        "csv_source": str(csv_path),
        "requested_cwes": sorted(target_cwes, key=lambda x: (len(x), x)),
        "coverage_threshold": args.coverage_threshold,
        "results": results,
        "note": "CWE '0' rows (queries with no assigned CWE) are never matched; they represent code-quality/best-practice rules rather than CWE-specific vulnerability checks.",
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} ({len(results)} language(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
