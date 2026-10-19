#!/usr/bin/env python3
"""
Business Logic & Abuse Case Agent helper (SKILL.md Sec 13, Tier 2 of
Threat Identification).

Deciding *that* a workflow has a business-logic problem, and writing the
attack narrative, is the model's job -- it requires understanding what the
workflow is *for*. But several structural questions about a documented
workflow are mechanical graph/attribute checks, exactly like
build_graph.py's "High-Risk Graph Patterns" are for the point-to-point
architecture graph:

  - does a later step have an inbound edge that bypasses the step before it
    (i.e. can the sequence be skipped)?
  - does a state-changing step lack documented idempotency, authorization
    re-assertion, or rate limiting?
  - is a declared invariant missing an enforcement point?
  - does an irreversible step lack a preceding confirmation step?
  - does a step trust a client-supplied completion/status flag instead of
    deriving it server-side?

Running these as code means Tier 2 threat identification starts from a list
of concrete, cited structural gaps instead of the model re-deriving them by
re-reading the whole workflow model's steps from scratch every time (and
risking missing one) -- the same "scripts do the mechanical check, the
model reasons about what it means" split used throughout this skill
(build_graph.py's risk patterns, recommend_sast_queries.py's CSV lookup,
map_attack_techniques.py's ID lookup).

Input: a JSON file (or list of files) holding `business_workflows` entries
conforming to references/output-schemas/threat-model-output.json's
`workflow` $def (either `{"business_workflows": [...]}` or a bare list of
workflow objects), optionally combined with a build_graph.py bundle (`--graph-bundle`)
so the "reachable out of order" check has real inbound-edge data to check
against.

Usage:
    python analyze_workflows.py workflows.json --out workflow_risk_patterns.json
    python analyze_workflows.py workflows.json --graph-bundle graph_bundle.json --out workflow_risk_patterns.json
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import load_json, save_json, eprint

SENSITIVE_WORKFLOW_KEYWORDS = (
    "payment", "charge", "refund", "balance", "credit", "wallet", "coupon",
    "discount", "promo", "inventory", "stock", "transfer", "withdraw",
    "redeem", "referral", "reward", "loyalty", "invoice", "order",
)

CLIENT_COMPLETION_FLAG_KEYWORDS = (
    "status", "stage", "step", "state", "completed", "paid", "confirmed",
    "approved", "verified", "is_paid", "ispaid", "is_verified",
)

COMPENSATION_KEYWORDS = (
    "rollback", "compensate", "compensation", "reverse", "undo", "cancel",
    "refund", "void",
)

CONFIRMATION_KEYWORDS = ("confirm", "review", "approve", "verify")

CALLBACK_KEYWORDS = ("webhook", "callback", "notify", "notification")


def _text_has_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    text = (text or "").lower()
    return any(k in text for k in keywords)


def _step_texts(step: dict) -> str:
    return " ".join([
        step.get("name", ""),
        step.get("state_change_description", ""),
        " ".join(step.get("client_supplied_fields", []) or []),
    ])


def load_workflows(paths: list[str]) -> list[dict]:
    workflows: list[dict] = []
    for p in paths:
        data = load_json(p)
        if isinstance(data, dict) and "business_workflows" in data:
            workflows.extend(data["business_workflows"])
        elif isinstance(data, list):
            workflows.extend(data)
        elif isinstance(data, dict) and "id" in data and "steps" in data:
            workflows.append(data)
    return workflows


def build_inbound_index(graph_bundle: dict | None) -> dict[str, list[str]]:
    """component_id -> list of component_ids with an edge INTO it."""
    inbound: dict[str, list[str]] = {}
    if not graph_bundle:
        return inbound
    for edge in graph_bundle.get("graph", {}).get("edges", []):
        inbound.setdefault(edge["to"], []).append(edge["from"])
    return inbound


def analyze_workflow(workflow: dict, inbound_index: dict[str, list[str]]) -> list[dict]:
    findings: list[dict] = []
    wf_id = workflow.get("id", "BP-UNKNOWN")
    wf_name = workflow.get("name", "")
    steps = workflow.get("steps", [])
    sensitive = _text_has_keyword(wf_name, SENSITIVE_WORKFLOW_KEYWORDS) or any(
        _text_has_keyword(_step_texts(s), SENSITIVE_WORKFLOW_KEYWORDS) for s in steps
    )

    def add(key, step_id, title, description, severity, evidence=()):
        findings.append({
            "pattern_key": key,
            "workflow_id": wf_id,
            "step_id": step_id,
            "title": title,
            "description": description,
            "severity": severity,
            "evidence": list(evidence),
        })

    for i, step in enumerate(steps):
        step_id = step.get("id", f"S{i + 1}")

        # 1. Step reachable out of documented order: something other than
        # the previous step's component has a direct edge into this step's
        # component.
        if i > 0 and inbound_index:
            prev_component = steps[i - 1].get("component")
            this_component = step.get("component")
            if this_component:
                inbound = inbound_index.get(this_component, [])
                unexpected = [c for c in inbound if c != prev_component]
                if unexpected:
                    add(
                        "workflow_step_reachable_out_of_order",
                        step_id,
                        f"'{step.get('name')}' ({wf_id}/{step_id}) may be reachable without completing the prior step",
                        f"The graph shows component '{this_component}' reachable from {unexpected}, not only from "
                        f"'{prev_component}' (the documented previous step). Verify the service enforces that this "
                        "step cannot run before its prerequisite step, rather than relying on clients to call "
                        "endpoints in the intended order.",
                        "High" if sensitive else "Medium",
                        evidence=[f"inbound to {this_component}: {unexpected}"],
                    )

        # 2. State-changing step without idempotency evidence.
        if step.get("state_change") == "Yes" and step.get("idempotency_required") != "Yes":
            add(
                "state_changing_step_without_idempotency_evidence",
                step_id,
                f"'{step.get('name')}' ({wf_id}/{step_id}) changes state without documented idempotency protection",
                "A retried or duplicated client request (network retry, double-click, replay, or deliberate "
                "parallel requests) may be processed twice. Verify an idempotency key, unique constraint, or "
                "equivalent duplicate-submission protection exists.",
                "High" if sensitive else "Medium",
            )

        # 3. Client-supplied field trusted without authorization/ownership re-check.
        client_fields = step.get("client_supplied_fields") or []
        if client_fields and step.get("authorization_check") != "Yes":
            add(
                "client_supplied_field_without_authorization_recheck",
                step_id,
                f"'{step.get('name')}' ({wf_id}/{step_id}) trusts client-supplied field(s) {client_fields} without a documented authorization/ownership re-check",
                "Server-trusted client input for business-critical fields (price, quantity, discount, ownership "
                "identifiers, workflow-instance IDs) at a step with no independent authorization check is a "
                "classic parameter-tampering and workflow-ownership-confusion pattern that SAST/DAST rules for "
                "generic injection or missing-auth will not catch, because the field and the request are "
                "syntactically valid.",
                "Critical" if sensitive else "High",
                evidence=[f"client_supplied_fields: {client_fields}"],
            )

        # 4. Irreversible step without a preceding confirmation/review step.
        if step.get("reversible") == "No":
            preceding = steps[:i]
            has_confirmation = any(
                _text_has_keyword(s.get("name", ""), CONFIRMATION_KEYWORDS) or s.get("confirms_or_reviews") == "Yes"
                for s in preceding
            )
            if not has_confirmation:
                add(
                    "irreversible_step_without_preceding_confirmation",
                    step_id,
                    f"'{step.get('name')}' ({wf_id}/{step_id}) is irreversible with no documented confirmation step before it",
                    "A single request (sent in error, automated, or malicious) permanently changes state with no "
                    "review/confirm gate and no compensating action available afterward.",
                    "High" if sensitive else "Medium",
                )

        # 5. Missing rate limit on a repeatable, sensitive, state-changing step.
        if step.get("state_change") == "Yes" and step.get("rate_limited") != "Yes" and sensitive:
            add(
                "missing_rate_limit_on_repeatable_sensitive_step",
                step_id,
                f"'{step.get('name')}' ({wf_id}/{step_id}) has no documented rate limit on a sensitive, repeatable, state-changing action",
                "Legitimate-looking repeated calls to this step (coupon redemption, inventory decrement, credit/"
                "balance changes) can be abused at scale -- inventory oversell, coupon-stacking, credential "
                "stuffing against a business process rather than a login form -- without tripping any generic "
                "WAF/SAST rule, since each individual call is syntactically valid.",
                "High",
            )

        # 6. Step relies on a client-declared completion/status flag.
        completion_fields = [f for f in client_fields if _text_has_keyword(f, CLIENT_COMPLETION_FLAG_KEYWORDS)]
        if completion_fields:
            add(
                "step_relies_on_client_declared_completion_flag",
                step_id,
                f"'{step.get('name')}' ({wf_id}/{step_id}) trusts a client-supplied status/completion field {completion_fields}",
                "If the server derives workflow progress (e.g. 'payment confirmed', 'step completed') from a "
                "field the client sets rather than from its own authoritative state (payment provider webhook, "
                "database record), a client can skip or fake completion of a prior step entirely.",
                "Critical",
                evidence=[f"client_supplied_fields matching completion-flag keywords: {completion_fields}"],
            )

        # 7. Async callback finalizes business state without verification.
        if _text_has_keyword(step.get("name", ""), CALLBACK_KEYWORDS) and step.get("state_change") == "Yes" \
                and step.get("authorization_check") != "Yes":
            add(
                "async_callback_finalizes_state_without_verification",
                step_id,
                f"'{step.get('name')}' ({wf_id}/{step_id}) finalizes business state from an external callback without documented verification",
                "Webhook/callback-driven state changes (e.g. marking an order paid on a payment-provider webhook) "
                "must verify the callback's authenticity and cross-check it against the provider's own "
                "source-of-truth API, not trust the callback payload alone.",
                "Critical" if sensitive else "High",
            )

    # 8. Invariant declared without an identified enforcement point.
    step_ids = {s.get("id") for s in steps}
    for inv in workflow.get("invariants", []):
        enforced_by = inv.get("enforced_by_step")
        if not enforced_by or enforced_by == "Unknown" or enforced_by not in step_ids:
            add(
                "invariant_without_enforcement_point",
                enforced_by if enforced_by in step_ids else None,
                f"Invariant {inv.get('id')} has no identified enforcement point in {wf_id}",
                f"'{inv.get('statement')}' is declared as a business rule for this workflow, but no step was "
                "identified as the place that actually checks/enforces it server-side. An unenforced invariant "
                "is a documented intention, not a control.",
                "High" if sensitive else "Medium",
            )

    # 9. Multi-step, state-changing workflow with no documented compensation/rollback step.
    state_changing_steps = [s for s in steps if s.get("state_change") == "Yes"]
    if len(state_changing_steps) >= 2 and not any(
        _text_has_keyword(s.get("name", ""), COMPENSATION_KEYWORDS) for s in steps
    ):
        add(
            "workflow_missing_compensation_step",
            None,
            f"{wf_id} ('{wf_name}') has multiple state-changing steps with no documented compensation/rollback step",
            "If the workflow fails partway through (e.g. inventory reserved but payment fails), is there a "
            "documented compensating action, or can the system be left in an inconsistent state an attacker "
            "can trigger deliberately (e.g. repeatedly starting and abandoning checkout to hold inventory)?",
            "Medium",
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("workflows", nargs="+", help="One or more JSON files with business_workflows entries")
    parser.add_argument("--graph-bundle", default=None,
                         help="build_graph.py output JSON, used for the workflow_step_reachable_out_of_order check")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    workflows = load_workflows(args.workflows)
    graph_bundle = load_json(args.graph_bundle) if args.graph_bundle else None
    inbound_index = build_inbound_index(graph_bundle)

    all_findings: list[dict] = []
    for wf in workflows:
        all_findings.extend(analyze_workflow(wf, inbound_index))

    for i, f in enumerate(all_findings, start=1):
        f["id"] = f"WFRP-{i:03d}"

    note = (
        "workflow_step_reachable_out_of_order was skipped (no --graph-bundle supplied); re-run with it for a "
        "real reachability check instead of relying on the documented step order alone."
        if not graph_bundle else ""
    )

    output = {
        "workflow_risk_patterns": all_findings,
        "workflows_analyzed": len(workflows),
        "note": note,
    }

    save_json(output, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} ({len(workflows)} workflow(s), {len(all_findings)} finding(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
