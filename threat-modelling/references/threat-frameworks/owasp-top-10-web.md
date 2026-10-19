# OWASP Top 10 Web Application Risks 2025 Reference

This reference maps OWASP Top 10:2025 web application risks to architecture threat modeling, SAST focus areas, DAST validation ideas, and action-item generation.

## Version Note

Latest checked: 2026-08-07. OWASP Top 10 for Web is now 2025, not 2021. The 2025 list introduces Software Supply Chain Failures and Mishandling of Exceptional Conditions, moves Security Misconfiguration to A02, and folds SSRF into Broken Access Control.

## Agent Usage Instructions

- Use this file as a threat-modeling reference, not as a compliance checklist.
- Map each risk to graph nodes, graph edges, source evidence, assumptions, SAST recommendations, DAST recommendations, and action items.
- If a control is not documented in the input artifacts, mark it as `Unknown` rather than assuming it exists.
- Keep DAST guidance high-level and only for authorized environments.

## Top Risks

## A01:2025: Broken Access Control

**Description:** Failures that allow users, services, or workloads to exceed intended permissions. In the 2025 taxonomy, SSRF is treated as part of this broader access-control failure class.


**Architecture indicators:**

- Object identifiers from users
- Admin functions exposed through shared API surfaces
- Authorization model undocumented
- SSRF-capable URL fetchers or metadata access paths


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Is authorization centralized and enforced server-side on every object and function access?
- Can user-controlled input influence where the server sends requests?


**Recommended mitigations:**

- Deny-by-default access control
- Centralized authorization middleware or policy enforcement
- Object ownership and tenant isolation checks
- SSRF allowlists and egress controls
- Least-privilege service identities


**SAST or static review focus:**

- Missing authorization middleware
- IDOR/BOLA patterns
- Tenant ID accepted from request
- User-controlled URL fetch
- Privilege checks bypassed by alternate routes


**DAST or dynamic validation focus:**

- BOLA/IDOR validation with safe test users
- BFLA role tests
- Forced browsing
- Authorized SSRF validation using approved endpoints


**Output mapping template:**

```json
{
  "category": "A01:2025 - Broken Access Control",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A02:2025: Security Misconfiguration

**Description:** Misconfigured software, cloud services, frameworks, headers, network controls, API gateways, or runtime settings that create avoidable exposure.


**Architecture indicators:**

- Debug mode enabled
- Public admin consoles or API docs
- Permissive CORS
- Missing security headers
- Open cloud storage or broad network exposure


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Are deployment baselines defined for every environment?
- Are configurations scanned as code and after deployment?


**Recommended mitigations:**

- Secure baseline templates
- Configuration-as-code scanning
- Cloud posture checks
- Environment separation
- Minimal exposed services
- Safe error handling


**SAST or static review focus:**

- Debug flags
- CORS wildcard
- Missing security headers
- Unsafe framework defaults
- Verbose error handling


**DAST or dynamic validation focus:**

- Security header checks
- CORS validation
- Error disclosure checks
- Exposed admin and API documentation review


**Output mapping template:**

```json
{
  "category": "A02:2025 - Security Misconfiguration",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A03:2025: Software Supply Chain Failures

**Description:** Compromise or weakness in dependencies, build systems, CI/CD, package managers, artifacts, plugins, containers, or distribution infrastructure.


**Architecture indicators:**

- Unpinned dependencies
- Unsigned build artifacts
- Unknown SBOM
- Third-party packages with broad install scripts
- CI/CD secrets shared broadly


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Are dependencies inventoried and pinned?
- Are build artifacts signed and provenance-attested?
- Are CI/CD identities least privileged?


**Recommended mitigations:**

- SBOM generation
- SCA and container scanning
- Signed artifacts and provenance
- Dependency pinning
- Protected build identities
- Release approvals


**SAST or static review focus:**

- Unsafe build scripts
- Dependency manifests
- Insecure package sources
- Hardcoded CI/CD credentials


**DAST or dynamic validation focus:**

- Version exposure review
- Dependency risk validation through approved scanning
- Runtime component inventory validation


**Output mapping template:**

```json
{
  "category": "A03:2025 - Software Supply Chain Failures",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A04:2025: Cryptographic Failures

**Description:** Weaknesses in encryption, key management, transport security, certificate validation, hashing, randomness, or protection of sensitive data.


**Architecture indicators:**

- TLS not documented
- Custom crypto
- Hardcoded keys
- Weak password hashing
- Secrets outside managed stores


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- What data requires encryption in transit and at rest?
- How are keys generated, stored, rotated, and revoked?


**Recommended mitigations:**

- Modern TLS
- Managed key vaults
- Strong password hashing
- No custom cryptography
- Key rotation
- Certificate validation


**SAST or static review focus:**

- Weak algorithms
- Disabled certificate validation
- Hardcoded keys
- Insecure random
- Custom crypto


**DAST or dynamic validation focus:**

- TLS configuration validation
- Sensitive data exposure review
- Cookie and transport flag checks


**Output mapping template:**

```json
{
  "category": "A04:2025 - Cryptographic Failures",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A05:2025: Injection

**Description:** Untrusted input is interpreted as commands, queries, expressions, templates, or executable content.


**Architecture indicators:**

- Dynamic SQL or NoSQL
- Command execution
- Template rendering
- Expression language use
- User content rendered in browser


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Where does untrusted input enter interpreters?
- Are parameterized APIs and context-aware encoding used?


**Recommended mitigations:**

- Parameterized queries
- Input validation
- Output encoding
- Avoid unsafe dynamic evaluation
- Safe query builders


**SAST or static review focus:**

- SQL/NoSQL injection
- Command injection
- Template injection
- XSS sinks
- Unsafe eval


**DAST or dynamic validation focus:**

- Injection fuzzing within scope
- XSS validation
- Query and command manipulation checks in authorized systems


**Output mapping template:**

```json
{
  "category": "A05:2025 - Injection",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A06:2025: Insecure Design

**Description:** Missing or ineffective security design controls, including failures to model abuse cases, authorization architecture, anti-automation, isolation, or resilience.


**Architecture indicators:**

- No threat model
- No abuse-case controls
- Security decisions made in clients
- No tenant isolation model
- Weak recovery flows


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- What abuse cases were designed against?
- Which controls must be built into architecture rather than patched into code?


**Recommended mitigations:**

- Threat modeling
- Secure design patterns
- Abuse-case requirements
- Reference architectures
- Defense-in-depth reviews


**SAST or static review focus:**

- Missing central policy enforcement
- Client-only controls
- Unsafe state transitions
- Workflow bypass patterns


**DAST or dynamic validation focus:**

- Business logic abuse testing
- Workflow bypass tests
- Recovery flow validation
- Anti-automation checks


**Output mapping template:**

```json
{
  "category": "A06:2025 - Insecure Design",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A07:2025: Authentication Failures

**Description:** Weak identity proofing, login, session management, token handling, credential recovery, or authentication lifecycle controls.


**Architecture indicators:**

- Custom authentication
- JWT validation gaps
- No MFA for privileged flows
- Weak reset flows
- Session cookie protections unknown


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- How are tokens validated and sessions bound?
- Are sensitive actions protected by step-up authentication?


**Recommended mitigations:**

- Strong authentication
- MFA or step-up where appropriate
- Secure session lifecycle
- Password hashing
- Token issuer/audience/expiry validation


**SAST or static review focus:**

- JWT/OIDC validation issues
- Weak password storage
- Insecure session cookies
- Custom auth logic


**DAST or dynamic validation focus:**

- JWT tampering
- Expired token reuse
- Session fixation
- Credential recovery flow tests


**Output mapping template:**

```json
{
  "category": "A07:2025 - Authentication Failures",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A08:2025: Software or Data Integrity Failures

**Description:** Failures to preserve integrity of code, updates, artifacts, data, serialized objects, configuration, or automation workflows.


**Architecture indicators:**

- Unsafe deserialization
- Unsigned updates
- Untrusted plugins
- Mutable deployment artifacts
- Unverified messages


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Are data and artifacts integrity-protected across trust boundaries?
- Are update and deployment paths signed and verified?


**Recommended mitigations:**

- Signed builds
- Artifact provenance
- Safe deserialization
- Message signing for high-risk flows
- Immutable deployment artifacts


**SAST or static review focus:**

- Unsafe deserialization
- Untrusted dynamic loading
- CI/CD tampering risks
- Message validation gaps


**DAST or dynamic validation focus:**

- Workflow tampering validation
- Deserialization behavior review without exploit payloads
- Update integrity checks


**Output mapping template:**

```json
{
  "category": "A08:2025 - Software or Data Integrity Failures",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A09:2025: Security Logging and Alerting Failures

**Description:** Insufficient logging, alerting, correlation, retention, or response readiness for security-relevant events.


**Architecture indicators:**

- No audit trail for admin actions
- No alerting
- Logs lack actor or object ID
- Sensitive data in logs
- No centralized correlation


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Which events require auditability and alerting?
- Are logs tamper-resistant and actionable?


**Recommended mitigations:**

- Centralized logging
- Structured audit events
- Alerting for high-risk behaviors
- Retention policy
- Tamper-resistant storage


**SAST or static review focus:**

- Missing audit calls
- Sensitive logging
- Swallowed security exceptions
- No correlation IDs


**DAST or dynamic validation focus:**

- Verify security events are logged
- Denied access logging
- Alert generation in test environment


**Output mapping template:**

```json
{
  "category": "A09:2025 - Security Logging and Alerting Failures",
  "mapped_threats": [],
  "mapped_graph_nodes": [],
  "mapped_graph_edges": [],
  "sast_recommendations": [],
  "dast_recommendations": [],
  "action_items": []
}
```

---

## A10:2025: Mishandling of Exceptional Conditions

**Description:** Unsafe behavior during errors, exceptions, timeouts, retries, partial failures, edge cases, or abnormal operating conditions.


**Architecture indicators:**

- Fail-open behavior
- Verbose exception leakage
- Unbounded retries
- Timeouts undocumented
- Partial transaction failures


**Threat modeling questions:**

- Which graph nodes and data flows are affected?
- What evidence confirms that the control exists?
- What sensitive data, user groups, tenants, or privileges are affected?
- What residual risk remains after planned controls?
- Does the system fail closed for security decisions?
- Are timeout, retry, and exception paths explicitly tested?


**Recommended mitigations:**

- Fail-closed defaults
- Consistent error handling
- Bounded retries
- Transaction rollback
- Safe exception messages
- Chaos/resilience testing


**SAST or static review focus:**

- Catch-all exception handlers
- Fail-open branches
- Unbounded retry loops
- Verbose error disclosure


**DAST or dynamic validation focus:**

- Error handling validation
- Timeout and retry behavior tests
- Malformed input and boundary-condition testing


**Output mapping template:**

```json
{
  "category": "A10:2025 - Mishandling of Exceptional Conditions",
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

Based on the OWASP Top 10:2025 release page and introduction. Verify against the official OWASP page before freezing compliance mappings.
