# Contributing to LinuxSphere

Thank you for improving the project. Contributions are especially helpful in **documentation, translations, reproducible test cases, accessibility and security hardening**.

## Before opening a pull request

1. Review the [project status](docs/PROJECT_STATUS.md), [roadmap](docs/ROADMAP.md) and existing issues.
2. Describe the problem or goal; distinguish confirmed behavior from expected behavior.
3. Keep patches small and focused. Provide commands/tests to reproduce and validate changes.
4. Never commit secrets, personal data, disk images with credentials or proprietary assets.
5. Update relevant English/German documentation when changing public behavior; for UI strings, keep language-pack keys and placeholders consistent.
6. Include third-party attribution and license information for new dependencies. A final license decision for original LinuxSphere code is still pending.

## Good first contributions

- Reproduce installation on BIOS and UEFI test machines.
- Improve user-facing errors for guest/network operations.
- Translate UI strings while preserving placeholders such as `{node}`.
- Report verified results for recovery, guest compatibility and security boundaries.

## Reporting a bug

Use the repository's bug-report template. Share LinuxSphere version, host configuration, steps, expected/observed behavior and sanitized logs; never include passwords, API tokens, SSH keys or private pairing codes.

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security-sensitive findings must follow [SECURITY.md](SECURITY.md).
