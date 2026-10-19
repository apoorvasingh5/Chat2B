# OWASP Mobile Top 10 2024 Reference

## Purpose

Use this reference for mobile applications, mobile APIs, device-bound workflows, mobile CI/CD, SDK integrations, and mobile data handling.

## Agent Usage Instructions

- Apply this reference when the architecture includes Android, iOS, cross-platform mobile apps, mobile SDKs, device authentication, app attestation, or mobile-specific backend APIs.
- Treat client-side controls as defense-in-depth, not as authoritative security enforcement.
- Always map mobile risks to backend implications.

## M1:2024: Improper Credential Usage

**Description:** Credentials, tokens, API keys, or secrets are hardcoded, stored insecurely, reused, or transmitted carelessly in the mobile app or related backend flows.

**Architecture indicators:**

- Hardcoded API keys
- Tokens stored in plaintext
- Credentials in logs
- No rotation strategy

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Never hardcode secrets
- Use platform secure storage
- Use short-lived tokens
- Bind tokens where appropriate
- Rotate and revoke credentials

**SAST or mobile static analysis focus:**

- Hardcoded secrets
- Insecure storage APIs
- Credential logging

**DAST or mobile dynamic testing focus:**

- Token replay checks
- Backend rejects stale or invalid tokens
- Mobile API abuse tests

---

## M2:2024: Inadequate Supply Chain Security

**Description:** Third-party SDKs, packages, build systems, signing keys, or distribution channels introduce risk.

**Architecture indicators:**

- Unknown SDK inventory
- No dependency review
- Unsigned builds
- Uncontrolled CI/CD

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- SBOM
- SCA
- SDK review
- Build signing
- Protected signing keys

**SAST or mobile static analysis focus:**

- Vulnerable dependencies
- Unsafe SDK calls
- Build script tampering

**DAST or mobile dynamic testing focus:**

- Version disclosure and dependency risk validation

---

## M3:2024: Insecure Authentication/Authorization

**Description:** Mobile or backend controls fail to authenticate users, devices, sessions, or authorize access correctly.

**Architecture indicators:**

- Client-side role checks
- Weak session controls
- Missing object-level auth
- No step-up for sensitive actions

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Server-side authz
- MFA or biometrics where suitable
- OAuth/OIDC hardening
- Session protection

**SAST or mobile static analysis focus:**

- Client-side authorization
- JWT validation
- Missing backend authorization

**DAST or mobile dynamic testing focus:**

- BOLA
- Role bypass
- Session management
- Token tampering

---

## M4:2024: Insufficient Input/Output Validation

**Description:** Mobile app or APIs do not validate inputs, outputs, deep links, IPC data, files, or server responses.

**Architecture indicators:**

- Unsafe deep links
- Unvalidated API responses
- File handling
- WebView input

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Schema validation
- Output encoding
- Safe WebView configuration
- Deeplink validation

**SAST or mobile static analysis focus:**

- Unsafe WebView sinks
- Path traversal
- Injection points
- Deserialization

**DAST or mobile dynamic testing focus:**

- Deep link abuse
- Input fuzzing within scope
- File handling tests

---

## M5:2024: Insecure Communication

**Description:** Sensitive data is exposed or modified because transport security is weak or not enforced.

**Architecture indicators:**

- HTTP endpoints
- Certificate validation disabled
- No TLS pinning for high-risk apps
- Weak TLS

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- TLS everywhere
- Certificate validation
- Certificate pinning where appropriate
- No sensitive data in URLs

**SAST or mobile static analysis focus:**

- Disabled cert validation
- Cleartext traffic allowed
- Weak TLS config

**DAST or mobile dynamic testing focus:**

- Proxy-based transport validation
- TLS enforcement
- Certificate validation behavior

---

## M6:2024: Inadequate Privacy Controls

**Description:** The app collects, stores, shares, or exposes personal data beyond user expectations or regulatory requirements.

**Architecture indicators:**

- Broad data collection
- Third-party trackers
- No consent evidence
- Sensitive data in analytics

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Data minimization
- Consent controls
- Privacy reviews
- PII masking
- Retention controls

**SAST or mobile static analysis focus:**

- Sensitive analytics logging
- Overcollection
- PII in crash reports

**DAST or mobile dynamic testing focus:**

- PII leakage in network traffic
- Analytics and crash report review

---

## M7:2024: Insufficient Binary Protections

**Description:** The mobile binary lacks resilience against reverse engineering, tampering, repackaging, or runtime manipulation for the app's risk level.

**Architecture indicators:**

- High-value app with no tamper detection
- No obfuscation
- Root/jailbreak risks unaddressed

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Obfuscation
- Anti-tamper controls
- Runtime integrity checks
- Fraud monitoring
- Server-side enforcement

**SAST or mobile static analysis focus:**

- Debug flags
- Weak tamper checks
- Secrets in binary

**DAST or mobile dynamic testing focus:**

- Runtime manipulation checks in authorized lab
- Repackaging detection validation

---

## M8:2024: Security Misconfiguration

**Description:** Unsafe mobile, backend, cloud, build, or platform settings weaken security posture.

**Architecture indicators:**

- Debug builds
- Backup enabled for sensitive data
- Permissive network config
- Exposed backend config

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Secure build profiles
- Hardened platform config
- Least permissions
- Environment separation

**SAST or mobile static analysis focus:**

- Debuggable builds
- Backup flags
- Excess permissions

**DAST or mobile dynamic testing focus:**

- Config validation
- Security headers
- Mobile manifest review

---

## M9:2024: Insecure Data Storage

**Description:** Sensitive data is stored on the device or in caches, logs, screenshots, backups, or local databases without sufficient protection.

**Architecture indicators:**

- PII stored locally
- Tokens in shared preferences
- Sensitive screenshots
- Local cache unknown

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Secure storage
- Encryption
- Cache minimization
- No sensitive logs
- Disable backups where needed

**SAST or mobile static analysis focus:**

- Plaintext local storage
- Sensitive logs
- Improper key storage

**DAST or mobile dynamic testing focus:**

- Device storage review
- Logout and cache clearing validation

---

## M10:2024: Insufficient Cryptography

**Description:** Cryptographic controls are weak, misused, custom-built, or lack key lifecycle management.

**Architecture indicators:**

- Custom crypto
- Weak algorithms
- Static IVs
- Poor key storage

**Threat modeling questions:**

- What sensitive data exists on the device?
- Which controls are enforced server-side versus only in the app?
- What assumptions are being made about device trust?
- What happens if the app is reverse engineered, modified, or run on a compromised device?

**Recommended mitigations:**

- Use vetted libraries
- Strong algorithms
- Secure key management
- Rotation
- No custom crypto

**SAST or mobile static analysis focus:**

- Weak algorithms
- Insecure random
- Static keys
- ECB mode

**DAST or mobile dynamic testing focus:**

- Crypto configuration validation
- Transport and storage protection checks

---

