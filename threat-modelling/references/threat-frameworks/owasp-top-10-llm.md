# OWASP GenAI LLM Top 10 2026 Reference

This reference maps the OWASP GenAI LLM Top 10 2026 to architecture threat modeling, agent design review, SAST/static review, DAST/adversarial validation, and action-item generation.

## Version Note

Latest checked: 2026-08-07. The current OWASP GenAI LLM Top 10 release is 2026, published in August 2026. This supersedes the 2025 LLM taxonomy used in the earlier file.

## Agent Usage Instructions

- Use this file as a threat-modeling reference, not as a compliance checklist.
- Map each risk to graph nodes, graph edges, source evidence, assumptions, SAST recommendations, DAST recommendations, and action items.
- If a control is not documented in the input artifacts, mark it as `Unknown` rather than assuming it exists.
- Keep DAST guidance high-level and only for authorized environments.

## Top Risks

## LLM01:2026: Prompt Injection

**Description:** Untrusted user, retrieved, tool, memory, multimodal, or indirect content changes model behavior or tool decisions.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM01:2026 - Prompt Injection",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM02:2026: Sensitive Information Disclosure

**Description:** LLM-integrated systems expose confidential, regulated, privileged, proprietary, or credential data through prompts, retrieval, memory, logs, tools, or outputs.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM02:2026 - Sensitive Information Disclosure",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM03:2026: Excessive Agency

**Description:** An LLM or agent has excessive functionality, permissions, or autonomy, allowing unexpected outputs to create harmful real-world actions.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM03:2026 - Excessive Agency",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM04:2026: Supply Chain

**Description:** Models, packages, plugins, datasets, tools, MCP servers, or providers are compromised, vulnerable, untrusted, or unverifiable.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM04:2026 - Supply Chain",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM05:2026: Data and Model Poisoning

**Description:** Training, fine-tuning, retrieval, memory, or embedding data is manipulated to influence model behavior, outputs, or decisions.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM05:2026 - Data and Model Poisoning",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM06:2026: Unbounded Consumption

**Description:** The system allows excessive token, compute, memory, network, storage, recursion, tool-call, or cost consumption.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM06:2026 - Unbounded Consumption",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM07:2026: Misinformation

**Description:** The system generates incorrect, unsupported, incomplete, or misleading information that users or automated workflows may trust.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM07:2026 - Misinformation",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM08:2026: Hidden Context Exposure

**Description:** Non-user-visible context, prompts, schemas, policies, chain instructions, tool descriptions, or retrieval metadata are exposed and aid attack planning.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM08:2026 - Hidden Context Exposure",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM09:2026: Vector and Embedding Weaknesses

**Description:** Vector stores, embeddings, retrieval filters, metadata, or similarity logic expose, corrupt, mis-associate, or cross-contaminate retrieved content.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM09:2026 - Vector and Embedding Weaknesses",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## LLM10:2026: Improper Output Handling

**Description:** LLM outputs are passed to downstream interpreters, renderers, tools, workflows, or humans without validation, encoding, policy checks, or approval gates.


**Architecture indicators:**

- LLM application, RAG pipeline, autonomous tool use, or AI workflow present
- Trust boundaries between user input, retrieved context, prompts, tools, memory, and downstream systems are unclear
- Controls are enforced only in prompt text rather than in code or policy layers


**Threat modeling questions:**

- What data enters the prompt, retrieval context, memory, or tool parameters?
- What can the model cause downstream systems to do?
- Which actions require validation or approval outside the model?
- How are retrieval and memory access controls enforced?
- What resource, cost, recursion, and tool-call limits exist?


**Recommended mitigations:**

- Separate data from instructions wherever possible
- Use least-privilege tools and scoped credentials
- Add policy enforcement outside the model
- Validate and encode outputs before downstream use
- Apply access-aware retrieval and memory controls
- Add monitoring, quotas, and human approval for high-impact actions


**SAST or static review focus:**

- Prompt construction with untrusted data
- Tool wrappers missing authorization
- Secrets in prompts or logs
- Retrieval without access filters
- LLM output passed to SQL, shell, HTML, code, tickets, emails, or APIs


**DAST or dynamic validation focus:**

- Prompt injection resilience tests with safe scenarios
- Synthetic sensitive-data leakage tests
- Agent action boundary testing in sandbox
- Resource-limit validation
- Retrieval isolation tests


**Output mapping template:**

```json
{
  "category": "LLM10:2026 - Improper Output Handling",
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

Based on the OWASP GenAI LLM Top 10 2026 resource page and the official OWASP GenAI Security Project GitHub source summary.
