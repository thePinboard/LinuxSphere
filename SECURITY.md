# Security policy

LinuxSphere VE is currently a **development preview**. No vulnerability disclosure SLA, bug bounty or independent security certification is promised.

## Supported versions

| Version | Security support status |
| --- | --- |
| 0.2 International | Development preview; fixes handled on a best-effort basis |
| 0.1 and older | Not recommended for new deployments |

## Reporting a security vulnerability

**Please do not disclose exploitable vulnerabilities, credentials, secret keys, proof-of-concept attacks or private system details in public GitHub issues.**

If the GitHub repository has **Private vulnerability reporting** enabled, open the repository's **Security** tab and select **Report a vulnerability**. Otherwise, use a private contact method explicitly published by the repository owner; do not assume an email address exists.

Include affected version and digest, concise steps to reproduce, impact, expected vs actual behavior, and sanitized logs. Do not test on infrastructure you do not own or lack permission to assess.

## Deployment reminder

Keep management interfaces on a trusted LAN/VPN, restrict host accounts, maintain patching, check pairing fingerprints and back up recovery secrets separately. See [the security model](docs/SECURITY_MODEL.md).
