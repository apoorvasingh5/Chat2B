#!/usr/bin/env python3
"""
MITRE ATT&CK / CAPEC mapping helper.

Deciding *which* threats and risk patterns matter is the model's job
(reasoning over the graph, per SKILL.md Sec 8). Deciding *which published
ATT&CK technique ID or CAPEC ID a given CWE or graph risk-pattern key
corresponds to* is a lookup against a reference table, not something the
model should reason out fresh each time -- that is exactly the kind of
"plausible-looking but unverifiable ID" the model is prone to guess
confidently and wrongly (see Core Operating Principle 2 in SKILL.md: do not
assert unsupported certainty).

This script performs that lookup deterministically against
references/threat-frameworks/attack-technique-map.json and returns, for a
given set of CWEs and/or build_graph.py risk-pattern keys, the matching
CAPEC IDs and ATT&CK technique IDs -- or an explicit "no_seed_mapping" /
"why_no_attack_technique" result instead of inventing one.

IMPORTANT: attack-technique-map.json is a small, hand-curated *seed* table
(see its "_confidence_note"), not an import of the authoritative MITRE
CAPEC/ATT&CK corpora. Every record this script returns carries
"confidence": "seed-unverified". Treat it as a reasoned starting point that
should be verified (and ideally replaced with real data pulled from
https://github.com/mitre/cti and https://capec.mitre.org) before being
treated as certified, the same way scripts/recommend_sast_queries.py works
off a real Checkmarx CSV export rather than a hand-typed table.

Usage:
    python map_attack_techniques.py --cwes 89,79,352,862
    python map_attack_techniques.py --risk-pattern-keys internet_exposed_reaches_sensitive_store,secret_used_outside_managed_store
    python map_attack_techniques.py --graph-bundle artifacts/graph_bundle.json --cwes 89,918 --out attack_map.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import load_json, save_json, eprint

DEFAULT_MAP = (
    Path(__file__).resolve().parent.parent
    / "references" / "threat-frameworks" / "attack-technique-map.json"
)


def normalize_cwe(raw: str) -> str:
    return raw.strip().upper().replace("CWE-", "").replace("CWE", "").strip()


def lookup_cwe(table: dict, cwe: str) -> dict:
    cwe_entry = table.get("cwe_to_capec", {}).get(cwe)
    if not cwe_entry:
        return {
            "cwe": f"CWE-{cwe}",
            "status": "no_seed_mapping",
            "note": "No CAPEC mapping in the seed table for this CWE. Do not guess one -- "
                    "look it up at https://capec.mitre.org or leave it unmapped.",
        }

    result: dict[str, Any] = {
        "cwe": f"CWE-{cwe}",
        "status": "mapped",
        "capec": cwe_entry.get("capec", []),
        "confidence": cwe_entry.get("confidence", "seed-unverified"),
        "attack_techniques": [],
    }
    capec_table = table.get("capec_to_attack", {})
    seen_techniques: dict[str, None] = {}
    why_notes = []
    for capec_label in cwe_entry.get("capec", []):
        capec_id = capec_label.split()[0]  # "CAPEC-66 SQL Injection" -> "CAPEC-66"
        entry = capec_table.get(capec_id)
        if not entry:
            continue
        for t in entry.get("attack_techniques", []):
            seen_techniques[t] = None
        if entry.get("why_no_attack_technique"):
            why_notes.append(f"{capec_id}: {entry['why_no_attack_technique']}")
    result["attack_techniques"] = list(seen_techniques)
    if why_notes:
        result["why_no_attack_technique"] = why_notes
    return result


def lookup_risk_pattern(table: dict, key: str) -> dict:
    entry = table.get("graph_risk_patterns", {}).get(key)
    if not entry:
        return {
            "pattern_key": key,
            "status": "no_seed_mapping",
            "note": "No ATT&CK mapping in the seed table for this build_graph.py pattern_key.",
        }
    result = {
        "pattern_key": key,
        "status": "mapped",
        "tactics": entry.get("tactics", []),
        "attack_techniques": entry.get("attack_techniques", []),
        "confidence": entry.get("confidence", "seed-unverified"),
    }
    if entry.get("why_no_attack_technique"):
        result["why_no_attack_technique"] = entry["why_no_attack_technique"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--map", default=str(DEFAULT_MAP), help="Path to attack-technique-map.json")
    parser.add_argument("--cwes", default="", help="Comma-separated CWE numbers (e.g. 89,79,862), with or without 'CWE-' prefix")
    parser.add_argument("--risk-pattern-keys", default="",
                         help="Comma-separated build_graph.py risk_patterns[].pattern_key values")
    parser.add_argument("--graph-bundle", default=None,
                         help="A build_graph.py output JSON; if given, its risk_patterns[].pattern_key values "
                              "are used automatically instead of/in addition to --risk-pattern-keys")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        eprint(f"error: mapping file not found: {map_path}")
        return 1
    table = load_json(map_path)

    cwes = [normalize_cwe(c) for c in args.cwes.split(",") if c.strip()]
    keys = [k.strip() for k in args.risk_pattern_keys.split(",") if k.strip()]

    if args.graph_bundle:
        bundle = load_json(args.graph_bundle)
        for rp in bundle.get("graph", {}).get("risk_patterns", []):
            pk = rp.get("pattern_key")
            if pk and pk not in keys:
                keys.append(pk)

    cwe_results = [lookup_cwe(table, c) for c in cwes]
    pattern_results = [lookup_risk_pattern(table, k) for k in keys]

    all_techniques: dict[str, None] = {}
    for r in cwe_results + pattern_results:
        for t in r.get("attack_techniques", []):
            all_techniques[t] = None

    output = {
        "source_map": str(map_path),
        "map_confidence_note": table.get("_confidence_note", ""),
        "cwe_results": cwe_results,
        "risk_pattern_results": pattern_results,
        "all_attack_techniques": list(all_techniques),
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} ({len(cwe_results)} CWE lookups, {len(pattern_results)} risk-pattern lookups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
