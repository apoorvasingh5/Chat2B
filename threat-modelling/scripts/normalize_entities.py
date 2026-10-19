#!/usr/bin/env python3
"""
Architecture Extraction Agent helper: entity normalization.

Takes one or more *draft* architecture-extraction JSON files -- the kind of
loosely-structured output described in SKILL.md Phase 3 ("components",
"data_flows", "trust_boundaries", "security_controls", "unknowns") produced
by the model while reading artifacts -- and deterministically:

  - merges drafts from multiple source artifacts,
  - de-duplicates entities that clearly refer to the same real-world thing
    (matched on a normalized name key),
  - assigns stable canonical IDs (C-001, DF-001, TB-001, SC-001, UNK-001),
  - fills required-but-missing properties with "Unknown" / [] per the
    canonical schema instead of leaving them absent,
  - coerces free-text enum-ish fields (confidence, environment,
    internet_exposed, node type) onto the schema's allowed values,
  - unions list fields (source_refs, tags, data_classification,
    assumptions) across merged duplicates instead of dropping evidence.

It does NOT invent new entities, resolve data-flow endpoints to component
IDs, or detect risk patterns -- that graph-wiring step happens in
build_graph.py, which consumes this script's output.

Usage:
    python normalize_entities.py draft1.json draft2.json ... --out normalized.json
    python normalize_entities.py draft.json --system-name "Payment Platform"
"""

from __future__ import annotations

import argparse
from typing import Any

from common import (
    CONFIDENCE_VALUES, NODE_TYPES, RELATIONSHIP_TYPES, YES_NO_UNKNOWN,
    IdAllocator, load_json_or_multiple, normalize_enum, normalize_key,
    save_json, eprint,
)

ENVIRONMENT_VALUES = ("Production", "Staging", "Development", "Test", "Shared", "Unknown")

LIST_FIELDS_COMMON = ("source_refs", "tags", "assumptions", "data_classification", "applies_to")


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _union_list(a: list, b: list) -> list:
    """Union two lists preserving order, de-duplicating simple scalars and
    dict-shaped source_refs by their JSON representation."""
    out = list(a)
    seen = {repr(x) for x in a}
    for item in b:
        key = repr(item)
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out


def _first_known(*values: Any, default: str = "Unknown") -> Any:
    for v in values:
        if v not in (None, "", "Unknown", []):
            return v
    return default


def _merge_record(existing: dict, incoming: dict, scalar_fields: tuple, list_fields: tuple = LIST_FIELDS_COMMON) -> dict:
    merged = dict(existing)
    for field in scalar_fields:
        merged[field] = _first_known(existing.get(field), incoming.get(field), default=existing.get(field, "Unknown"))
    for field in list_fields:
        if field in existing or field in incoming:
            merged[field] = _union_list(_as_list(existing.get(field)), _as_list(incoming.get(field)))
    return merged


def normalize_components(drafts: list[dict], warnings: list[str]) -> tuple[list[dict], dict[str, str]]:
    by_key: dict[str, dict] = {}
    order: list[str] = []
    existing_ids = [d.get("id") for draft in drafts for d in draft.get("components", []) if d.get("id")]
    allocator = IdAllocator("C", existing_ids)

    scalar_fields = ("description", "technology", "owner", "environment",
                      "internet_exposed", "authentication", "authorization", "trust_zone")

    for draft in drafts:
        for raw in draft.get("components", []):
            name = (raw.get("name") or "").strip()
            if not name:
                warnings.append("skipped a component with no name")
                continue
            key = normalize_key(name)
            record = {
                "name": name,
                "type": normalize_enum(raw.get("type"), NODE_TYPES, default="Other"),
                "description": raw.get("description", ""),
                "technology": raw.get("technology", "Unknown") or "Unknown",
                "owner": raw.get("owner", "Unknown") or "Unknown",
                "environment": normalize_enum(raw.get("environment"), ENVIRONMENT_VALUES, default="Unknown"),
                "internet_exposed": normalize_enum(raw.get("internet_exposed"), YES_NO_UNKNOWN, default="Unknown"),
                "authentication": raw.get("authentication", "Unknown") or "Unknown",
                "authorization": raw.get("authorization", "Unknown") or "Unknown",
                "data_classification": _as_list(raw.get("data_classification")),
                "trust_zone": raw.get("trust_zone", "Unknown") or "Unknown",
                "tags": _as_list(raw.get("tags")),
                "source_refs": _as_list(raw.get("source_refs")),
                "confidence": normalize_enum(raw.get("confidence"), CONFIDENCE_VALUES, default="Low"),
                "assumptions": _as_list(raw.get("assumptions")),
            }
            if raw.get("id"):
                record["id"] = raw["id"]

            if key in by_key:
                if raw.get("type") and normalize_enum(raw.get("type"), NODE_TYPES, default="Other") != by_key[key]["type"]:
                    warnings.append(
                        f"component '{name}' seen with conflicting types "
                        f"({by_key[key]['type']} vs {record['type']}); kept {by_key[key]['type']}"
                    )
                merged = _merge_record(by_key[key], record, scalar_fields)
                merged["confidence"] = _prefer_confidence(by_key[key]["confidence"], record["confidence"])
                by_key[key] = merged
                warnings.append(f"merged duplicate component '{name}'")
            else:
                by_key[key] = record
                order.append(key)

    components = []
    name_index: dict[str, str] = {}
    for key in order:
        record = by_key[key]
        cid = record.pop("id", None) or allocator.next()
        record = {"id": cid, **record}
        components.append(record)
        name_index[key] = cid

    return components, name_index


def _prefer_confidence(a: str, b: str) -> str:
    order = {"High": 3, "Medium": 2, "Low": 1}
    return a if order.get(a, 0) >= order.get(b, 0) else b


def normalize_data_flows(drafts: list[dict], warnings: list[str]) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    order: list[tuple] = []
    existing_ids = [d.get("id") for draft in drafts for d in draft.get("data_flows", []) if d.get("id")]
    allocator = IdAllocator("DF", existing_ids)

    scalar_fields = ("protocol", "authentication", "authorization",
                      "crosses_trust_boundary", "encryption_in_transit")

    for draft in drafts:
        for raw in draft.get("data_flows", []):
            from_name = (raw.get("from") or "").strip()
            to_name = (raw.get("to") or "").strip()
            if not from_name or not to_name:
                warnings.append("skipped a data flow missing 'from' or 'to'")
                continue
            relationship = normalize_enum(raw.get("relationship"), RELATIONSHIP_TYPES, default="OTHER")
            key = (normalize_key(from_name), normalize_key(to_name), relationship)
            record = {
                "from_name": from_name,
                "to_name": to_name,
                "relationship": relationship,
                "protocol": raw.get("protocol", "Unknown") or "Unknown",
                "port": raw.get("port", "Unknown"),
                "authentication": raw.get("authentication", "Unknown") or "Unknown",
                "authorization": raw.get("authorization", "Unknown") or "Unknown",
                "data_classification": _as_list(raw.get("data_classification")),
                "crosses_trust_boundary": normalize_enum(raw.get("crosses_trust_boundary"), YES_NO_UNKNOWN, default="Unknown"),
                "encryption_in_transit": normalize_enum(
                    raw.get("encryption_in_transit"), YES_NO_UNKNOWN + ("Not applicable",), default="Unknown"
                ),
                "source_refs": _as_list(raw.get("source_refs")),
                "confidence": normalize_enum(raw.get("confidence"), CONFIDENCE_VALUES, default="Low"),
                "assumptions": _as_list(raw.get("assumptions")),
            }
            if raw.get("id"):
                record["id"] = raw["id"]

            if key in by_key:
                merged = _merge_record(by_key[key], record, scalar_fields)
                merged["confidence"] = _prefer_confidence(by_key[key]["confidence"], record["confidence"])
                by_key[key] = merged
                warnings.append(f"merged duplicate data flow '{from_name}' -> '{to_name}' ({relationship})")
            else:
                by_key[key] = record
                order.append(key)

    data_flows = []
    for key in order:
        record = by_key[key]
        fid = record.pop("id", None) or allocator.next()
        data_flows.append({"id": fid, **record})
    return data_flows


def normalize_named_list(drafts: list[dict], field: str, prefix: str, warnings: list[str],
                          scalar_fields: tuple = ("description",)) -> list[dict]:
    """Generic normalizer for trust_boundaries / security_controls: dedupe
    by name, union list fields, assign canonical IDs."""
    by_key: dict[str, dict] = {}
    order: list[str] = []
    existing_ids = [d.get("id") for draft in drafts for d in draft.get(field, []) if d.get("id")]
    allocator = IdAllocator(prefix, existing_ids)

    for draft in drafts:
        for raw in draft.get(field, []):
            name = (raw.get("name") or raw.get("title") or "").strip()
            if not name:
                warnings.append(f"skipped a {field} entry with no name")
                continue
            key = normalize_key(name)
            record = dict(raw)
            record["name"] = name
            record["source_refs"] = _as_list(raw.get("source_refs"))
            record["assumptions"] = _as_list(raw.get("assumptions"))
            record["applies_to"] = _as_list(raw.get("applies_to"))
            record["confidence"] = normalize_enum(raw.get("confidence"), CONFIDENCE_VALUES, default="Low")
            if key in by_key:
                merged = _merge_record(by_key[key], record, scalar_fields)
                merged["confidence"] = _prefer_confidence(by_key[key]["confidence"], record["confidence"])
                by_key[key] = merged
                warnings.append(f"merged duplicate {field} entry '{name}'")
            else:
                by_key[key] = record
                order.append(key)

    results = []
    for key in order:
        record = by_key[key]
        rid = record.pop("id", None) or allocator.next()
        results.append({"id": rid, **record})
    return results


def normalize_workflow_steps(steps: list[dict]) -> list[dict]:
    """Dedupe a workflow's steps by normalized name, preserving order and
    any already-assigned step ids (so re-normalizing previously-normalized
    steps, e.g. when merging two drafts of the same workflow, is stable)."""
    by_key: dict[str, dict] = {}
    order: list[str] = []

    scalar_fields = ("component", "state_change", "state_change_description",
                      "authorization_check", "idempotency_required", "reversible",
                      "rate_limited", "confirms_or_reviews")
    list_fields = ("graph_edge_refs", "preconditions", "client_supplied_fields", "source_refs")

    for raw in steps:
        name = (raw.get("name") or "").strip()
        if not name:
            continue
        key = normalize_key(name)
        record = {
            "name": name,
            "component": raw.get("component", "Unknown") or "Unknown",
            "graph_edge_refs": _as_list(raw.get("graph_edge_refs")),
            "preconditions": _as_list(raw.get("preconditions")),
            "state_change": normalize_enum(raw.get("state_change"), YES_NO_UNKNOWN, default="Unknown"),
            "state_change_description": raw.get("state_change_description", ""),
            "client_supplied_fields": _as_list(raw.get("client_supplied_fields")),
            "authorization_check": normalize_enum(raw.get("authorization_check"), YES_NO_UNKNOWN, default="Unknown"),
            "idempotency_required": normalize_enum(raw.get("idempotency_required"), YES_NO_UNKNOWN, default="Unknown"),
            "reversible": normalize_enum(raw.get("reversible"), YES_NO_UNKNOWN, default="Unknown"),
            "rate_limited": normalize_enum(raw.get("rate_limited"), YES_NO_UNKNOWN, default="Unknown"),
            "confirms_or_reviews": normalize_enum(raw.get("confirms_or_reviews"), YES_NO_UNKNOWN, default="Unknown"),
            "source_refs": _as_list(raw.get("source_refs")),
        }
        if raw.get("id"):
            record["id"] = raw["id"]

        if key in by_key:
            by_key[key] = _merge_record(by_key[key], record, scalar_fields, list_fields)
        else:
            by_key[key] = record
            order.append(key)

    results = []
    for idx, key in enumerate(order, start=1):
        record = by_key[key]
        sid = record.pop("id", None) or f"S{idx}"
        results.append({"id": sid, **record})
    return results


def normalize_workflow_invariants(invariants: list[dict], allocator: IdAllocator) -> list[dict]:
    by_key: dict[str, dict] = {}
    order: list[str] = []

    for raw in invariants:
        statement = (raw.get("statement") or "").strip()
        if not statement:
            continue
        key = normalize_key(statement)[:80]
        record = {
            "statement": statement,
            "enforced_by_step": raw.get("enforced_by_step", "Unknown") or "Unknown",
            "confidence": normalize_enum(raw.get("confidence"), CONFIDENCE_VALUES, default="Low"),
        }
        if raw.get("id"):
            record["id"] = raw["id"]

        if key in by_key:
            by_key[key]["enforced_by_step"] = _first_known(
                by_key[key]["enforced_by_step"], record["enforced_by_step"], default="Unknown"
            )
        else:
            by_key[key] = record
            order.append(key)

    results = []
    for key in order:
        record = by_key[key]
        iid = record.pop("id", None) or allocator.next()
        results.append({"id": iid, **record})
    return results


def normalize_workflows(drafts: list[dict], warnings: list[str]) -> list[dict]:
    """Dedupe business_workflows by normalized name, merging steps/invariants
    from multiple drafts of the same workflow (e.g. one extracted from a
    sequence diagram, one from prose). See SKILL.md Sec 3 Architecture
    Extraction Agent -> Business workflow extraction, and Sec 13 Business
    Logic & Abuse Case Agent, which consumes this output via
    scripts/analyze_workflows.py."""
    by_key: dict[str, dict] = {}
    order: list[str] = []
    existing_wf_ids = [d.get("id") for draft in drafts for d in draft.get("business_workflows", []) if d.get("id")]
    wf_allocator = IdAllocator("BP", existing_wf_ids)
    existing_inv_ids = [
        inv.get("id")
        for draft in drafts
        for d in draft.get("business_workflows", [])
        for inv in d.get("invariants", [])
        if inv.get("id")
    ]
    inv_allocator = IdAllocator("INV", existing_inv_ids)

    for draft in drafts:
        for raw in draft.get("business_workflows", []):
            name = (raw.get("name") or "").strip()
            if not name:
                warnings.append("skipped a business_workflow with no name")
                continue
            key = normalize_key(name)
            steps = normalize_workflow_steps(raw.get("steps", []))
            invariants = normalize_workflow_invariants(raw.get("invariants", []), inv_allocator)
            record = {
                "name": name,
                "goal": raw.get("goal", ""),
                "initiating_actor": raw.get("initiating_actor", "Unknown") or "Unknown",
                "steps": steps,
                "invariants": invariants,
                "source_refs": _as_list(raw.get("source_refs")),
                "confidence": normalize_enum(raw.get("confidence"), CONFIDENCE_VALUES, default="Low"),
            }
            if raw.get("id"):
                record["id"] = raw["id"]

            if key in by_key:
                existing = by_key[key]
                existing["steps"] = normalize_workflow_steps(existing["steps"] + steps)
                existing_inv_ids_seen = {i["id"] for i in existing["invariants"]}
                existing["invariants"] = existing["invariants"] + [
                    i for i in invariants if i["id"] not in existing_inv_ids_seen
                ]
                existing["goal"] = _first_known(existing.get("goal"), record.get("goal"), default="")
                existing["initiating_actor"] = _first_known(
                    existing.get("initiating_actor"), record.get("initiating_actor")
                )
                existing["source_refs"] = _union_list(existing["source_refs"], record["source_refs"])
                warnings.append(f"merged duplicate business_workflow '{name}'")
            else:
                by_key[key] = record
                order.append(key)

    results = []
    for key in order:
        record = by_key[key]
        wid = record.pop("id", None) or wf_allocator.next()
        results.append({"id": wid, **record})
    return results


def normalize_unknowns(drafts: list[dict], warnings: list[str]) -> list[dict]:
    by_key: dict[str, dict] = {}
    order: list[str] = []
    existing_ids = [d.get("id") for draft in drafts for d in draft.get("unknowns", []) if d.get("id")]
    allocator = IdAllocator("UNK", existing_ids)

    for draft in drafts:
        for raw in draft.get("unknowns", []):
            description = (raw.get("description") or raw.get("topic") or "").strip()
            if not description:
                continue
            key = normalize_key(description)[:80]
            record = {
                "topic": raw.get("topic", ""),
                "description": description,
                "applies_to": _as_list(raw.get("applies_to")),
                "source_refs": _as_list(raw.get("source_refs")),
            }
            if raw.get("id"):
                record["id"] = raw["id"]
            if key in by_key:
                by_key[key]["applies_to"] = _union_list(by_key[key]["applies_to"], record["applies_to"])
                by_key[key]["source_refs"] = _union_list(by_key[key]["source_refs"], record["source_refs"])
                warnings.append(f"merged duplicate unknown '{description[:60]}'")
            else:
                by_key[key] = record
                order.append(key)

    results = []
    for key in order:
        record = by_key[key]
        uid = record.pop("id", None) or allocator.next()
        results.append({"id": uid, **record})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("drafts", nargs="+", help="One or more draft architecture-extraction JSON files")
    parser.add_argument("--system-name", default="Unknown", help="System name to stamp into the output")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    drafts = load_json_or_multiple(args.drafts)
    warnings: list[str] = []

    components, name_index = normalize_components(drafts, warnings)
    data_flows = normalize_data_flows(drafts, warnings)
    trust_boundaries = normalize_named_list(drafts, "trust_boundaries", "TB", warnings)
    security_controls = normalize_named_list(drafts, "security_controls", "SC", warnings)
    business_workflows = normalize_workflows(drafts, warnings)
    unknowns = normalize_unknowns(drafts, warnings)

    unresolved = sorted({
        name for df in data_flows
        for name in (df["from_name"], df["to_name"])
        if normalize_key(name) not in name_index
    })
    if unresolved:
        warnings.append(
            f"{len(unresolved)} data-flow endpoint(s) do not match an extracted component "
            f"and will need a placeholder node in build_graph.py: {', '.join(unresolved)}"
        )

    result = {
        "system_name": args.system_name,
        "components": components,
        "data_flows": data_flows,
        "trust_boundaries": trust_boundaries,
        "security_controls": security_controls,
        "business_workflows": business_workflows,
        "unknowns": unknowns,
        "name_index": name_index,
        "unresolved_data_flow_endpoints": unresolved,
        "warnings": warnings,
    }

    save_json(result, args.out)
    if args.out != "-":
        eprint(
            f"wrote {args.out} ({len(components)} components, {len(data_flows)} data flows, "
            f"{len(business_workflows)} business workflows, {len(warnings)} warnings)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
