"""
Shared utilities for the Threat Modelling pipeline scripts.

Every script in scripts/ (parse_markdown, parse_html, parse_pdf,
normalize_entities, build_graph, export_report) imports this module.
It intentionally has zero third-party dependencies so the pipeline keeps
working even in minimal Python environments; optional-dependency scripts
degrade gracefully instead of hard-failing.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"

CONFIDENCE_VALUES = ("High", "Medium", "Low")
YES_NO_UNKNOWN = ("Yes", "No", "Unknown")

NODE_TYPES = (
    "Actor", "UserGroup", "Application", "WebApplication", "MobileApplication",
    "BackendService", "Microservice", "API", "APIGateway", "Database",
    "DataStore", "ObjectStorage", "MessageQueue", "EventStream",
    "IdentityProvider", "AuthorizationServer", "SecretStore", "CloudResource",
    "Container", "KubernetesCluster", "Function", "NetworkZone",
    "TrustBoundary", "ThirdPartyService", "AdminInterface", "CICDPipeline",
    "SourceCodeRepository", "SASTTool", "DASTTool", "MonitoringSystem",
    "LoggingSystem", "LLMApplication", "LLMModel", "VectorDatabase",
    "AgentTool", "Other",
)

RELATIONSHIP_TYPES = (
    "USES", "CALLS", "READS_FROM", "WRITES_TO", "AUTHENTICATES_WITH",
    "AUTHORIZES_WITH", "HOSTED_ON", "DEPLOYED_BY", "STORES_SECRET_IN",
    "USES_SECRET", "SENDS_DATA_TO", "RECEIVES_DATA_FROM",
    "TRAVERSES_TRUST_BOUNDARY", "EXPOSED_TO", "ADMINISTERS", "LOGS_TO",
    "MONITORED_BY", "SCANNED_BY", "DEPENDS_ON", "RETRIEVES_FROM",
    "WRITES_MEMORY_TO", "CALLS_TOOL", "OTHER",
)

SENSITIVE_DATA_MARKERS = (
    "pii", "personal", "payment", "card", "cvv", "credential", "password",
    "secret", "token", "session", "health", "phi", "financial", "ssn",
    "national id", "biometric", "confidential",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text_file(path: str | Path) -> str:
    """Read a text file, tolerating BOM and non-UTF8 bytes."""
    p = Path(path)
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path | None) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if path is None or str(path) == "-":
        sys.stdout.write(text + "\n")
    else:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")


def load_json_or_multiple(paths: Iterable[str | Path]) -> list[Any]:
    """Load one or more JSON files, accepting either a single object or a
    list of objects per file, and flatten into a list of objects."""
    out: list[Any] = []
    for p in paths:
        data = load_json(p)
        if isinstance(data, list):
            out.extend(data)
        else:
            out.append(data)
    return out


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def normalize_key(name: str) -> str:
    """Collapse a display name into a comparable dedupe key."""
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def normalize_enum(value: Any, allowed: Iterable[str], default: str = "Unknown") -> str:
    if value is None:
        return default
    value = str(value).strip()
    if not value:
        return default
    for candidate in allowed:
        if value.lower() == candidate.lower():
            return candidate
    return default if default in allowed or default == "Unknown" else value


def is_sensitive_classification(classifications: Iterable[str]) -> bool:
    joined = " ".join(classifications or []).lower()
    return any(marker in joined for marker in SENSITIVE_DATA_MARKERS)


class IdAllocator:
    """Generates stable, gap-free canonical IDs for a given prefix
    (e.g. C-001, DF-001), continuing from the highest existing ID so that
    re-running normalize/build steps on partially-ID'd input doesn't
    collide with previously assigned IDs."""

    def __init__(self, prefix: str, existing: Iterable[str] = ()):
        self.prefix = prefix
        self._next = 1
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
        for item in existing:
            m = pattern.match(item or "")
            if m:
                self._next = max(self._next, int(m.group(1)) + 1)

    def next(self) -> str:
        value = f"{self.prefix}-{self._next:03d}"
        self._next += 1
        return value


def eprint(*args: Any, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)
