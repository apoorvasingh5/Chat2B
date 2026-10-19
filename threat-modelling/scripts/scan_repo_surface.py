#!/usr/bin/env python3
"""
Repo Context Agent helper: generic entry-point + authorization-presence
scan (SKILL.md Sec 2.1).

One of the scripts permitted to touch a user-provided source repository
path (see SKILL.md Sec 5's repository exception). This engine has NO
framework-specific code. Every framework/protocol it recognizes -- REST
routes, MCP tools, gRPC methods, GraphQL resolvers, message consumers, CLI
commands, scheduled jobs, serverless handlers -- is a data-driven pattern
in references/repo-patterns/entrypoint-patterns.json. Supporting a new
ecosystem tomorrow (another RPC framework, a new queue library, whatever)
means adding a row to that JSON file, never adding branching logic here.
See that file's own `_extend_instructions`.

For each matched entry point, a generic (also framework-agnostic)
authorization/ownership-keyword window check runs, and a generic
"needs_deep_dive" heuristic flags entries worth a closer, model-driven look
via scripts/read_repo_snippet.py (sensitive-sounding name + no auth keyword
found) -- this script only ever emits small structured facts with file:line
citations, never file contents beyond the single matched line.

Usage:
    python scan_repo_surface.py --repo-root C:/path/to/repo --out surface_scan.json
    python scan_repo_surface.py --repo-root C:/path/to/repo --manifest manifest_scan.json --out surface_scan.json
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import load_json, save_json, utc_now_iso, eprint

PATTERNS_DIR = Path(__file__).resolve().parent.parent / "references" / "repo-patterns"
DEFAULT_REGISTRIES = [
    PATTERNS_DIR / "entrypoint-patterns.json",
    PATTERNS_DIR / "code-risk-patterns.json",
]

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__", "dist",
    "build", "target", "vendor", ".tox", "bin", "obj", ".idea", ".vscode",
    "coverage", ".mypy_cache", ".pytest_cache", "test", "tests", "__tests__",
    "spec",
}

EXTENSIONS = {".py": "Python", ".js": "JavaScript", ".ts": "JavaScript",
              ".java": "Java", ".cs": "CSharp", ".go": "Go", ".rb": "Ruby", ".php": "PHP"}

MAX_FILE_BYTES = 1_000_000

AUTH_KEYWORDS = re.compile(
    r'login_required|permission_classes|IsAuthenticated|jwt_required|require_auth'
    r'|@PreAuthorize|@Secured|\[Authorize\]|authenticate\(|requireAuth|ensureAuthenticated'
    r'|AuthorizationFilter|@RolesAllowed|current_user\.|request\.user\.',
    re.IGNORECASE,
)

OWNERSHIP_KEYWORDS = re.compile(
    r'user_id\s*==|\.owner\b|\.user_id\b|current_user\.id|ownership|belongs_to', re.IGNORECASE
)


def load_registries(paths: list[Path]) -> dict:
    """Loads and merges one or more pattern registry JSON files. Each
    contributes its own 'patterns' (and, where present, its own
    'sensitive_action_keywords'), so a new concern -- entry points, insecure
    config toggles, outbound-dependency hints, whatever comes next -- can
    live in its own file without the engine caring which file a pattern
    came from."""
    compiled: list[dict] = []
    sensitive_keywords: set[str] = set()
    sources: list[str] = []
    for path in paths:
        registry = load_json(path)
        sources.append(str(path))
        sensitive_keywords.update(k.lower() for k in registry.get("sensitive_action_keywords", []))
        for p in registry["patterns"]:
            fields = {}
            for name, spec in p.get("fields", {}).items():
                field = dict(spec)
                if "regex" in field:
                    flags = re.MULTILINE if field.get("multiline") else 0
                    field["_compiled"] = re.compile(field["regex"], flags)
                fields[name] = field
            compiled.append({
                **p,
                "_source": str(path),
                "_anchor": re.compile(p["anchor_regex"]),
                "_fields": fields,
            })
    return {
        "_compiled_patterns": compiled,
        "_sources": sources,
        "sensitive_action_keywords": sorted(sensitive_keywords),
    }


def pattern_is_relevant(pattern: dict, detected_deps_lower: set[str] | None) -> bool:
    hints = pattern.get("dependency_hints")
    if not hints or detected_deps_lower is None:
        return True  # no manifest supplied, or pattern applies unconditionally: favor recall
    return any(any(hint in dep for dep in detected_deps_lower) for hint in hints)


def load_detected_dependencies(manifest_path: str | None) -> set[str] | None:
    if not manifest_path:
        return None
    data = load_json(manifest_path)
    deps: set[str] = set()
    for m in data.get("manifests_found", []):
        deps.update(d.lower() for d in m.get("dependencies", []))
    deps.update(f.lower() for f in data.get("frameworks_detected", []))
    return deps


def extract_field(field: dict, anchor_match: "re.Match", window: str, window_lines: list[str]) -> str | None:
    value = None
    if "group" in field:
        try:
            value = anchor_match.group(field["group"])
        except IndexError:
            value = None
    elif "_compiled" in field:
        m = field["_compiled"].search(window)
        if m:
            value = m.group(1) if m.groups() else m.group(0)
    if value is not None and field.get("upper"):
        value = value.upper().strip("[]") if value else value
    return value.strip() if isinstance(value, str) else value


def iter_candidate_files(repo_root: Path) -> list[Path]:
    """Scans files whose extension is in EXTENSIONS. Patterns with
    language=None (universal) still only apply within this same file set --
    a deliberate scope bound, not every file in the repo gets regex-scanned."""
    out = []
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix not in EXTENSIONS:
            continue
        out.append(p)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", required=True, help="Path to the repository root (read-only)")
    parser.add_argument("--registry", nargs="+", default=[str(p) for p in DEFAULT_REGISTRIES],
                         help="Path(s) to pattern registry JSON file(s) (extend these, not this script, for new "
                              "frameworks/protocols/config-risk patterns). Default: all registries under "
                              "references/repo-patterns/.")
    parser.add_argument("--manifest", default=None,
                         help="scan_repo_manifest.py output; used to skip patterns whose dependency_hints don't match "
                              "(precision optimization). Omit to apply every pattern regardless of detected deps.")
    parser.add_argument("--max-files", type=int, default=5000,
                         help="Safety cap on files scanned; stops and warns rather than running unbounded (default 5000)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        eprint(f"error: not a directory: {repo_root}")
        return 1

    registry = load_registries([Path(p) for p in args.registry])
    detected_deps = load_detected_dependencies(args.manifest)
    sensitive_keywords = registry["sensitive_action_keywords"]

    active_patterns = [p for p in registry["_compiled_patterns"] if pattern_is_relevant(p, detected_deps)]
    active_ids = {id(p) for p in active_patterns}
    skipped_patterns = [p["id"] for p in registry["_compiled_patterns"] if id(p) not in active_ids]

    entry_points = []
    files_scanned = 0
    truncated = False

    for path in iter_candidate_files(repo_root):
        if files_scanned >= args.max_files:
            truncated = True
            break
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        files_scanned += 1
        lang = EXTENSIONS[path.suffix]
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = str(path.relative_to(repo_root)).replace("\\", "/")

        for pattern in active_patterns:
            if pattern.get("language") not in (None, lang):
                continue
            window_size = pattern.get("window_lines", 1)
            for i, line in enumerate(lines):
                m = pattern["_anchor"].search(line)
                if not m:
                    continue
                window_lines = lines[i:min(i + window_size, len(lines))]
                window = "\n".join(window_lines)

                fields = {}
                for fname, fspec in pattern.get("_fields", {}).items():
                    fields[fname] = extract_field(fspec, m, window, window_lines)

                has_auth = bool(AUTH_KEYWORDS.search(window))
                has_ownership_check = bool(OWNERSHIP_KEYWORDS.search(window))

                haystack = (" ".join(str(v) for v in fields.values() if v) + " " + path.parent.name).lower()
                looks_sensitive = any(k in haystack for k in sensitive_keywords)
                needs_deep_dive = looks_sensitive and not has_auth

                entry_points.append({
                    "kind": pattern["kind"],
                    "pattern_id": pattern["id"],
                    "file": rel,
                    "line": i + 1,
                    "language": lang,
                    "module": path.parent.name,
                    "fields": fields,
                    "authorization_check": "Yes" if has_auth else "Unknown",
                    "ownership_check_heuristic": "Yes" if has_ownership_check else "Unknown",
                    "needs_deep_dive": needs_deep_dive,
                    "source_ref": f"REPO:{rel}:{i + 1}",
                })

    module_groups: dict[str, list[str]] = {}
    for ep in entry_points:
        module_groups.setdefault(ep["module"], []).append(ep["source_ref"])

    kind_counts: dict[str, int] = {}
    for ep in entry_points:
        kind_counts[ep["kind"]] = kind_counts.get(ep["kind"], 0) + 1

    output = {
        "generated_at": utc_now_iso(),
        "repo_root": str(repo_root),
        "registries_used": list(args.registry),
        "manifest_used": args.manifest,
        "active_pattern_ids": [p["id"] for p in active_patterns],
        "skipped_pattern_ids_no_matching_dependency": skipped_patterns,
        "files_scanned": files_scanned,
        "truncated": truncated,
        "note": (
            "Heuristic regex match against a data-driven pattern registry, not a parser -- high recall, low "
            "precision by design. authorization_check is 'Yes' only if an auth-looking keyword appeared within "
            "the pattern's window; 'Unknown' is NOT evidence of a missing check. needs_deep_dive flags entries "
            "worth a bounded, cited look via scripts/read_repo_snippet.py -- it is a prioritization hint, not a "
            "finding. Zero entry_points of a given kind usually means no pattern for that repo's actual framework "
            "exists yet in references/repo-patterns/entrypoint-patterns.json (extend it) rather than 'no endpoints.'"
            + (" WARNING: --max-files limit reached; results are incomplete." if truncated else "")
        ),
        "kind_counts": kind_counts,
        "module_groups": module_groups,
        "entry_points": entry_points,
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} ({files_scanned} file(s) scanned, {len(entry_points)} entry point(s), kinds: {kind_counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
