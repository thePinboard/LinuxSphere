# Third-party technology acknowledgements

LinuxSphere builds on independently maintained technologies. Listing a component is an acknowledgement of its technical role, **not** an endorsement, a license grant, or proof of a complete dependency audit.

| Project | Role in LinuxSphere | License action |
| --- | --- | --- |
| Debian GNU/Linux | Base operating system and installer | Preserve applicable per-package licenses and distribution duties |
| Linux kernel | Host kernel, drivers and virtualization facilities | Follow applicable Linux/kernel license terms |
| QEMU / KVM / libvirt | Guest virtualization and management | Audit actual shipped package versions and license files |
| Incus | Container runtime | Audit shipped package/license notices |
| Cockpit | Host web administration integration | Audit installed distribution package notices |
| Restic | Encrypted backups | Audit installed distribution package notices |
| OpenSSH | SSH/SFTP transfer and administration | Audit installed distribution package notices |
| xterm.js and addon-fit | Browser terminal presentation | Retain upstream license copies bundled in `console/vendor/` |

**Important:** This list is *not* an exhaustive Software Bill of Materials. Use the Debian package manifest and the complete ISO filesystem for an authoritative release inventory.
