# STRIDE Threat Modeling Reference

## Purpose

Use this reference to evaluate each graph node, data flow, trust boundary crossing, identity path, and privileged operation for STRIDE threats.

STRIDE categories:

1. Spoofing
2. Tampering
3. Repudiation
4. Information Disclosure
5. Denial of Service
6. Elevation of Privilege

## How the Agent Should Use This File

For every security graph element, the agent should ask:

- What can go wrong?
- What attacker capability is required?
- What asset is affected?
- What security property is violated?
- What controls are present, missing, or unknown?
- What evidence supports the assessment?

The agent must not create unsupported threats. If a threat is plausible but not confirmed, mark it as an assumption or missing-context risk.

## STRIDE Category Matrix

### S: Spoofing

**Security property affected:** Authenticity

**Definition:** An attacker pretends to be another user, service, workload, device, or trusted system.

**Common architecture indicators:**

- Authentication mechanism is undocumented.
- Service-to-service identity is unclear.
- API accepts bearer tokens without documented validation.
- Mobile or web client directly trusts client-side identity claims.
- mTLS, workload identity, managed identity, or certificate validation is absent or unknown.
- Third-party callbacks, webhooks, or partner integrations lack sender validation.

**Questions to ask:**

- How is the caller authenticated?
- Is identity validated server-side?
- Are tokens validated for issuer, audience, expiry, signature, and intended use?
- Is service identity bound to workload, environment, or network location?
- Are webhook signatures or mutual authentication used?
- Can one tenant, user, device, or service impersonate another?

**Example threats:**

- Forged JWT accepted by backend API.
- Spoofed webhook triggers privileged workflow.
- Compromised service account impersonates production workload.
- Mobile client sends user role claims that backend trusts.

**Typical mitigations:**

- Strong authentication using OIDC, OAuth2, SAML, mTLS, managed identity, or workload identity.
- Strict token validation: issuer, audience, expiry, signature, nonce, scopes, and claims.
- Sender validation for webhooks using signatures, timestamp validation, replay protection, and allowlists where appropriate.
- No trust in client-supplied identity, role, tenant, or ownership claims.
- Credential rotation and least-privilege service identities.

**SAST focus:**

- Token validation bypass.
- Missing issuer or audience validation.
- Client-supplied role or tenant trust.
- Hardcoded credentials.
- Weak or custom authentication logic.

**DAST focus:**

- JWT tampering.
- Expired token reuse.
- Missing audience or issuer enforcement.
- Webhook signature bypass testing with approved test endpoints.
- Session fixation or identity switching tests.

---

### T: Tampering

**Security property affected:** Integrity

**Definition:** An attacker modifies data, messages, configuration, code, artifacts, or infrastructure state without authorization.

**Common architecture indicators:**

- Data crosses trust boundaries without integrity protection evidence.
- Message queues or event streams lack signing, validation, or authorization evidence.
- CI/CD pipeline can modify production without approval or provenance controls.
- Configuration, feature flags, or templates are writable by broad roles.
- File uploads are accepted and later processed.
- Webhooks or callbacks alter state.

**Questions to ask:**

- Is data integrity protected in transit and at rest?
- Are requests, events, webhooks, and files validated before processing?
- Are schemas enforced?
- Can messages be replayed, reordered, or altered?
- Are deployment artifacts signed or verified?
- Can configuration changes bypass review?

**Example threats:**

- Attacker modifies payment amount in transit or request body.
- Malicious event injected into queue triggers account changes.
- Unsigned container image is deployed to production.
- Uploaded file modifies backend processing behavior.

**Typical mitigations:**

- TLS for transport protection.
- Message signing or HMAC validation for high-risk asynchronous flows.
- Schema validation and strict input validation.
- Immutable audit logs and configuration governance.
- Signed builds, artifact provenance, and deployment approvals.
- Replay protection using nonces, timestamps, idempotency keys, or sequence numbers.

**SAST focus:**

- Missing server-side validation.
- Unsafe deserialization.
- Mass assignment.
- Insecure file handling.
- Unsanitized templates or expression evaluation.
- Insecure CI/CD scripts.

**DAST focus:**

- Parameter tampering.
- HTTP method tampering.
- Mass assignment.
- File upload validation.
- Event replay in authorized test environments.

---

### R: Repudiation

**Security property affected:** Non-repudiation and accountability

**Definition:** A user, service, or administrator can deny performing an action because the system lacks reliable evidence.

**Common architecture indicators:**

- Audit logging is undocumented.
- Logs do not include actor, action, target, timestamp, result, and correlation ID.
- Administrative actions are not separately audited.
- Logs are mutable or accessible to the same identities being audited.
- Security events are not centralized.

**Questions to ask:**

- Which actions require auditability?
- Are authentication, authorization, admin, data access, and policy changes logged?
- Are logs tamper-resistant?
- Are timestamps synchronized?
- Are logs correlated across services?
- Are denied and failed actions captured?

**Example threats:**

- Admin deletes customer records and denies action.
- Service account modifies authorization policy without traceability.
- Attacker disables logs before data exfiltration.

**Typical mitigations:**

- Centralized audit logging.
- Immutable or append-only log storage.
- Correlation IDs across services.
- Privileged activity logging and alerting.
- Time synchronization.
- Clear retention policy aligned to legal and compliance needs.

**SAST focus:**

- Missing audit calls around privileged operations.
- Sensitive operations without structured logging.
- Logging failures swallowed silently.
- Logs containing sensitive data.

**DAST focus:**

- Validate audit event generation for login, logout, access denied, role changes, data export, and admin actions.
- Verify logs include correlation IDs and actor identifiers.
- Verify failed actions are logged without leaking sensitive details.

---

### I: Information Disclosure

**Security property affected:** Confidentiality

**Definition:** Information is exposed to unauthorized users, services, tenants, logs, clients, third parties, or networks.

**Common architecture indicators:**

- Sensitive data classification is unknown.
- APIs expose user-owned resources.
- Logs receive request or response bodies.
- Storage is internet-accessible or exposure is unknown.
- Data crosses trust boundaries.
- Encryption at rest or in transit is undocumented.
- Error responses reveal implementation details.
- Third parties receive sensitive data.

**Questions to ask:**

- What sensitive data is stored, processed, transmitted, or logged?
- Is object-level authorization enforced?
- Is data encrypted in transit and at rest?
- Are secrets stored in a managed secret store?
- Are logs masked or tokenized?
- Are third-party data sharing agreements and controls documented?

**Example threats:**

- IDOR exposes another user's records.
- Logs contain access tokens or payment data.
- Public object storage exposes files.
- Error response exposes stack trace or internal hostname.
- Prompt, RAG context, or model output exposes sensitive information.

**Typical mitigations:**

- Server-side authorization and ownership checks.
- Encryption in transit and at rest.
- Tokenization, masking, and data minimization.
- Secrets management with rotation.
- Private endpoints and restricted network exposure.
- Least-privilege access to data stores.
- Response filtering and error handling.

**SAST focus:**

- Sensitive data logging.
- Missing authorization checks.
- Hardcoded secrets.
- Weak cryptography.
- Verbose error handling.
- Insecure direct object references.

**DAST focus:**

- IDOR and BOLA testing.
- Sensitive data exposure in responses and errors.
- Security headers.
- Directory or object enumeration.
- Token leakage in URLs, headers, logs, or redirects.

---

### D: Denial of Service

**Security property affected:** Availability

**Definition:** Attackers degrade or deny service to valid users by exhausting compute, memory, network, storage, queue, database, external dependency, or business process capacity.

**Common architecture indicators:**

- Internet-facing APIs lack rate limiting evidence.
- Expensive operations are unauthenticated.
- Queues can grow without bounds.
- File upload size or type limits are unknown.
- Dependency calls lack timeouts or circuit breakers.
- Autoscaling and quota controls are undocumented.
- LLM or AI calls can trigger unbounded token or tool consumption.

**Questions to ask:**

- Are rate limits enforced per user, tenant, IP, token, and endpoint?
- Are expensive operations protected?
- Are quotas defined for tenants and integrations?
- Are dependency timeouts and retries bounded?
- Are queues monitored for backlog and poison messages?
- Are model token usage and tool calls bounded?

**Example threats:**

- API endpoint abused to exhaust database connections.
- Large file upload consumes storage or malware scanning capacity.
- Queue flood delays critical processing.
- LLM workflow generates excessive cost or resource consumption.

**Typical mitigations:**

- Rate limiting and quotas.
- Request size limits.
- Backpressure, circuit breakers, and bounded retries.
- Queue dead-lettering and poison message handling.
- Autoscaling with cost guardrails.
- Per-tenant resource isolation.
- LLM token, cost, recursion, and tool-call limits.

**SAST focus:**

- Unbounded loops or recursive calls.
- Missing timeout settings.
- Unsafe retry logic.
- Lack of file size validation.
- Expensive operations before authentication or authorization.

**DAST focus:**

- Safe rate-limit validation.
- Request size and payload limit tests.
- API schema fuzzing within approved bounds.
- Timeout and resilience behavior validation.

---

### E: Elevation of Privilege

**Security property affected:** Authorization

**Definition:** An attacker gains permissions beyond what they are entitled to, including user privilege escalation, tenant breakout, admin access, workload privilege escalation, or cloud control-plane compromise.

**Common architecture indicators:**

- Role model is undocumented.
- Admin APIs share routes or code paths with user APIs.
- Service accounts have broad permissions.
- Kubernetes workloads use default service accounts.
- Cloud identities use wildcard permissions.
- Authorization is performed only in the frontend.
- Multi-tenant isolation is unclear.

**Questions to ask:**

- Is authorization enforced server-side for every protected operation?
- Are admin functions isolated from user functions?
- Are service identities least privileged?
- Is tenant context derived from trusted server-side identity?
- Are privileged actions protected with step-up authentication or approval?
- Are cloud roles scoped to minimum required actions and resources?

**Example threats:**

- Regular user calls admin endpoint.
- Tenant A accesses Tenant B data.
- Compromised service identity writes to production secrets.
- Container workload obtains cluster-admin capabilities.

**Typical mitigations:**

- Centralized policy enforcement.
- Deny-by-default authorization.
- Least privilege IAM and RBAC.
- Separation of admin and user planes.
- Tenant isolation controls.
- Privileged access management, just-in-time access, and approval workflows.
- Cloud control-plane monitoring.

**SAST focus:**

- Missing authorization middleware.
- Role checks performed client-side.
- Inconsistent access control across endpoints.
- Dangerous IAM policy generation.
- Privileged code paths reachable from user input.

**DAST focus:**

- BFLA testing.
- Role switching tests.
- Tenant isolation testing.
- Admin endpoint access attempts with lower-privilege accounts.
- Horizontal and vertical authorization tests.

## STRIDE-by-Graph-Element Guidance

### Actor or UserGroup

Evaluate Spoofing, Repudiation, and Elevation of Privilege.

### Application, API, Microservice, or Function

Evaluate all STRIDE categories.

### Database, Storage, Queue, or Event Stream

Evaluate Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege.

### Identity Provider or Authorization Server

Evaluate Spoofing, Tampering, Information Disclosure, Denial of Service, and Elevation of Privilege.

### Secret Store

Evaluate Spoofing, Information Disclosure, Tampering, and Elevation of Privilege.

### Trust Boundary

Evaluate all flows crossing the boundary for Spoofing, Tampering, Information Disclosure, and Elevation of Privilege.

### CI/CD Pipeline

Evaluate Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege.

## Threat Output Template

```json
{
  "id": "T-001",
  "title": "<short threat title>",
  "stride": ["Spoofing"],
  "component": "<component name>",
  "graph_refs": {
    "nodes": ["C-001"],
    "edges": ["DF-001"]
  },
  "attack_scenario": "<what could go wrong>",
  "preconditions": [],
  "impact": "<business and technical impact>",
  "likelihood": "High|Medium|Low",
  "severity": "Critical|High|Medium|Low|Informational",
  "confidence": "High|Medium|Low",
  "evidence": [],
  "assumptions": [],
  "open_questions": [],
  "recommended_controls": []
}
```
