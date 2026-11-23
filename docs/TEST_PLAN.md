# Proposed validation matrix (not completed test results)

Record each test with ISO digest, host hardware/VM configuration, date, exact commands, expected/actual outcome and logs with secrets removed.

| ID | Test | Minimum acceptance criterion | Current reporting status |
| --- | --- | --- | --- |
| INS-01 | BIOS and UEFI installation | Both boot and allow a user to reach the dashboard | Needs v0.2 report |
| INS-02 | Role selection | All four roles configure intended services | Needs v0.2 report |
| INS-03 | Locale | EN, DE, FR, ES pages and host setting work | Needs v0.2 report |
| VM-01 | Guest boot | BIOS and UEFI VM launch; console responds | Needs v0.2 report |
| VM-02 | Resources | CPU/RAM adjustments and SafeChange rollback | Needs v0.2 report |
| CT-01 | Container | Incus create, start, shell, stop, delete | Needs v0.2 report |
| NODE-01 | Pairing | Join, invalid/expired invite, token revoke | Needs v0.2 report |
| FUS-01 | Job | Two distinct unprivileged worker jobs and results | Needs v0.2 report |
| BAK-01 | Restore | Stopped VM / container backup and off-host restore | Needs v0.2 report |
| SEC-01 | Access | Unauthenticated/invalid token requests rejected | Needs v0.2 report |
| SPH-01 | Capsule | Valid x86 `.dscap` imported; corruption rejected | Needs v0.2 report |
| OPS-01 | Stability | Monitoring and guest operations under sustained load | Needs v0.2 report |

Never post actual keys, passwords or private host information in public test logs.
