# SANS / CWE Top 25 Most Dangerous Software Weaknesses 2025 Reference

## Version Note

Latest checked: 2026-08-07. SANS maintains a Top 25 Software Errors page that points practitioners to CWE/MITRE entries. The latest CWE Top 25 available at the time of generation is the 2025 list.

## Agent Usage Instructions

- Use this file to map threats to secure coding, SAST, SCA, code review, and backlog priorities.
- Prefer CWE IDs in generated action items because they are stable identifiers.
- Map each CWE to affected graph nodes, code repositories, application components, and validation methods.

## 2025 Top 25 List

## 1. CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 2. CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 3. CWE-352: Cross-Site Request Forgery (CSRF)

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 4. CWE-862: Missing Authorization

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 5. CWE-787: Out-of-bounds Write

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 6. CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 7. CWE-416: Use After Free

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 8. CWE-125: Out-of-bounds Read

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 9. CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 10. CWE-94: Improper Control of Generation of Code ('Code Injection')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 11. CWE-120: Buffer Copy without Checking Size of Input ('Classic Buffer Overflow')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 12. CWE-434: Unrestricted Upload of File with Dangerous Type

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 13. CWE-476: NULL Pointer Dereference

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 14. CWE-121: Stack-based Buffer Overflow

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 15. CWE-502: Deserialization of Untrusted Data

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 16. CWE-122: Heap-based Buffer Overflow

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 17. CWE-863: Incorrect Authorization

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 18. CWE-20: Improper Input Validation

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 19. CWE-284: Improper Access Control

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 20. CWE-200: Exposure of Sensitive Information to an Unauthorized Actor

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 21. CWE-306: Missing Authentication for Critical Function

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 22. CWE-918: Server-Side Request Forgery (SSRF)

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 23. CWE-77: Improper Neutralization of Special Elements used in a Command ('Command Injection')

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 24. CWE-639: Authorization Bypass Through User-Controlled Key

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---

## 25. CWE-770: Allocation of Resources Without Limits or Throttling

**Threat modeling relevance:** This weakness should be considered when the architecture includes code paths, APIs, parsers, memory-unsafe components, authorization decisions, file handling, external input, or trust-boundary crossings related to this CWE.


**Questions for the agent:**

- Which components or repositories could contain this weakness?
- Is there an existing SAST, SCA, or manual review control mapped to this CWE?
- Is the affected path internet-facing, privileged, multi-tenant, or handling sensitive data?
- What DAST or runtime validation is safe and authorized for this weakness?


**Recommended handling:**

- Map to SAST rules or CodeQL/Semgrep equivalents where applicable.
- Add secure code review checks for affected components.
- Prioritize internet-exposed, privileged, and sensitive-data paths.
- Add DAST validation only in authorized test environments and avoid destructive payloads.

---


## Source Note

Based on the 2025 CWE Top 25 Most Dangerous Software Weaknesses list and SANS Top 25 Software Errors reference page.
