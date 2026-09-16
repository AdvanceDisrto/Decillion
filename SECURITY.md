# Security policy

Report vulnerabilities privately to the repository owner rather than opening a public issue containing exploit details.

## Supported versions

The latest commit on `main` is supported during the pre-1.0 phase.

## Threat boundaries

Decillion protects stored content against disclosure and tampering when its KEK, signing key, host, and authorization plane are correctly secured. It does not claim protection after endpoint compromise, key exfiltration, malicious plaintext submission, denial of service, or a broken cryptographic dependency.

The reference API stores a node signing key beside its state and uses static tokens. Replace both with an HSM/KMS-backed signing service and OIDC or mTLS for production. External cryptographic review and penetration testing are required before custody of customer data.
