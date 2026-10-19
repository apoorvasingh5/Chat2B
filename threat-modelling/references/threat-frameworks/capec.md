# CAPEC (Common Attack Pattern Enumeration and Classification) Reference

## Purpose

CAPEC sits between CWE (a weakness in code/design) and MITRE ATT&CK (a
post-compromise adversary technique): it describes the **attack pattern** --
the mechanism an attacker actually uses to exploit a weakness. It is the
right level of detail for most application-layer threats this skill
identifies (injection, authentication/authorization bypass, CSRF, SSRF,
deserialization), which is exactly where `mitre-attack.md` notes ATT&CK
often has no clean 1:1 technique.

Every Threat object already carries a `cwe` array (SKILL.md Sec 8/11). CAPEC
IDs are the natural next field to attach: CWE says *what's wrong*, CAPEC
says *how it gets exploited*, ATT&CK (where it applies) says *what the
adversary does with it afterward*.

## How the Agent Should Use This File

1. **Use the deterministic lookup, not memory.** Once a threat's CWEs are
   known (Sec 11, same point `recommend_sast_queries.py` runs), run
   `scripts/map_attack_techniques.py --cwes <list>`. It returns the matching
   CAPEC ID(s) from `attack-technique-map.json` plus any further-derived
   ATT&CK technique(s), or an explicit `no_seed_mapping` result if the CWE
   isn't in the (small, curated) seed table. Do not invent a CAPEC ID for an
   unmapped CWE -- leave it unmapped and, if it matters, note it as an open
   question to verify against https://capec.mitre.org.
2. **Add a `capec` array to each Threat object** alongside its existing
   `cwe` array, populated from the script's output.
3. **The seed table is intentionally small and labeled `"seed-unverified"`.**
   It only covers the CWEs SKILL.md Sec 11 already names explicitly (SQLi,
   XSS, CSRF, hardcoded credentials, SSRF, XXE, insecure deserialization,
   broken/missing authorization). Treat any CWE/CAPEC pairing not in the
   table as needing manual lookup, not as "no CAPEC pattern exists."

## Curated Attack Patterns

### CAPEC-1: Accessing Functionality Not Properly Constrained by ACLs

**Mechanism:** The attacker accesses functionality or resources that should
be restricted, because the access control check is missing, misconfigured,
or enforced only on the client.

**Maps to:** CWE-862 (Missing Authorization), CWE-863 (Incorrect
Authorization).

**Architecture indicator:** `unknown_authorization_on_api_call` risk
pattern -- an API/gateway call with no documented authorization model.

**No clean ATT&CK equivalent** -- this is an application-logic gap, not an
intrusion-lifecycle technique.

---

### CAPEC-66: SQL Injection

**Mechanism:** Attacker-controlled input is concatenated into a SQL
statement without parameterization, altering query logic.

**Maps to:** CWE-89. **ATT&CK:** T1190 (Exploit Public-Facing Application)
when reachable from an internet-facing component.

---

### CAPEC-63: Cross-Site Scripting (XSS)

**Mechanism:** Attacker-controlled input is rendered in a victim's browser
without encoding/sanitization, executing in the victim's session context.

**Maps to:** CWE-79. **ATT&CK:** T1189 (Drive-by Compromise) for the
client-side execution step.

---

### CAPEC-62: Cross Site Request Forgery

**Mechanism:** A victim's authenticated browser session is used to submit
an attacker-crafted request without the victim's intent, because the
server does not verify request origin/intent (no anti-CSRF token, no
SameSite cookie enforcement).

**Maps to:** CWE-352. No ATT&CK equivalent -- this exploits browser trust,
not infrastructure.

---

### CAPEC-37: Retrieve Embedded Sensitive Data

**Mechanism:** Secrets (API keys, credentials, tokens) are embedded in
client binaries, mobile app packages, config files, or source and are
recovered by an attacker with access to the artifact.

**Maps to:** CWE-798 (Hardcoded Credentials). **ATT&CK:**
T1552.001 (Unsecured Credentials: Credentials In Files).

**Architecture indicator:** `secret_used_outside_managed_store` /
`mobile_app_direct_database_access` risk patterns.

---

### CAPEC-664: Server-Side Request Forgery

**Mechanism:** Attacker supplies or influences a URL/host that a server-side
component fetches, reaching internal services, cloud metadata endpoints, or
otherwise-unreachable network zones.

**Maps to:** CWE-918. **ATT&CK:** T1190, often chained with T1526 (Cloud
Service Discovery) if it reaches a cloud metadata endpoint.

---

### CAPEC-221: Data Serialization External Entities Blowup

**Mechanism:** An XML parser resolves external entities, allowing file
disclosure, SSRF, or denial of service via entity expansion. (Closest
published CAPEC pattern to "XXE" as commonly described -- verify against
capec.mitre.org for the current canonical entry.)

**Maps to:** CWE-611.

---

### CAPEC-586: Object Injection

**Mechanism:** Untrusted serialized data is deserialized without validation,
allowing the attacker to construct objects/gadget chains that execute
unintended code or logic.

**Maps to:** CWE-502. No standalone ATT&CK technique -- the resulting
impact (typically remote code execution) is usually described via T1190
or T1059 depending on what the gadget chain achieves.

---

### CAPEC-122: Privilege Abuse

**Mechanism:** A legitimate but over-broad grant of privilege (role, IAM
policy, service account) is used beyond its intended purpose, rather than
bypassing access control outright.

**Maps to:** CWE-269 (Improper Privilege Management), CWE-284 (Improper
Access Control). **ATT&CK:** T1078 (Valid Accounts), T1078.004 for cloud
accounts specifically.

**Architecture indicator:** `serverless_function_undocumented_permissions`,
`kubernetes_workload_undocumented_identity` risk patterns.

---

### CAPEC-115: Authentication Bypass

**Mechanism:** An attacker circumvents the authentication mechanism itself
(logic flaw, default credentials, missing enforcement on an alternate
path) rather than presenting valid credentials.

**Maps to:** CWE-287 (Improper Authentication), CWE-306 (Missing
Authentication for Critical Function). **ATT&CK:** T1078 (Valid Accounts)
once bypassed access is used.

---

### CAPEC-233: Privilege Escalation

**Mechanism:** An attacker with limited privileges manipulates the system
(role assignment, token claims, container escape) to obtain higher
privileges than originally granted.

**Maps to:** CWE-269. **ATT&CK:** T1548 (Abuse Elevation Control
Mechanism), T1611 (Escape to Host) in container contexts.

## Threat Object Field Addition

Add `capec` alongside the existing `cwe` array:

```json
{
  "id": "T-001",
  "cwe": ["CWE-862"],
  "capec": ["CAPEC-1"],
  "attack_techniques": []
}
```

An empty `attack_techniques` array with CWE/CAPEC populated is a valid,
expected result for application-logic threats -- it is not a gap to fill
in by guessing.

## See Also

- `mitre-attack.md` in this directory, for the post-compromise/intrusion-
  lifecycle techniques CAPEC patterns sometimes lead into.
- `scripts/map_attack_techniques.py` and `attack-technique-map.json` for
  the deterministic lookup.
