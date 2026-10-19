#!/usr/bin/env python3
"""
Graph Builder Agent helper.

Consumes the output of normalize_entities.py and produces:

  1. `graph` -- an object that conforms to
     references/output-schemas/graph-schema.json (metadata + nodes + edges +
     risk_patterns). Node ids all use the schema-mandated "C-###" pattern
     (trust boundaries are attributes of nodes/edges -- trust_zone and
     crosses_trust_boundary -- not separate node ids), and edges reference
     resolved node ids rather than free-text names.
  2. Pass-through `trust_boundaries`, `security_controls`, and `unknowns`
     lists (from normalize_entities.py) for the report-writing step, which
     are not part of the strict graph schema.
  3. `business_workflows`, pass-through from normalize_entities.py but with
     each step's `component` (a free-text name) resolved into a canonical
     graph node id the same way data-flow endpoints are, so
     scripts/analyze_workflows.py can cross-reference a step's component
     against real graph edges (e.g. for its "reachable out of order" check).

Any data-flow endpoint that didn't match a known component is materialized
as an explicit low-confidence placeholder node (type "Other") with an
assumption noting it was auto-created -- never silently dropped, and never
given invented properties beyond "Unknown".

It also runs the SKILL.md "High-Risk Graph Patterns" detectors
algorithmically (reachability / attribute checks), which is deterministic
graph analysis and therefore better done in code than left to the model.

Usage:
    python build_graph.py normalized.json --system-name "Payment Platform" --out graph_bundle.json
    python build_graph.py normalized.json --source-artifacts src1.json src2.json --validate --out graph_bundle.json
"""

from __future__ import annotations

import argparse
from collections import deque
from typing import Callable

from common import (
    is_sensitive_classification, load_json, normalize_key, save_json,
    utc_now_iso, IdAllocator, eprint, SCHEMA_VERSION,
)

SENSITIVE_STORE_TYPES = {"Database", "DataStore", "ObjectStorage"}
MAX_BFS_HOPS = 6


def build_nodes(entities: dict) -> tuple[list[dict], dict[str, str], list[str]]:
    nodes = []
    name_index: dict[str, str] = dict(entities.get("name_index", {}))
    for comp in entities.get("components", []):
        node = {
            "id": comp["id"],
            "name": comp["name"],
            "type": comp.get("type", "Other"),
            "description": comp.get("description", ""),
            "technology": comp.get("technology", "Unknown"),
            "owner": comp.get("owner", "Unknown"),
            "environment": comp.get("environment", "Unknown"),
            "internet_exposed": comp.get("internet_exposed", "Unknown"),
            "authentication": comp.get("authentication", "Unknown"),
            "authorization": comp.get("authorization", "Unknown"),
            "data_classification": comp.get("data_classification", []),
            "trust_zone": comp.get("trust_zone", "Unknown"),
            "tags": comp.get("tags", []),
            "source_refs": comp.get("source_refs", []),
            "confidence": comp.get("confidence", "Low"),
            "assumptions": comp.get("assumptions", []),
        }
        nodes.append(node)
        name_index.setdefault(normalize_key(comp["name"]), comp["id"])

    placeholders_created: list[str] = []
    return nodes, name_index, placeholders_created


def resolve_or_create_placeholder(
    display_name: str, name_index: dict[str, str], nodes: list[dict],
    allocator: IdAllocator, placeholders_created: list[str],
) -> str:
    key = normalize_key(display_name)
    if key in name_index:
        return name_index[key]

    new_id = allocator.next()
    nodes.append({
        "id": new_id,
        "name": display_name,
        "type": "Other",
        "description": "",
        "technology": "Unknown",
        "owner": "Unknown",
        "environment": "Unknown",
        "internet_exposed": "Unknown",
        "authentication": "Unknown",
        "authorization": "Unknown",
        "data_classification": [],
        "trust_zone": "Unknown",
        "tags": ["auto-generated-placeholder"],
        "source_refs": [],
        "confidence": "Low",
        "assumptions": [
            "Auto-created placeholder node: referenced as a data-flow endpoint "
            "but not extracted as a distinct architecture component. Verify "
            "identity, type, and properties with the user before relying on this node."
        ],
    })
    name_index[key] = new_id
    placeholders_created.append(new_id)
    return new_id


def build_edges(entities: dict, name_index: dict[str, str], nodes: list[dict],
                 placeholders_created: list[str]) -> list[dict]:
    allocator = IdAllocator("C", [n["id"] for n in nodes])
    edges = []
    for flow in entities.get("data_flows", []):
        from_id = resolve_or_create_placeholder(flow["from_name"], name_index, nodes, allocator, placeholders_created)
        to_id = resolve_or_create_placeholder(flow["to_name"], name_index, nodes, allocator, placeholders_created)
        edges.append({
            "id": flow["id"],
            "from": from_id,
            "to": to_id,
            "relationship": flow.get("relationship", "OTHER"),
            "protocol": flow.get("protocol", "Unknown"),
            "port": flow.get("port", "Unknown"),
            "authentication": flow.get("authentication", "Unknown"),
            "authorization": flow.get("authorization", "Unknown"),
            "data_classification": flow.get("data_classification", []),
            "crosses_trust_boundary": flow.get("crosses_trust_boundary", "Unknown"),
            "encryption_in_transit": flow.get("encryption_in_transit", "Unknown"),
            "source_refs": flow.get("source_refs", []),
            "confidence": flow.get("confidence", "Low"),
            "assumptions": flow.get("assumptions", []),
        })
    return edges


def _bfs_first_path(start: str, is_target: Callable[[str], bool],
                     adjacency: dict[str, list[tuple[str, dict]]], max_hops: int = MAX_BFS_HOPS):
    visited = {start}
    queue = deque([(start, [], [])])
    while queue:
        current, path_nodes, path_edges = queue.popleft()
        if len(path_nodes) >= max_hops:
            continue
        for to_id, edge in adjacency.get(current, []):
            if to_id in visited:
                continue
            new_nodes = path_nodes + [to_id]
            new_edges = path_edges + [edge["id"]]
            if is_target(to_id):
                return new_nodes, new_edges
            visited.add(to_id)
            queue.append((to_id, new_nodes, new_edges))
    return None, None


def resolve_workflow_components(
    workflows: list[dict], name_index: dict[str, str], nodes: list[dict],
    allocator: IdAllocator, placeholders_created: list[str],
) -> list[dict]:
    """Resolve each workflow step's `component` (a free-text name from
    extraction/normalization, same convention as a data_flow's from_name/
    to_name) into the canonical graph node id, creating a placeholder node
    if it doesn't match an extracted component -- the same treatment
    resolve_or_create_placeholder already gives data-flow endpoints. This
    lets scripts/analyze_workflows.py's reachability check compare a step's
    component against real graph node ids instead of free text."""
    resolved = []
    for wf in workflows:
        wf = dict(wf)
        new_steps = []
        for step in wf.get("steps", []):
            step = dict(step)
            component_name = step.get("component")
            if component_name and component_name != "Unknown":
                step["component"] = resolve_or_create_placeholder(
                    component_name, name_index, nodes, allocator, placeholders_created
                )
            new_steps.append(step)
        wf["steps"] = new_steps
        resolved.append(wf)
    return resolved


def detect_risk_patterns(nodes: list[dict], edges: list[dict]) -> list[dict]:
    by_id = {n["id"]: n for n in nodes}
    adjacency: dict[str, list[tuple[str, dict]]] = {}
    for e in edges:
        adjacency.setdefault(e["from"], []).append((e["to"], e))

    findings: list[dict] = []

    def add(key, title, description, severity, node_ids=(), edge_ids=(), evidence=()):
        findings.append({
            "pattern_key": key,
            "title": title,
            "description": description,
            "severity": severity,
            "graph_refs": {"nodes": list(node_ids), "edges": list(edge_ids)},
            "evidence": list(evidence),
        })

    # 1. Internet-exposed entry point reaching a sensitive data store.
    for node in nodes:
        if node.get("internet_exposed") != "Yes":
            continue

        def is_sensitive_store(node_id: str) -> bool:
            target = by_id.get(node_id, {})
            return target.get("type") in SENSITIVE_STORE_TYPES and (
                is_sensitive_classification(target.get("data_classification", []))
                or not target.get("data_classification")
            )

        path_nodes, path_edges = _bfs_first_path(node["id"], is_sensitive_store, adjacency)
        if path_nodes:
            target = by_id[path_nodes[-1]]
            add(
                "internet_exposed_reaches_sensitive_store",
                f"Internet-exposed '{node['name']}' can reach data store '{target['name']}'",
                f"'{node['name']}' is marked internet-exposed and a forward data-flow path "
                f"reaches '{target['name']}' ({target['type']}) within {len(path_nodes)} hop(s). "
                "Verify authentication/authorization are enforced at every hop on this path.",
                "Critical" if is_sensitive_classification(target.get("data_classification", [])) else "High",
                node_ids=[node["id"]] + path_nodes,
                edge_ids=path_edges,
                evidence=[f"node {node['id']} internet_exposed=Yes", f"reachable target {target['id']}"],
            )

    # 2. Unauthenticated external / trust-boundary-crossing flow.
    for e in edges:
        crosses = e.get("crosses_trust_boundary")
        auth = (e.get("authentication") or "Unknown")
        if crosses == "Yes" and auth in ("Unknown", "None", "none"):
            src = by_id.get(e["from"], {})
            dst = by_id.get(e["to"], {})
            add(
                "unauthenticated_trust_boundary_crossing",
                f"Trust-boundary-crossing flow with unknown/no authentication: {src.get('name')} -> {dst.get('name')}",
                "This data flow crosses a trust boundary but its authentication mechanism is "
                "undocumented or absent. Treat as unauthenticated until confirmed otherwise.",
                "High",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
                evidence=[f"edge {e['id']} crosses_trust_boundary=Yes, authentication={auth}"],
            )

    # 3. Authorization unknown on API / gateway calls.
    for e in edges:
        dst = by_id.get(e["to"], {})
        if dst.get("type") in ("API", "APIGateway") and (e.get("authorization") or "Unknown") == "Unknown":
            src = by_id.get(e["from"], {})
            add(
                "unknown_authorization_on_api_call",
                f"Authorization undocumented on call into '{dst.get('name')}'",
                f"The call from '{src.get('name')}' to '{dst.get('name')}' has no documented "
                "authorization model. Object/function-level authorization gaps (BOLA/BFLA) "
                "cannot be ruled out.",
                "High",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
                evidence=[f"edge {e['id']} authorization=Unknown, target type={dst.get('type')}"],
            )

    # 4. Secrets used outside a managed secret store.
    secret_stores = {n["id"] for n in nodes if n.get("type") == "SecretStore"}
    for e in edges:
        if e.get("relationship") == "USES_SECRET" and e["to"] not in secret_stores and e["from"] not in secret_stores:
            src = by_id.get(e["from"], {})
            add(
                "secret_used_outside_managed_store",
                f"'{src.get('name')}' uses a secret without a documented managed secret store",
                "A USES_SECRET relationship exists where neither endpoint is a recognized "
                "SecretStore node. Secrets may be hardcoded, stored in config, or managed "
                "outside an auditable secret store.",
                "High",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )
    if not secret_stores and any(e.get("relationship") in ("USES_SECRET", "STORES_SECRET_IN") for e in edges):
        add(
            "no_secret_store_despite_usage",
            "No SecretStore node identified despite secret usage",
            "Secret-related relationships exist in the architecture but no component was "
            "classified as a SecretStore. Confirm how secrets are actually managed.",
            "Medium",
        )

    # 5. Trust boundary crossing without confirmed encryption in transit.
    for e in edges:
        if e.get("crosses_trust_boundary") == "Yes" and e.get("encryption_in_transit") not in ("Yes",):
            src = by_id.get(e["from"], {})
            dst = by_id.get(e["to"], {})
            add(
                "trust_boundary_crossing_without_encryption",
                f"Unconfirmed encryption in transit across trust boundary: {src.get('name')} -> {dst.get('name')}",
                "Data crosses a trust boundary without confirmed transport encryption "
                f"(encryption_in_transit={e.get('encryption_in_transit')}).",
                "High" if is_sensitive_classification(e.get("data_classification", [])) else "Medium",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )

    # 6. Admin interface broadly exposed.
    for node in nodes:
        if node.get("type") == "AdminInterface" and node.get("internet_exposed") in ("Yes", "Unknown"):
            add(
                "admin_interface_broadly_exposed",
                f"Admin interface '{node['name']}' may be broadly reachable",
                f"Admin interface internet_exposed={node.get('internet_exposed')}. Confirm it is "
                "restricted to a management network, VPN, or bastion rather than broadly reachable.",
                "Critical" if node.get("internet_exposed") == "Yes" else "Medium",
                node_ids=[node["id"]],
            )

    # 7. Third party receiving sensitive data.
    for e in edges:
        dst = by_id.get(e["to"], {})
        if dst.get("type") == "ThirdPartyService" and (
            is_sensitive_classification(e.get("data_classification", [])) or e.get("data_classification")
        ):
            src = by_id.get(e["from"], {})
            add(
                "third_party_receives_sensitive_data",
                f"Third party '{dst.get('name')}' receives data classified as {e.get('data_classification')}",
                f"'{src.get('name')}' sends data to third party '{dst.get('name')}'. Confirm a data "
                "processing agreement, minimization, and encryption are in place.",
                "High",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )

    # 8. Mobile app directly accessing a backend database.
    for e in edges:
        src = by_id.get(e["from"], {})
        dst = by_id.get(e["to"], {})
        if src.get("type") == "MobileApplication" and dst.get("type") in ("Database", "DataStore"):
            add(
                "mobile_app_direct_database_access",
                f"Mobile app '{src.get('name')}' appears to directly access data store '{dst.get('name')}'",
                "Mobile clients calling a database or data store directly (bypassing an API layer) "
                "typically indicate embedded credentials or overly broad client-side access.",
                "Critical",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )

    # 9. Frontend directly accessing an internal backend service (bypassing a gateway/API).
    for e in edges:
        src = by_id.get(e["from"], {})
        dst = by_id.get(e["to"], {})
        if src.get("type") in ("WebApplication", "MobileApplication") and dst.get("type") in ("BackendService", "Microservice"):
            add(
                "frontend_bypasses_gateway_to_internal_service",
                f"'{src.get('name')}' calls internal service '{dst.get('name')}' directly",
                "Frontend/mobile clients calling backend services or microservices directly, without "
                "an API gateway in the path, bypasses centralized authN/Z, rate limiting, and monitoring.",
                "Medium",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )

    # 10. CI/CD deploying to production without documented approval evidence.
    for e in edges:
        src = by_id.get(e["from"], {})
        dst = by_id.get(e["to"], {})
        if src.get("type") == "CICDPipeline" and e.get("relationship") in ("DEPLOYED_BY", "DEPENDS_ON") \
                and dst.get("environment") == "Production":
            add(
                "cicd_deploys_to_production_without_approval",
                f"CI/CD pipeline '{src.get('name')}' deploys to production '{dst.get('name')}'",
                "No approval/change-control evidence was extracted for this production deployment path. "
                "Confirm mandatory review/approval gates exist.",
                "Medium",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )

    # 11. Logging system receiving sensitive data without masking evidence.
    for e in edges:
        dst = by_id.get(e["to"], {})
        if dst.get("type") == "LoggingSystem" and is_sensitive_classification(e.get("data_classification", [])):
            src = by_id.get(e["from"], {})
            add(
                "logging_system_receives_sensitive_data",
                f"Sensitive data may flow into logging system '{dst.get('name')}'",
                f"'{src.get('name')}' logs data classified as {e.get('data_classification')} with no "
                "documented masking/redaction control.",
                "High",
                node_ids=[e["from"], e["to"]], edge_ids=[e["id"]],
            )

    # 12. Public object storage holding sensitive data.
    for node in nodes:
        if node.get("type") == "ObjectStorage" and node.get("internet_exposed") == "Yes" \
                and (node.get("data_classification") or is_sensitive_classification(node.get("data_classification", []))):
            add(
                "public_object_storage_holds_sensitive_data",
                f"Internet-exposed object storage '{node['name']}' holds classified data",
                f"Storage bucket/container is internet-exposed and holds data classified as "
                f"{node.get('data_classification')}.",
                "Critical",
                node_ids=[node["id"]],
            )

    # 13. Serverless function with unknown/broad permissions.
    for node in nodes:
        if node.get("type") == "Function" and node.get("authorization") == "Unknown":
            add(
                "serverless_function_undocumented_permissions",
                f"Serverless function '{node['name']}' has an undocumented permission model",
                "No IAM role/permission scoping evidence was extracted for this function. "
                "Confirm least-privilege execution roles.",
                "Medium",
                node_ids=[node["id"]],
            )

    # 14. Kubernetes workload with unknown/default service account.
    for node in nodes:
        if node.get("type") in ("KubernetesCluster", "Container") and node.get("authentication") == "Unknown":
            add(
                "kubernetes_workload_undocumented_identity",
                f"'{node['name']}' has no documented workload identity",
                "No service-account / workload-identity evidence was extracted. Default service "
                "accounts commonly carry broader permissions than required.",
                "Medium",
                node_ids=[node["id"]],
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("normalized", help="Path to normalize_entities.py output JSON")
    parser.add_argument("--system-name", default=None, help="Override system name (defaults to value in normalized.json)")
    parser.add_argument("--scope", default="", help="Free-text scope description for metadata")
    parser.add_argument("--generated-by", default="Threat Modelling/build_graph.py")
    parser.add_argument("--source-artifacts", nargs="*", default=[],
                         help="parse_markdown.py/parse_html.py/parse_pdf.py output JSON files, "
                              "used to populate metadata.source_artifacts")
    parser.add_argument("--validate", action="store_true",
                         help="Validate the built graph against references/output-schemas/graph-schema.json "
                              "if the 'jsonschema' package is installed")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    entities = load_json(args.normalized)
    system_name = args.system_name or entities.get("system_name", "Unknown")

    nodes, name_index, placeholders_created = build_nodes(entities)
    edges = build_edges(entities, name_index, nodes, placeholders_created)
    workflow_allocator = IdAllocator("C", [n["id"] for n in nodes])
    business_workflows = resolve_workflow_components(
        entities.get("business_workflows", []), name_index, nodes, workflow_allocator, placeholders_created
    )
    risk_findings = detect_risk_patterns(nodes, edges)

    grp_allocator_seen = 0
    risk_patterns = []
    for finding in risk_findings:
        grp_allocator_seen += 1
        risk_patterns.append({"id": f"GRP-{grp_allocator_seen:03d}", **finding})

    source_artifacts = []
    for path in args.source_artifacts:
        parsed = load_json(path)
        artifact = parsed.get("artifact", {})
        if artifact:
            source_artifacts.append({
                "id": artifact.get("id", "SRC-000"),
                "name": artifact.get("file_name", "Unknown"),
                "type": artifact.get("type", "other"),
                "location": artifact.get("location", ""),
                "hash": artifact.get("hash", ""),
            })

    graph = {
        "metadata": {
            "system_name": system_name,
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            "generated_by": args.generated_by,
            "scope": args.scope,
            "source_artifacts": source_artifacts,
        },
        "nodes": nodes,
        "edges": edges,
        "risk_patterns": risk_patterns,
    }

    validation = {"schema_checked": False, "valid": None, "errors": []}
    if args.validate:
        try:
            import jsonschema  # type: ignore
            from pathlib import Path
            schema_path = Path(__file__).resolve().parent.parent / "references" / "output-schemas" / "graph-schema.json"
            schema = load_json(schema_path)
            validator = jsonschema.Draft202012Validator(schema)
            errors = sorted(validator.iter_errors(graph), key=lambda e: list(e.path))
            validation["schema_checked"] = True
            validation["valid"] = len(errors) == 0
            validation["errors"] = [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors]
        except ImportError:
            validation["errors"] = ["jsonschema package not installed; skipped strict validation (pip install jsonschema)"]

    result = {
        "graph": graph,
        "trust_boundaries": entities.get("trust_boundaries", []),
        "security_controls": entities.get("security_controls", []),
        "business_workflows": business_workflows,
        "unknowns": entities.get("unknowns", []),
        "placeholder_nodes_created": placeholders_created,
        "normalization_warnings": entities.get("warnings", []),
        "validation": validation,
    }

    save_json(result, args.out)
    if args.out != "-":
        eprint(
            f"wrote {args.out} "
            f"({len(nodes)} nodes, {len(edges)} edges, {len(risk_patterns)} risk patterns, "
            f"{len(placeholders_created)} placeholder nodes)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
