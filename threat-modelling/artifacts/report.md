# Threat Model Report: Mobile Banking Platform

_Generated: 2026-08-10T00:00:00Z | Schema version: 1.0 | Assessment type: Full_

## 1. Executive Summary

**Overall risk: Critical**

The platform's primary path (Mobile App -> API Gateway -> Account API -> Account Database) is reasonably controlled, but a legacy offline-sync path lets the mobile app write directly to the Account Database with no documented authentication, authorization, or encryption, bypassing the API Gateway entirely. Object-level authorization on the Account API and the security posture of the Admin Portal are also undocumented.

**Top risks:**

- Legacy mobile-to-database sync path bypasses the API Gateway and has no documented authentication, authorization, or encryption.

- Account API authorization model is undocumented; object-level authorization (BOLA) cannot be confirmed.

- Notification Service (third party) receives customer PII via a call with undocumented authentication.



**Key recommendations:**

- Retire the legacy mobile-to-database sync path, or route it through the API Gateway with the same authentication/authorization controls as the primary path.

- Confirm and, if missing, implement server-side object-level authorization in the Account API.

- Document and restrict Admin Portal network exposure to an admin-only network segment.


**Major unknowns:**

- Account API object-level authorization model.

- Admin Portal network exposure.

- Authentication used for the Account API -> Notification Service webhook call.



## 2. Scope

**Included:**

- Mobile Banking Platform: Mobile App, API Gateway, Account API, Account Database, Notification Service, Admin Portal


**Excluded:**


**Scoping assumptions:**

- The API Gateway terminates TLS and forwards over HTTPS internally.

- Admin Portal network exposure is not documented and is treated as unconfirmed.


## 3. Input Artifacts Reviewed


- examples/sample-architecture.md (SRC-001)



## 4. Architecture Summary

**Components:**

- Mobile App

- API Gateway

- Account API

- Account Database

- Notification Service

- Admin Portal


**Data flows:**

- Mobile App -> API Gateway (CALLS, HTTPS, OAuth2)

- API Gateway -> Account API (CALLS, HTTPS)

- Account API -> Account Database (READS_FROM, SQL)

- Mobile App -> Account Database (WRITES_TO, legacy offline sync)

- Account API -> Notification Service (SENDS_DATA_TO, HTTPS webhook)

- Admin Portal -> Account Database (ADMINISTERS, HTTPS)


**Technology profile:** Cloud: Unknown | Application types: mobile, web, api | Identity: OAuth2 | Data stores: SQL | Security domains: web, api, mobile

## 5. Security Knowledge Graph Summary

- Nodes: 3
- Edges: 2
- High-risk graph patterns flagged: 2


- **GRP-001** (Critical): Internet-exposed 'API Gateway' can reach data store 'Account Database'

- **GRP-003** (High): Authorization undocumented on call into 'Account API'


## 6. Key Assets and Data Classification


- Account Database (Customer PII, Account Balance)



## 7. Trust Boundaries


- Internet to DMZ

- DMZ to Internal Network



## 8. Assumptions and Open Questions

**Scoping assumptions:**

- The API Gateway terminates TLS and forwards over HTTPS internally.

- Admin Portal network exposure is not documented and is treated as unconfirmed.


**Open questions:**

- **Q-001** [Unanswered, risk if unknown: Critical] Does the Account API enforce object-level authorization on every account lookup, or does it rely solely on the API Gateway's OAuth2 token? _(applies to: Account API)_

- **Q-002** [Unanswered, risk if unknown: High] Is the Admin Portal restricted to a dedicated admin network segment, or reachable from the general corporate network? _(applies to: Admin Portal)_

- **Q-003** [Unanswered, risk if unknown: Critical] What authentication (if any) protects the legacy mobile-to-database offline sync path? _(applies to: Mobile App, Account Database)_



## 9. Questionnaire Results

| ID | Domain | Question | Status | Risk if Unknown |
|---|---|---|---|---|

| API-SEC-006 | api | Is object-level authorization enforced server-side for every operation that accesses a user-owned or tenant-owned resource? | Unanswered | Critical |

| WEB-SEC-016 | web | What kind of authorization does the application implement (RBAC, ABAC, Permission based AC, Location, etc.)? | Unanswered | High |


## 10. Threats Identified

| ID | Threat | Component | Severity | Confidence | STRIDE |
|---|---|---|---|---|---|

| T-001 | Undocumented object-level authorization in Account API | Account API | Critical | Medium | Elevation of Privilege, Information Disclosure |

| T-002 | Legacy mobile-to-database sync path bypasses API layer | Account Database | Critical | Medium | Spoofing, Tampering, Elevation of Privilege |

| T-003 | Customer PII sent to third-party Notification Service without confirmed authentication | Notification Service | High | Medium | Information Disclosure, Spoofing |



### T-001: Undocumented object-level authorization in Account API

- **Component:** Account API
- **Category:** Authorization
- **STRIDE:** Elevation of Privilege, Information Disclosure
- **Affected data:** Customer PII, Account Balance
- **Attack scenario:** An authenticated mobile user manipulates an account identifier to view or modify another customer's balance or transaction history, if the Account API relies only on the API Gateway's authentication and does not independently verify resource ownership.
- **Impact:** Unauthorized access to another customer's financial data.
- **Likelihood:** Medium | **Severity:** Critical | **Confidence:** Medium
- **Preconditions:**

  - Account API exposes account-identifier-based operations

  - Object-level authorization is undocumented at the Account API layer

- **Evidence:**

  - Known Gaps section of architecture.md flags this as an open TODO

- **Assumptions:**

  - API Gateway performs authentication only, not object-level authorization



### T-002: Legacy mobile-to-database sync path bypasses API layer

- **Component:** Account Database
- **Category:** Access Control
- **STRIDE:** Spoofing, Tampering, Elevation of Privilege
- **Affected data:** Customer PII, Account Balance
- **Attack scenario:** The mobile app writes directly to the Account Database for offline sync, bypassing the API Gateway and Account API. If the mobile client embeds direct database credentials or an unauthenticated path, any compromise of the app or its traffic grants direct write access to account data.
- **Impact:** Unauthorized read/write access to customer financial data, potentially bypassing all API-layer controls.
- **Likelihood:** High | **Severity:** Critical | **Confidence:** Medium
- **Preconditions:**

  - Mobile app has network-reachable direct access to the Account Database

  - No confirmed authentication, authorization, or encryption on this path

- **Evidence:**

  - Overview and Known Gaps sections of architecture.md; Mermaid diagram shows a direct Mobile App -> Account Database edge

- **Assumptions:**



### T-003: Customer PII sent to third-party Notification Service without confirmed authentication

- **Component:** Notification Service
- **Category:** Data Protection
- **STRIDE:** Information Disclosure, Spoofing
- **Affected data:** Customer PII
- **Attack scenario:** The Account API calls the Notification Service webhook with customer name, phone number, and transaction amount. Without confirmed request authentication, a spoofed or intercepted call path could disclose or inject notification data.
- **Impact:** Disclosure of customer PII to an unauthenticated party, or injected fraudulent notifications.
- **Likelihood:** Medium | **Severity:** High | **Confidence:** Medium
- **Preconditions:**

  - Webhook call authentication is undocumented

  - Call crosses a trust boundary to an external third party

- **Evidence:**

  - Third-Party Integrations section of architecture.md

- **Assumptions:**




## 11. Attack Paths


### AP-001: External attacker abuses the legacy sync path to reach account data directly

- **Entry point:** Mobile App
- **Path:** External User, Mobile App, Account Database
- **Required weaknesses:**

  - Legacy sync path has no confirmed authentication or authorization

  - Path bypasses API Gateway and Account API controls entirely

- **Impact:** Direct unauthorized read/write access to customer account data. | **Severity:** Critical
- **Recommended controls:**

  - Retire the legacy sync path or route it through the API Gateway

  - Require the same authentication/authorization on this path as the primary API path





## 12. Recommended Mitigations


### For T-001

**Preventive:**

- Enforce server-side object-level authorization on every Account API operation that accepts an account or customer identifier.

- Use centralized authorization middleware rather than per-endpoint checks.


**Detective:**

- Log and alert on denied authorization attempts and identifier-enumeration patterns.


**Corrective:**

- Revoke affected sessions and audit access logs if unauthorized access is confirmed.


**Compensating:**

- Add API Gateway-level checks restricting callers to their own account identifiers while the Account API fix is implemented.



### For T-002

**Preventive:**

- Retire the legacy mobile-to-database sync path.

- If it must remain, route it through the API Gateway and Account API with the same authentication, authorization, and TLS requirements as the primary path.


**Detective:**

- Alert on any direct network connection from mobile IP ranges to the Account Database.


**Corrective:**

- Rotate any credentials used by the legacy sync path immediately if it is found to be unauthenticated.


**Compensating:**

- Restrict Account Database network access to only the Account API's service identity as an interim control.



### For T-003

**Preventive:**

- Authenticate the Account API -> Notification Service webhook call (e.g., signed requests or mutual TLS).


**Detective:**

- Monitor and alert on webhook call failures or unexpected volume.


**Corrective:**


**Compensating:**

- Minimize the customer data fields sent to the Notification Service to only what is strictly required.




## 13. SAST Recommendations

| ID | Component | Focus Area | Priority |
|---|---|---|---|

| SAST-001 | Account API | Broken object-level authorization | P0 |

| SAST-002 | Mobile App | Hardcoded credentials / direct database access from a client | P0 |

| SAST-003 | Account API | Outbound webhook call authentication | P1 |



- **SAST-001** (P0) — Account API: Scan Account API controller/handler methods that accept an account or customer identifier for missing ownership/authorization checks before data access.

- **SAST-002** (P0) — Mobile App: Scan the mobile app codebase for embedded database connection strings, credentials, or direct DB client libraries.

- **SAST-003** (P1) — Account API: Review the Notification Service webhook client code for signed-request or mutual-TLS authentication and for the specific fields transmitted.


## 14. DAST Recommendations

| ID | Component | Test | Priority |
|---|---|---|---|

| DAST-001 | Account API | BOLA/IDOR testing for account resources | P0 |

| DAST-002 | Account Database | Legacy sync path authentication check | P0 |

| DAST-003 | Notification Service | Webhook call authentication and data minimization check | P1 |



### DAST-001: BOLA/IDOR testing for account resources

- **Component:** Account API
- **Objective:** Verify that an authenticated user cannot access another user's account or transaction data by modifying object identifiers.
- **Steps:**

  - Authenticate as Test User A and capture valid account resource requests.

  - Authenticate as Test User B and attempt to access User A's resources by changing identifiers.

  - Attempt safe enumeration of account identifiers within approved test data.

- **Expected secure behavior:** The API denies cross-account access without revealing whether the target identifier exists.
- **Priority:** P0
- **Safety note:** Run only against an authorized test environment or approved production-safe test accounts.


### DAST-002: Legacy sync path authentication check

- **Component:** Account Database
- **Objective:** Confirm the legacy mobile-to-database sync path requires authentication and rejects unauthenticated or replayed requests.
- **Steps:**

  - Identify the network path/protocol used by the legacy sync feature in a test environment.

  - Attempt a sync request without valid credentials/session.

  - Attempt a sync request replaying a captured request from a different test account.

- **Expected secure behavior:** Unauthenticated or replayed sync requests are rejected.
- **Priority:** P0
- **Safety note:** Test only in an authorized non-production environment with test accounts and test data.


### DAST-003: Webhook call authentication and data minimization check

- **Component:** Notification Service
- **Objective:** Confirm the Notification Service webhook call is authenticated and does not transmit more customer data than necessary.
- **Steps:**

  - Capture a live webhook call in an authorized test environment.

  - Verify presence and validity of request signing or mutual-TLS authentication.

  - Review the payload fields against the documented minimum necessary data.

- **Expected secure behavior:** The webhook call is authenticated and transmits only the minimum necessary customer data.
- **Priority:** P1
- **Safety note:** Use test/sandbox third-party endpoints where available; avoid sending real customer data during testing.



## 15. Prioritized Action Items

| ID | Title | Priority | Owner | Mapped Threats | Due |
|---|---|---|---|---|---|

| A-001 | Implement server-side object-level authorization in Account API | P0 | Unknown | T-001 | Before next production release |

| A-002 | Retire or re-secure the legacy mobile-to-database sync path | P0 | Unknown | T-002 | Immediate |

| A-003 | Authenticate and minimize data in the Notification Service webhook call | P1 | Unknown | T-003 | Next planned security backlog cycle |


## 16. Residual Risk


- **RR-001** (Medium): Admin Portal network exposure remains undocumented pending confirmation from the infrastructure team; treated as an accepted, time-boxed risk. _Accepted by: Unknown, review date: 2026-09-10_



## 17. Appendix: Extracted Graph JSON

```json
{
  "metadata": {
    "system_name": "Mobile Banking Platform",
    "schema_version": "1.0",
    "generated_at": "2026-08-10T00:00:00Z",
    "generated_by": "Threat Modelling/build_graph.py",
    "scope": "Illustrative excerpt only - run build_graph.py for the full graph.",
    "source_artifacts": [
      {
        "id": "SRC-001",
        "name": "sample-architecture.md",
        "type": "markdown",
        "location": "examples/sample-architecture.md"
      }
    ]
  },
  "nodes": [
    {
      "id": "C-002",
      "name": "API Gateway",
      "type": "APIGateway",
      "description": "Single internet-facing entry point that fronts the Account API.",
      "technology": "Kong",
      "owner": "Unknown",
      "environment": "Production",
      "internet_exposed": "Yes",
      "authentication": "OAuth2",
      "authorization": "Unknown",
      "data_classification": [],
      "trust_zone": "DMZ",
      "tags": [],
      "source_refs": [],
      "confidence": "High",
      "assumptions": []
    },
    {
      "id": "C-003",
      "name": "Account API",
      "type": "API",
      "description": "Internal service handling account balance and transfer operations.",
      "technology": "Java / Spring Boot",
      "owner": "Unknown",
      "environment": "Production",
      "internet_exposed": "No",
      "authentication": "Unknown",
      "authorization": "Unknown",
      "data_classification": [],
      "trust_zone": "Internal",
      "tags": [],
      "source_refs": [],
      "confidence": "Medium",
      "assumptions": [
        "Authorization model for object-level access is not documented."
      ]
    },
    {
      "id": "C-004",
      "name": "Account Database",
      "type": "Database",
      "description": "Stores customer account balances and PII.",
      "technology": "PostgreSQL",
      "owner": "Unknown",
      "environment": "Production",
      "internet_exposed": "No",
      "authentication": "Unknown",
      "authorization": "Unknown",
      "data_classification": [
        "Customer PII",
        "Account Balance"
      ],
      "trust_zone": "Internal",
      "tags": [],
      "source_refs": [],
      "confidence": "High",
      "assumptions": []
    }
  ],
  "edges": [
    {
      "id": "DF-002",
      "from": "C-002",
      "to": "C-003",
      "relationship": "CALLS",
      "protocol": "HTTPS",
      "port": "Unknown",
      "authentication": "Unknown",
      "authorization": "Unknown",
      "data_classification": [],
      "crosses_trust_boundary": "No",
      "encryption_in_transit": "Yes",
      "source_refs": [],
      "confidence": "High",
      "assumptions": []
    },
    {
      "id": "DF-003",
      "from": "C-003",
      "to": "C-004",
      "relationship": "READS_FROM",
      "protocol": "SQL",
      "port": "Unknown",
      "authentication": "Unknown",
      "authorization": "Unknown",
      "data_classification": [
        "Customer PII",
        "Account Balance"
      ],
      "crosses_trust_boundary": "No",
      "encryption_in_transit": "Unknown",
      "source_refs": [],
      "confidence": "High",
      "assumptions": []
    }
  ],
  "risk_patterns": [
    {
      "id": "GRP-001",
      "title": "Internet-exposed 'API Gateway' can reach data store 'Account Database'",
      "description": "'API Gateway' is marked internet-exposed and a forward data-flow path reaches 'Account Database' (Database) within 2 hop(s).",
      "severity": "Critical",
      "graph_refs": {
        "nodes": [
          "C-002",
          "C-003",
          "C-004"
        ],
        "edges": [
          "DF-002",
          "DF-003"
        ]
      },
      "evidence": [
        "node C-002 internet_exposed=Yes",
        "reachable target C-004"
      ]
    },
    {
      "id": "GRP-003",
      "title": "Authorization undocumented on call into 'Account API'",
      "description": "The call from 'API Gateway' to 'Account API' has no documented authorization model.",
      "severity": "High",
      "graph_refs": {
        "nodes": [
          "C-002",
          "C-003"
        ],
        "edges": [
          "DF-002"
        ]
      },
      "evidence": [
        "edge DF-002 authorization=Unknown, target type=API"
      ]
    }
  ]
}
```

## 18. Appendix: Evidence Mapping


- SRC-001 section 'Known Gaps' -> T-001, T-002 (documented TODO/assumption lines)

- SRC-001 Mermaid diagram in 'Data Flow' -> DF-001..DF-006 and the graph nodes/edges above

- SRC-001 section 'Third-Party Integrations' -> T-003


