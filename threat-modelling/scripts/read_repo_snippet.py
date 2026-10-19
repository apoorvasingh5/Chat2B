#!/usr/bin/env python3
"""
Repo Context Agent helper: bounded, audited source-snippet reader
(SKILL.md Sec 2.1 "AI-native deep dive").

The deterministic scripts (scan_repo_manifest.py, scan_repo_surface.py,
scan_repo_infra.py) find WHERE something interesting is (file:line) but
cannot judge WHAT it means -- that needs the model's actual reasoning,
same as everywhere else in this skill. This script is the one narrow,
controlled channel for that: it returns a small, bounded window of real
source text around a specific, already-cited file:line, so the model can
read and reason about ambiguous or sensitive-looking entries
(scan_repo_surface.py's needs_deep_dive: true) WITHOUT gaining general
Read/Grep/Glob access to the repository.

Guardrails enforced IN CODE, not by instruction alone:
  - The resolved file must stay inside --repo-root (blocks ../ escapes).
  - The returned window is hard-capped at --max-lines (default 60), even
    if a larger --context is requested.
  - Filenames matching common secret patterns (.env, *.pem, id_rsa,
    credentials*, *.key, *.p12) are refused outright -- never returned,
    regardless of reason.
  - Every call is required to carry --reason and is appended to
    --log-file (default: <repo-root>/.threat-modelling-snippet-log.jsonl)
    so there is a complete, reviewable audit trail of every piece of
    source text the model ever looked at and why. This is what makes a
    handful of targeted reads auditable instead of being indistinguishable
    from unrestricted file access.

This script returns real file content -- unlike the other three repo
scripts, which never do. Use it sparingly and only for entries the
deterministic scan already flagged as worth a closer look, one call per
entry, not as a substitute for them.

Usage:
    python read_repo_snippet.py --repo-root C:/path/to/repo \\
        --file pkg/modules/cxone/delete_project_module.go --line 40 \\
        --context 20 --reason "needs_deep_dive: DeleteProjectToolName, no auth keyword found nearby"
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from common import eprint

SECRET_FILENAME_PATTERNS = re.compile(
    r'\.env($|\.)|\.pem$|\.key$|\.p12$|\.pfx$|id_rsa|id_dsa|id_ecdsa|id_ed25519'
    r'|credentials\.(json|ya?ml)$|\.npmrc$|\.netrc$|secrets?\.(ya?ml|json)$',
    re.IGNORECASE,
)

MAX_LINES_HARD_CAP = 200
MAX_FILE_BYTES = 2_000_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", required=True, help="Repository root; the requested file must resolve inside it")
    parser.add_argument("--file", required=True, help="Path to the file, relative to --repo-root")
    parser.add_argument("--line", type=int, required=True, help="1-based line number to center the window on")
    parser.add_argument("--context", type=int, default=20,
                         help="Lines of context before/after --line (default 20; hard-capped, see --max-lines)")
    parser.add_argument("--max-lines", type=int, default=60,
                         help=f"Hard cap on total lines returned, enforced regardless of --context (default 60, max {MAX_LINES_HARD_CAP})")
    parser.add_argument("--reason", required=True,
                         help="Why this snippet is needed (e.g. which needs_deep_dive entry/question this answers). Logged, not optional.")
    parser.add_argument("--log-file", default=None,
                         help="Audit log path (default: <repo-root>/.threat-modelling-snippet-log.jsonl)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        eprint(f"error: not a directory: {repo_root}")
        return 1

    max_lines = min(args.max_lines, MAX_LINES_HARD_CAP)

    requested = (repo_root / args.file).resolve()
    try:
        requested.relative_to(repo_root)
    except ValueError:
        eprint(f"error: refused -- '{args.file}' resolves outside --repo-root")
        return 2

    if SECRET_FILENAME_PATTERNS.search(requested.name):
        eprint(f"error: refused -- '{args.file}' matches a secret-like filename pattern; never returned")
        return 3

    if not requested.is_file():
        eprint(f"error: not a file: {requested}")
        return 1

    if requested.stat().st_size > MAX_FILE_BYTES:
        eprint(f"error: refused -- file exceeds {MAX_FILE_BYTES} bytes, too large for a bounded snippet read")
        return 4

    lines = requested.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)
    context = min(args.context, max_lines // 2)
    start = max(1, args.line - context)
    end = min(total, args.line + context)
    if end - start + 1 > max_lines:
        end = start + max_lines - 1

    rel = str(requested.relative_to(repo_root)).replace("\\", "/")
    snippet_lines = [{"line": n, "text": lines[n - 1]} for n in range(start, end + 1)]

    log_path = Path(args.log_file) if args.log_file else repo_root / ".threat-modelling-snippet-log.jsonl"
    log_entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file": rel,
        "requested_line": args.line,
        "returned_range": [start, end],
        "reason": args.reason,
    }
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except OSError as e:
        eprint(f"warning: could not write audit log at {log_path}: {e}")

    result = {
        "file": rel,
        "source_ref": f"REPO:{rel}:{start}-{end}",
        "requested_line": args.line,
        "returned_range": [start, end],
        "total_lines_in_file": total,
        "reason": args.reason,
        "audit_log": str(log_path),
        "lines": snippet_lines,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
