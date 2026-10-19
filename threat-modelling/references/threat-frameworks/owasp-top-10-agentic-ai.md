# OWASP Top 10 for Agentic Applications 2026 Reference

This reference maps the OWASP Top 10 for Agentic Applications 2026 to threat modeling, graph construction, static review, dynamic validation, and remediation planning for autonomous and semi-autonomous AI agents.

## Version Note

Latest checked: 2026-08-07. OWASP released the Agentic Applications Top 10 for 2026 in December 2025. This is different from the OWASP Agentic Skills Top 10, which focuses specifically on skill packages and manifests.

## Agent Usage Instructions

- Use this file as a threat-modeling reference, not as a compliance checklist.
- Map each risk to graph nodes, graph edges, source evidence, assumptions, SAST recommendations, DAST recommendations, and action items.
- If a control is not documented in the input artifacts, mark it as `Unknown` rather than assuming it exists.
- Keep DAST guidance high-level and only for authorized environments.

## Top Risks

## ASI01:2026: Agent Goal Hijack

**Description:** Attackers redirect or alter an agent's objective, plan, or decision path through malicious user input, external documents, tool output, memory, or indirect instructions.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI01:2026 - Agent Goal Hijack",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI02:2026: Tool Misuse and Exploitation

**Description:** Agents use legitimate tools in unsafe ways through manipulated parameters, tool-chain abuse, excessive autonomy, or unsafe tool invocation.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI02:2026 - Tool Misuse and Exploitation",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI03:2026: Identity and Privilege Abuse

**Description:** Agent identities, delegated credentials, tokens, or inherited user privileges are misused, over-scoped, leaked, or escalated.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI03:2026 - Identity and Privilege Abuse",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI04:2026: Agentic Supply Chain Vulnerabilities

**Description:** Agent components such as tools, plugins, MCP servers, skills, memory providers, datasets, packages, or external agents are compromised or untrusted.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI04:2026 - Agentic Supply Chain Vulnerabilities",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI05:2026: Unexpected Code Execution

**Description:** Agents generate, invoke, interpret, or execute code, commands, scripts, workflows, or templates unexpectedly or unsafely.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI05:2026 - Unexpected Code Execution",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI06:2026: Memory and Context Poisoning

**Description:** Attackers manipulate short-term context, long-term memory, RAG sources, task state, or shared agent memory to influence future decisions.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI06:2026 - Memory and Context Poisoning",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI07:2026: Insecure Inter-Agent Communication

**Description:** Messages between agents lack authentication, authorization, integrity, provenance, or schema validation, enabling spoofing, tampering, replay, or delegation abuse.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI07:2026 - Insecure Inter-Agent Communication",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI08:2026: Cascading Failures

**Description:** A small error, injected instruction, or compromised agent propagates across multi-step or multi-agent workflows, causing broad impact.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI08:2026 - Cascading Failures",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI09:2026: Human-Agent Trust Exploitation

**Description:** Humans over-trust agent outputs, approvals, summaries, or recommendations, enabling social engineering, unsafe delegation, or rubber-stamped actions.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI09:2026 - Human-Agent Trust Exploitation",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## ASI10:2026: Rogue Agents

**Description:** Compromised, malicious, misaligned, or unsupervised agents deviate from intended behavior while appearing legitimate inside the ecosystem.


**Architecture indicators:**

- Autonomous or semi-autonomous agent can plan and act
- Agent has tools, memory, external calls, or inter-agent communication
- Agent identity, tool permissions, approval gates, or audit trails are undocumented


**Threat modeling questions:**

- What goals can the agent pursue and who can change them?
- What tools and data can the agent access?
- Which actions are irreversible, financial, administrative, externally visible, or high impact?
- How is agent identity authenticated, authorized, logged, and revoked?
- How are memory and inter-agent messages validated?


**Recommended mitigations:**

- Least-privilege agent identities and scoped tool permissions
- Explicit policy enforcement before tool dispatch
- Human approval for high-impact actions
- Signed and verified tools, skills, and MCP servers
- Memory provenance, validation, and expiration
- Inter-agent authentication and message integrity
- Comprehensive audit logs and anomaly monitoring


**SAST or static review focus:**

- Tool wrappers without authorization
- Agent actions executed from raw model output
- Over-broad API keys
- Untrusted memory writes
- Unsafe code execution paths
- Missing audit events


**DAST or dynamic validation focus:**

- Sandboxed agent goal-hijack tests
- Tool misuse simulations with safe tools
- Cross-agent spoofing and replay validation
- Memory poisoning tests using synthetic data
- Approval-gate bypass tests


**Output mapping template:**

```json
{
  "category": "ASI10:2026 - Rogue Agents",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---


## Source Note

Based on OWASP GenAI Security Project resources and practitioner summaries of the ASI01-ASI10 taxonomy. Verify the full wording against the official OWASP PDF during publication review.
