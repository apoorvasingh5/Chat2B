# OWASP API Security Top 10 2023 Reference

## Purpose

Use this reference for REST, GraphQL, gRPC, SOAP, event-driven APIs, internal APIs, BFF layers, mobile APIs, partner APIs, and public API gateways.

## Agent Usage Instructions

- Prioritize authorization risks for object, property, and function access.
- Include API inventory and versioning in the graph.
- Treat undocumented APIs and unknown owners as security risks.
- Map each API risk to SAST and DAST recommendations.

## API1:2023: Broken Object Level Authorization

**Description:** APIs expose object identifiers and fail to enforce access checks on every object access.

**Architecture indicators:**

- Object IDs in paths or bodies
- User-owned data
- Multi-tenant resources

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Server-side object authorization
- Ownership checks
- Deny-by-default
- Centralized policy enforcement

**SAST focus:**

- Controller methods missing object auth
- Repository calls before authorization
- Tenant context from request

**DAST focus:**

- BOLA/IDOR with safe test accounts

---

## API2:2023: Broken Authentication

**Description:** Authentication is weak or incorrectly implemented, allowing identity compromise or token/session abuse.

**Architecture indicators:**

- Custom auth
- Weak token validation
- No MFA for high-risk operations

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Strong auth
- Token validation
- MFA or step-up
- Secure session lifecycle

**SAST focus:**

- JWT/OIDC validation gaps
- Weak password flows
- Session handling

**DAST focus:**

- JWT tampering
- Session fixation
- Expired token reuse

---

## API3:2023: Broken Object Property Level Authorization

**Description:** APIs expose or allow modification of object properties without property-level authorization.

**Architecture indicators:**

- Mass assignment
- Excessive response fields
- PATCH/PUT endpoints

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Response filtering
- DTO allowlists
- Field-level authorization
- Schema enforcement

**SAST focus:**

- Mass assignment
- Overexposed serializers
- Unsafe binders

**DAST focus:**

- Mass assignment
- Excessive data exposure tests

---

## API4:2023: Unrestricted Resource Consumption

**Description:** APIs allow unbounded use of compute, memory, bandwidth, storage, external calls, or paid resources.

**Architecture indicators:**

- No rate limit
- Large payloads
- Expensive queries
- Third-party paid API calls

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Rate limits
- Quotas
- Request limits
- Timeouts
- Cost guardrails

**SAST focus:**

- No timeout
- Unbounded pagination
- Large file handling

**DAST focus:**

- Rate limit and size limit validation within approved bounds

---

## API5:2023: Broken Function Level Authorization

**Description:** APIs fail to enforce authorization for functions or administrative capabilities.

**Architecture indicators:**

- Admin paths
- Role-specific APIs
- Hidden or undocumented endpoints

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Function-level policy checks
- Admin plane isolation
- Least privilege roles

**SAST focus:**

- Missing role checks
- Route-level auth gaps
- Admin action exposure

**DAST focus:**

- BFLA role and function tests

---

## API6:2023: Unrestricted Access to Sensitive Business Flows

**Description:** APIs expose business workflows that can be abused at scale even without classic implementation bugs.

**Architecture indicators:**

- Ticket purchase
- Account creation
- Posting
- Coupon redemption
- Credential recovery

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Abuse-case modeling
- Bot controls
- Velocity limits
- Fraud monitoring

**SAST focus:**

- No anti-automation hooks
- Weak workflow state checks

**DAST focus:**

- Business logic abuse simulation with approved test limits

---

## API7:2023: Server Side Request Forgery

**Description:** API fetches attacker-controlled or insufficiently validated remote resources.

**Architecture indicators:**

- URL import
- Webhooks
- Image/PDF fetch
- Cloud metadata access

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Allowlists
- Egress controls
- Private IP blocking
- Redirect validation

**SAST focus:**

- Unsafe HTTP clients
- User-controlled URL fetch

**DAST focus:**

- Safe SSRF validation against approved endpoints

---

## API8:2023: Security Misconfiguration

**Description:** API and supporting systems are deployed with unsafe headers, modes, network rules, CORS, errors, or defaults.

**Architecture indicators:**

- Swagger public
- Verbose errors
- Permissive CORS
- Default config

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Secure baselines
- API gateway policy
- CORS restrictions
- Error handling

**SAST focus:**

- Debug flags
- CORS wildcard
- Stack traces

**DAST focus:**

- Headers
- CORS
- Error handling
- API docs exposure

---

## API9:2023: Improper Inventory Management

**Description:** APIs are undocumented, unmanaged, outdated, duplicated, deprecated, or missing owners.

**Architecture indicators:**

- Shadow APIs
- Legacy versions
- Unknown owner
- No schema inventory

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- API inventory
- Version lifecycle
- Owner mapping
- Discovery
- Deprecation policy

**SAST focus:**

- Unreferenced routes
- Old versions
- Debug endpoints

**DAST focus:**

- API discovery and deprecated endpoint validation

---

## API10:2023: Unsafe Consumption of APIs

**Description:** The system trusts third-party APIs, responses, webhooks, schemas, or errors without sufficient validation and isolation.

**Architecture indicators:**

- Partner APIs
- Webhook consumers
- Third-party data controls decisions

**Threat modeling questions:**

- Which API operations are exposed?
- Which identities can call them?
- Which objects, properties, functions, and business flows are protected?
- Are controls enforced in API code, gateway policy, or both?
- What is unknown?

**Recommended mitigations:**

- Validate third-party data
- Timeouts
- Schema checks
- Isolation
- Trust boundaries

**SAST focus:**

- Unchecked third-party responses
- Unsafe deserialization
- No timeout

**DAST focus:**

- Third-party failure and malformed response simulation

---

