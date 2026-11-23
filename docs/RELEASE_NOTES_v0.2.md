# LinuxSphere VE 0.2 International — release notes

**Suggested release title:** `LinuxSphere VE 0.2 International — Development Preview`  
**Suggested tag:** `v0.2.0`  
**Release type:** **Pre-release** (not stable/production certified)

## Highlights

- Installable Debian 13-based x86-64 image with **Hybrid**, **Manager**, **Worker** and **Storage** role options.
- Multilingual LinuxSphere dashboard with **English, German, French and Spanish** language packs; configurable host locale and custom translation pack support.
- Dedicated **CLI** area with interactive host shell and tools for VM, container and system administration.
- Browser management for host resources, guest lifecycle, node pairing, backups and distributed jobs.
- QEMU/libvirt virtual machines, optional host KVM acceleration and Incus containers.
- **SphereFusion** for explicitly distributed independent jobs.
- **SphereLink** for encrypted offline transfer/import of supported stopped DroidSphere VE 2.0 x86 PC guests.
- Restic-based encrypted backup/restore workflows and source modules for SafeChange rollback.

## Package verification

- Asset name: `LinuxSphere-VE-0.2-International-amd64.iso`
- Size: `492830720` bytes (approximately `470.0 MiB`)
- SHA-256: `0cc01ec79686cd90f0344fad62a40563a56b8857df27e57c545172e25f5fdd4a`

Verify the actual uploaded release asset against this digest; do not silently substitute a rebuilt ISO with a different hash.

## Notes for testers

- Prefer a disposable test machine or isolated VM; installer disk partitioning can delete data.
- Plan at least 2 logical CPUs, 4 GiB RAM and 20 GiB system storage, plus guest capacity.
- Access UI: `https://SERVER-IP:9090/linuxsphere` from a trusted LAN/VPN.
- Node API: TCP 9443; SSH/SFTP: TCP 22. Limit access to trusted peers.
- Current functionality is a **development preview**. Real-hardware compatibility, production security, automatic HA failover, general live migration and transparent cross-host guest RAM are not certified.

## DroidSphere

DroidSphere is a separate Android virtualization project. SphereLink enables controlled encrypted **offline** exchange of selected stopped x86 PC guest data; it is **not** native device resource pooling or general ARM guest conversion.

**Documentation:** [README](../README.md) · [Installation](en/INSTALLATION.md) · [Known limitations](PROJECT_STATUS.md)
