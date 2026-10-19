#!/usr/bin/env python3
"""
Repo Context Agent helper: dependency manifest scan (SKILL.md Sec 2.1).

This is one of exactly three scripts permitted to touch a user-provided
source repository path (see SKILL.md Sec 5's repository exception). It
walks the repo for dependency-manifest files only, extracts language and
named dependencies, and emits small structured JSON with file:line/file
citations -- it never emits full file contents, and the model must not
open or grep repo files itself; this script is the only reader.

Usage:
    python scan_repo_manifest.py --repo-root C:/path/to/repo --out manifest_scan.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import save_json, utc_now_iso, eprint

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__", "dist",
    "build", "target", "vendor", ".tox", "bin", "obj", ".idea", ".vscode",
    "coverage", ".mypy_cache", ".pytest_cache", "site-packages",
}

MAX_FILE_BYTES = 2_000_000  # manifests are never legitimately larger than this

MANIFEST_RULES = [
    ("package.json", "JavaScript"),
    ("requirements.txt", "Python"),
    ("pyproject.toml", "Python"),
    ("Pipfile", "Python"),
    ("pom.xml", "Java"),
    ("build.gradle", "Java"),
    ("build.gradle.kts", "Java"),
    ("go.mod", "Go"),
    ("Gemfile", "Ruby"),
    ("composer.json", "PHP"),
]

FRAMEWORK_KEYWORDS = (
    "express", "flask", "fastapi", "django", "spring", "spring-boot",
    "next", "react", "vue", "angular", "nestjs", "rails", "laravel",
    "gin", "echo", "fiber", "aspnetcore", "actix", "koa",
)


def iter_repo_files(repo_root: Path):
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def extract_json_dependency_names(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return []
    names: list[str] = []
    for key in ("dependencies", "devDependencies", "require", "require-dev"):
        section = data.get(key)
        if isinstance(section, dict):
            names.extend(section.keys())
    return names


def extract_requirements_names(path: Path) -> list[str]:
    names = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            m = re.match(r"^([A-Za-z0-9_.\-]+)", line)
            if m:
                names.append(m.group(1))
    except OSError:
        pass
    return names


def extract_simple_name_list(path: Path, pattern: str) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return re.findall(pattern, text, re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", required=True, help="Path to the repository root (read-only)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        eprint(f"error: not a directory: {repo_root}")
        return 1

    manifests_found = []
    languages: dict[str, int] = {}
    frameworks_seen: set[str] = set()

    for path in iter_repo_files(repo_root):
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        name = path.name
        rule = next((lang for fname, lang in MANIFEST_RULES if fname == name), None)
        if not rule:
            continue

        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        if name == "package.json":
            deps = extract_json_dependency_names(path)
        elif name in ("requirements.txt",):
            deps = extract_requirements_names(path)
        elif name == "pyproject.toml":
            deps = extract_simple_name_list(path, r'^([A-Za-z0-9_.\-]+)\s*=', )
        elif name == "go.mod":
            deps = extract_simple_name_list(path, r'^\s*([\w.\-]+(?:/[\w.\-]+)+)\s+v[\d.]')
        elif name == "Gemfile":
            deps = extract_simple_name_list(path, r'gem\s+["\']([A-Za-z0-9_\-]+)["\']')
        elif name == "composer.json":
            deps = extract_json_dependency_names(path)
        elif name in ("pom.xml",):
            deps = extract_simple_name_list(path, r'<artifactId>([A-Za-z0-9_.\-]+)</artifactId>')
        elif name in ("build.gradle", "build.gradle.kts"):
            deps = extract_simple_name_list(path, r'[\'"]([a-zA-Z0-9_.\-]+:[a-zA-Z0-9_.\-]+):[\d.]+[\'"]')
        else:
            deps = []

        deps = sorted(set(deps))[:200]  # bound output size on pathological manifests
        for dep in deps:
            low = dep.lower()
            for fw in FRAMEWORK_KEYWORDS:
                if fw in low:
                    frameworks_seen.add(fw)

        languages[rule] = languages.get(rule, 0) + 1
        manifests_found.append({
            "file": rel,
            "language": rule,
            "dependency_count": len(deps),
            "dependencies": deps,
            "source_ref": f"REPO:{rel}",
        })

    output = {
        "generated_at": utc_now_iso(),
        "repo_root": str(repo_root),
        "note": (
            "Deterministic manifest scan only -- no source code was read beyond manifest files "
            "listed above. Treat 'languages'/'frameworks_detected' as candidates for "
            "technology_profile, confidence Low until corroborated."
        ),
        "manifests_found": manifests_found,
        "languages_detected": sorted(languages, key=lambda k: -languages[k]),
        "frameworks_detected": sorted(frameworks_seen),
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} ({len(manifests_found)} manifest(s), {len(languages)} language(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
