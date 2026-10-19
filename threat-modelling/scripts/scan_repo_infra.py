#!/usr/bin/env python3
"""
Repo Context Agent helper: infrastructure-as-code config scan
(SKILL.md Sec 2.1).

One of exactly three scripts permitted to touch a user-provided source
repository path (see SKILL.md Sec 5's repository exception). Scans
Dockerfiles, docker-compose files, and Kubernetes manifests for a small,
fixed set of line-level patterns (no root user declared, privileged mode,
host networking, broad port exposure, missing non-root/service-account
hardening). This is plain text/line scanning, not a YAML/Dockerfile
parser -- it is deliberately simple so it has no third-party dependency
and degrades to "pattern not found" rather than crashing on unusual syntax.

Findings reuse the same pattern_key/severity shape as
build_graph.py's risk_patterns so they fold into the same review step
instead of inventing a third findings format.

Usage:
    python scan_repo_infra.py --repo-root C:/path/to/repo --out infra_scan.json
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import save_json, utc_now_iso, eprint

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "vendor"}
MAX_FILE_BYTES = 500_000

DOCKERFILE_NAMES = re.compile(r'(^|[/\\])Dockerfile(\.[A-Za-z0-9_\-]+)?$')
COMPOSE_NAMES = re.compile(r'docker-compose(\.[A-Za-z0-9_\-]+)?\.ya?ml$')
K8S_HINT = re.compile(r'^\s*kind:\s*(Deployment|Pod|DaemonSet|StatefulSet|ReplicaSet)\s*$', re.MULTILINE)


def iter_candidate_files(repo_root: Path):
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.stat().st_size > MAX_FILE_BYTES:
            continue
        if DOCKERFILE_NAMES.search(p.name) or COMPOSE_NAMES.search(p.name) or p.suffix in (".yaml", ".yml"):
            yield p


def scan_dockerfile(path: Path, rel: str, findings: list[dict]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    has_user = any(re.match(r'^\s*USER\s+(?!root\b)', l, re.IGNORECASE) for l in lines)
    if not has_user:
        findings.append({
            "pattern_key": "container_no_non_root_user",
            "title": f"{rel} does not declare a non-root USER",
            "description": "No 'USER <non-root>' instruction found; the container likely runs as root by default, "
                            "widening the blast radius of any code-execution vulnerability inside it.",
            "severity": "Medium",
            "evidence": [f"REPO:{rel}"],
        })
    for i, line in enumerate(lines):
        m = re.search(r'^\s*EXPOSE\s+([\d\s]+)', line, re.IGNORECASE)
        if m:
            findings.append({
                "pattern_key": "container_port_exposed",
                "title": f"{rel}:{i + 1} exposes port(s) {m.group(1).strip()}",
                "description": "Documented for cross-reference against the architecture model's internet_exposed "
                                "fields -- an EXPOSEd port is not necessarily internet-facing, that depends on "
                                "orchestration/network config.",
                "severity": "Informational",
                "evidence": [f"REPO:{rel}:{i + 1}"],
            })
        if re.search(r'^\s*(ADD|COPY)\s+.*(\.env\b|\.pem\b|credentials\.json|id_rsa\b)', line, re.IGNORECASE):
            findings.append({
                "pattern_key": "container_bakes_in_secret_like_file",
                "title": f"{rel}:{i + 1} copies a secret-like file into the image",
                "description": "A file matching a common secrets filename pattern is copied into the image layer. "
                                "Image layers are often more widely distributed/cached than intended.",
                "severity": "High",
                "evidence": [f"REPO:{rel}:{i + 1}", line.strip()[:200]],
            })


def scan_compose_or_k8s(path: Path, rel: str, findings: list[dict]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    is_k8s_workload = bool(K8S_HINT.search(text))

    for i, line in enumerate(lines):
        if re.search(r'^\s*privileged:\s*true', line, re.IGNORECASE):
            findings.append({
                "pattern_key": "privileged_container_or_pod",
                "title": f"{rel}:{i + 1} sets privileged: true",
                "description": "A privileged container/pod has near-host-equivalent capabilities; a compromise "
                                "inside it can escalate to the host.",
                "severity": "Critical",
                "evidence": [f"REPO:{rel}:{i + 1}"],
            })
        if re.search(r'^\s*(network_mode|hostNetwork):\s*(host|true)', line, re.IGNORECASE):
            findings.append({
                "pattern_key": "host_network_enabled",
                "title": f"{rel}:{i + 1} enables host networking",
                "description": "The container/pod shares the host's network namespace, bypassing normal "
                                "container network isolation.",
                "severity": "High",
                "evidence": [f"REPO:{rel}:{i + 1}"],
            })
        m = re.search(r'^\s*-?\s*"?0\.0\.0\.0:(\d+):(\d+)"?', line)
        if m:
            findings.append({
                "pattern_key": "container_port_exposed",
                "title": f"{rel}:{i + 1} binds a port to 0.0.0.0 ({m.group(1)}->{m.group(2)})",
                "description": "Binding to 0.0.0.0 (vs 127.0.0.1) makes the port reachable from outside the host "
                                "if the host itself is network-reachable -- cross-reference with the architecture "
                                "model's internet_exposed field for this component.",
                "severity": "Medium",
                "evidence": [f"REPO:{rel}:{i + 1}"],
            })

    if is_k8s_workload:
        if not re.search(r'serviceAccountName:', text):
            findings.append({
                "pattern_key": "kubernetes_workload_undocumented_identity",
                "title": f"{rel} does not set serviceAccountName",
                "description": "No explicit serviceAccountName found; the workload likely uses the namespace's "
                                "default service account, which commonly carries broader permissions than needed.",
                "severity": "Medium",
                "evidence": [f"REPO:{rel}"],
            })
        if not re.search(r'runAsNonRoot:\s*true', text):
            findings.append({
                "pattern_key": "container_no_non_root_user",
                "title": f"{rel} does not set runAsNonRoot: true",
                "description": "No pod/container securityContext.runAsNonRoot found.",
                "severity": "Low",
                "evidence": [f"REPO:{rel}"],
            })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", required=True, help="Path to the repository root (read-only)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        eprint(f"error: not a directory: {repo_root}")
        return 1

    findings: list[dict] = []
    files_scanned = 0

    for path in iter_candidate_files(repo_root):
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        files_scanned += 1
        try:
            if DOCKERFILE_NAMES.search(path.name):
                scan_dockerfile(path, rel, findings)
            else:
                scan_compose_or_k8s(path, rel, findings)
        except OSError:
            continue

    for i, f in enumerate(findings, start=1):
        f["id"] = f"REPOINFRA-{i:03d}"

    output = {
        "generated_at": utc_now_iso(),
        "repo_root": str(repo_root),
        "files_scanned": files_scanned,
        "note": (
            "Plain line-pattern scan of Dockerfiles/compose/Kubernetes manifests, not a validating "
            "parser -- treat findings as candidates (Low/Medium confidence) to confirm, not confirmed facts. "
            "pattern_key values overlap build_graph.py's risk_patterns vocabulary where the concept matches."
        ),
        "findings": findings,
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} ({files_scanned} file(s) scanned, {len(findings)} finding(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
