# Security policy

## Reporting a vulnerability

Please do not open a public issue containing a security vulnerability, credentials, secrets, identifiable patient information, or protected health information.

Until a dedicated security contact is published, use GitHub's private vulnerability reporting feature for this repository when available.

Include:
- affected version/commit;
- minimal reproduction steps;
- expected and observed behavior;
- potential safety/security impact;
- whether any real patient or sensitive data was involved (do not include that data).

## Medical-AI safety issues

Treat any route that could incorrectly permit a high-risk clinical capability, bypass human review, leak clinical data, or silently weaken a safety invariant as security/safety-sensitive.

## Supported versions

Before the first stable release, only the latest tagged release is supported.

## Data handling

Use synthetic or appropriately de-identified test data. Never include real patient identifiers in issues, pull requests, logs, fixtures, benchmark submissions, or vulnerability reports.
