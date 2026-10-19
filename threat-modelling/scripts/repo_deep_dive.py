#!/usr/bin/env python3
"""
Repo Context Agent harness (SKILL.md Sec 2.1).

Orchestrates the three deterministic repo-scan scripts
(scan_repo_manifest.py, scan_repo_surface.py, scan_repo_infra.py), then
consolidates their output into ONE repo_insights.json bundle -- the single
artifact that feeds Architecture Extraction (SKILL.md Sec 3), the same way
one parse_markdown.py output feeds it for a document. Running the three
scripts separately and expecting the model to remember to reconcile all
three by hand is exactly how information gets silently dropped; this
harness's job is to make dropping something require actively ignoring a
field in one file, not forgetting a step.

It also computes an explicit coverage/gap report: zero entry points found,
zero manifests found, zero infra config found, etc. are all reported as
named gaps rather than silently producing a thin result that looks
complete. "We found nothing" and "we didn't look in the right place" must
never look the same.

This harness does NOT itself read file contents beyond what the three
scripts already extract (same restriction as each of them -- see SKILL.md
Sec 5's repository exception). For entries flagged needs_deep_dive: true,
follow up with scripts/read_repo_snippet.py yourself, selectively, per
SKILL.md Sec 2.1 -- this harness only tells you where to look, consistent
with "scripts find candidates, the model reasons about what they mean"
used everywhere else in this skill (build_graph.py's risk patterns,
analyze_workflows.py's workflow_risk_patterns).

Usage:
    python repo_deep_dive.py --repo-root C:/path/to/repo --artifacts-dir artifacts --out artifacts/repo_insights.json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import load_json, save_json, utc_now_iso, eprint

SCRIPTS_DIR = Path(__file__).resolve().parent


def run_script(name: str, args: list[str]) -> dict:
    cmd = [sys.executable, str(SCRIPTS_DIR / name), *args, "--out", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        eprint(f"error running {name}: {proc.stderr.strip()}")
        return {"_error": proc.stderr.strip(), "_script": name}
    try:
        import json
        return json.loads(proc.stdout)
    except ValueError as e:
        eprint(f"error parsing {name} output: {e}")
        return {"_error": str(e), "_script": name}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", required=True, help="Path to the repository root (read-only)")
    parser.add_argument("--artifacts-dir", default="artifacts",
                         help="Directory to also write the three raw per-script outputs into, for traceability (default: artifacts/)")
    parser.add_argument("--out", default="-", help="Output JSON path for the consolidated repo_insights.json, or '-' for stdout")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        eprint(f"error: not a directory: {repo_root}")
        return 1

    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    manifest = run_script("scan_repo_manifest.py", ["--repo-root", str(repo_root)])
    save_json(manifest, artifacts_dir / "repo-manifest.json")

    manifest_path = artifacts_dir / "repo-manifest.json"
    surface = run_script("scan_repo_surface.py", ["--repo-root", str(repo_root), "--manifest", str(manifest_path)])
    save_json(surface, artifacts_dir / "repo-surface.json")

    infra = run_script("scan_repo_infra.py", ["--repo-root", str(repo_root)])
    save_json(infra, artifacts_dir / "repo-infra.json")

    gaps: list[str] = []

    if manifest.get("_error"):
        gaps.append(f"scan_repo_manifest.py failed: {manifest['_error']}")
    elif not manifest.get("manifests_found"):
        gaps.append(
            "No dependency manifest found anywhere in the repo. Language/framework detection is "
            "unavailable from this scan; confirm the tech stack with the user or a document."
        )

    entry_points = surface.get("entry_points", [])
    if surface.get("_error"):
        gaps.append(f"scan_repo_surface.py failed: {surface['_error']}")
    elif not entry_points:
        gaps.append(
            "Zero entry points matched any registered pattern. This does NOT mean the system has no "
            "endpoints/tools/handlers -- it means none of the patterns in "
            "references/repo-patterns/entrypoint-patterns.json matched. Check active_pattern_ids / "
            "skipped_pattern_ids_no_matching_dependency in repo-surface.json: if the real framework isn't "
            "represented, extend the pattern registry (data change) rather than concluding 'no surface.'"
        )
    if surface.get("truncated"):
        gaps.append("scan_repo_surface.py hit --max-files and stopped early; results are incomplete.")

    needs_deep_dive = [ep for ep in entry_points if ep.get("needs_deep_dive")]

    if infra.get("_error"):
        gaps.append(f"scan_repo_infra.py failed: {infra['_error']}")
    elif infra.get("files_scanned", 0) == 0:
        gaps.append(
            "No Dockerfile/compose/Kubernetes manifest found in the repo. Deployment topology "
            "(internet-exposed? which network zone?) is not determinable from this repo alone -- "
            "record it as an open question rather than assuming either way."
        )

    candidate_workflow_families = {
        module: refs for module, refs in surface.get("module_groups", {}).items() if len(refs) >= 2
    }

    output = {
        "generated_at": utc_now_iso(),
        "repo_root": str(repo_root),
        "scripts_run": ["scan_repo_manifest.py", "scan_repo_surface.py", "scan_repo_infra.py"],
        "raw_outputs": {
            "manifest": str(artifacts_dir / "repo-manifest.json"),
            "surface": str(artifacts_dir / "repo-surface.json"),
            "infra": str(artifacts_dir / "repo-infra.json"),
        },
        "technology_profile_candidate": {
            "languages": manifest.get("languages_detected", []),
            "frameworks": manifest.get("frameworks_detected", []),
        },
        "entry_points": entry_points,
        "entry_point_kind_counts": surface.get("kind_counts", {}),
        "candidate_workflow_families": candidate_workflow_families,
        "needs_deep_dive_entries": needs_deep_dive,
        "infra_findings": infra.get("findings", []),
        "coverage_report": {
            "manifests_found": len(manifest.get("manifests_found", [])),
            "entry_points_found": len(entry_points),
            "infra_files_scanned": infra.get("files_scanned", 0),
            "needs_deep_dive_count": len(needs_deep_dive),
            "gaps": gaps,
        },
        "note": (
            "Consolidated, deterministic repo evidence only. Every field here is a candidate fact "
            "(Low confidence by default) with REPO:<file>:<line> citations in the underlying raw_outputs "
            "files -- confirm, merge with document-derived facts, and correct per SKILL.md Sec 3. For "
            "needs_deep_dive_entries, use scripts/read_repo_snippet.py for a bounded, audited, cited look "
            "before writing a threat about them -- do not reason from the entry's name/title alone if the "
            "action sounds sensitive enough to warrant checking."
        ),
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(
            f"wrote {args.out} ({len(entry_points)} entry points, {len(needs_deep_dive)} flagged for deep dive, "
            f"{len(gaps)} coverage gap(s))"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
