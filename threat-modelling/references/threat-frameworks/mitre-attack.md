# MITRE ATT&CK Reference

## Purpose

Use this reference when building Attack Path objects (Sec 9, Attack Path
Agent) and when annotating Threat objects, so attack narratives cite real,
named ATT&CK tactics/techniques instead of generic prose like "attacker
escalates privileges."

This file is **curated, not exhaustive**. ATT&CK Enterprise alone has
roughly 200 techniques and 450+ sub-techniques; dumping all of them into
context would waste tokens and would not improve threat-modeling quality,
since most techniques describe post-compromise behavior that is irrelevant
to an architecture review (e.g. specific malware persistence mechanisms).
This file lists only the techniques that regularly show up when reasoning
about *architecture*, grouped by the ATT&CK matrix they come from.

## How the Agent Should Use This File

1. **Prefer the deterministic lookup over reasoning from this file by hand.**
   `scripts/map_attack_techniques.py` matches identified CWEs and
   `build_graph.py` risk-pattern keys against
   `references/threat-frameworks/attack-technique-map.json` and returns
   technique IDs directly. Run it once CWEs/risk patterns are known (same
   point in the workflow as `recommend_sast_queries.py`, Phase 6/7) and fold
   its `attack_techniques` output into the relevant `threats[]` and
   `attack_paths[]` objects. Do not hand-pick technique IDs from memory for
   anything the script already covers.
2. **Do not force a technique onto every threat.** Many application-logic
   weaknesses (BOLA, business-logic abuse, CSRF) have no clean 1:1 Enterprise
   ATT&CK technique -- `attack-technique-map.json` marks these explicitly
   with `why_no_attack_technique`. Citing CWE + CAPEC is enough for those;
   an invented or stretched technique ID is worse than no citation, because
   it looks authoritative while being wrong (the same discipline SKILL.md
   already requires for facts vs. assumptions).
3. **Only use this file directly (not the script) for cases the seed map
   doesn't cover** -- e.g. a technique-specific narrative detail the user
   asks about. Treat any technique ID you state from memory, rather than
   from the script's output, as an assumption to flag, and recommend the
   user verify it against https://attack.mitre.org before relying on it.
4. **Tie techniques to tactics, and tactics to the kill-chain position** of
   the attack path: an Attack Path object's `path` array already orders
   nodes from entry point to target -- map each hop to the tactic that best
   describes the attacker's goal at that hop (Initial Access at the entry
   point, Collection/Exfiltration at the data store, etc.).

## Enterprise Matrix: Tactics Relevant to Architecture Review

| Tactic ID | Tactic | When it shows up in a threat model |
|---|---|---|
| TA0001 | Initial Access | Any internet-exposed component reachable without strong authentication |
| TA0002 | Execution | Code/command execution via deserialization, injection, or CI/CD |
| TA0003 | Persistence | Backdoored CI/CD artifacts, long-lived credentials, webhook registrations |
| TA0004 | Privilege Escalation | Missing/unknown authorization, over-permissioned service identities |
| TA0005 | Defense Evasion | Disabling/bypassing logging, monitoring, or centralized gateways |
| TA0006 | Credential Access | Hardcoded secrets, secrets outside a managed store, unencrypted transit |
| TA0007 | Discovery | Enumerable object storage, exposed admin interfaces, metadata endpoints |
| TA0008 | Lateral Movement | Flat network zones, shared service accounts across trust boundaries |
| TA0009 | Collection | Reading from sensitive data stores, logs, or caches |
| TA0010 | Exfiltration | Data flows to third parties, public storage, or unmonitored egress |
| TA0011 | Command and Control | Outbound webhooks/callbacks, agent/tool-calling LLM components |
| TA0040 | Impact | Resource hijacking, ransomware-style data destruction, DoS |

## Curated Techniques by Domain

### Internet-Facing Applications and APIs

| ID | Technique | Architecture indicator |
|---|---|---|
| T1190 | Exploit Public-Facing Application | Internet-exposed API/web app with unauthenticated or weakly-authenticated path to a backend |
| T1133 | External Remote Services | VPN, RDP, SSH, or admin console reachable from outside the trust boundary |
| T1078 | Valid Accounts | Compromised or shared credentials used where authorization is otherwise unknown |
| T1557 | Adversary-in-the-Middle | Trust-boundary crossing without confirmed transport encryption |
| T1189 | Drive-by Compromise | Stored/reflected XSS served to a victim's browser |

### Cloud (IaaS)

| ID | Technique | Architecture indicator |
|---|---|---|
| T1078.004 | Valid Accounts: Cloud Accounts | Over-permissioned IAM roles, default service accounts |
| T1526 | Cloud Service Discovery | Broad IAM read permissions, exposed cloud metadata endpoints |
| T1619 | Cloud Storage Object Discovery | Internet-exposed object storage buckets/containers |
| T1530 | Data from Cloud Storage | Sensitive data reachable from a public or weakly-scoped bucket |
| T1537 | Transfer Data to Cloud Account | Data flows to an external cloud account/third party |
| T1496 | Resource Hijacking | Serverless functions or compute with broad, undocumented permissions |
| T1552 | Unsecured Credentials | Secrets used outside a managed secret store, embedded in mobile/client code |

### Containers and Kubernetes

| ID | Technique | Architecture indicator |
|---|---|---|
| T1610 | Deploy Container | CI/CD pipeline can push workloads without approval evidence |
| T1609 | Container Administration Command | Workload identity/service account undocumented |
| T1611 | Escape to Host | Default service account, privileged containers, missing pod security policy |
| T1613 | Container and Resource Discovery | Broad RBAC, missing namespace isolation |

### CI/CD and Software Supply Chain

| ID | Technique | Architecture indicator |
|---|---|---|
| T1195 | Supply Chain Compromise | CI/CD deploys to production without documented approval/provenance |
| T1195.002 | Compromise Software Supply Chain | Unsigned build artifacts, unverified third-party dependencies |
| T1199 | Trusted Relationship | Third-party integration or partner with broad, undocumented access |

### Credential and Secrets Handling

| ID | Technique | Architecture indicator |
|---|---|---|
| T1552 | Unsecured Credentials | Secrets outside a SecretStore, hardcoded config |
| T1552.001 | Credentials In Files | Secrets committed to config files or client bundles |
| T1552.004 | Private Keys | Private keys outside a managed key store |
| T1621 | Multi-Factor Authentication Request Generation | MFA fatigue risk where push-based MFA is the only control |

### Collection and Exfiltration

| ID | Technique | Architecture indicator |
|---|---|---|
| T1005 | Data from Local System | Sensitive data logged or cached without masking |
| T1213 | Data from Information Repositories | Internal wikis/ticketing systems holding sensitive architecture or credential data |
| T1567 | Exfiltration Over Web Service | Data sent to a third-party service without a documented data processing agreement |

## See Also

- **MITRE ATLAS** (https://atlas.mitre.org) is the ATT&CK-style framework
  specifically for AI/ML system threats and pairs with
  `owasp-top-10-llm.md` and `owasp-top-10-agentic-ai.md` in this directory.
  It is not yet represented as a local reference file here; treat any ATLAS
  technique ID cited in a report as unverified until checked against
  atlas.mitre.org, the same way this file's seed mappings are unverified.
- `capec.md` in this directory, for attack-pattern-level (not
  intrusion-lifecycle-level) citations that fit application-layer
  weaknesses better than ATT&CK does.
- `scripts/map_attack_techniques.py` and
  `attack-technique-map.json` for the deterministic lookup mechanism.
