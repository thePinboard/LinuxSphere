# Project status and verification scope

**Snapshot date:** 23 November 2026. **Main artifact:** `LinuxSphere-VE-0.2-International-amd64.iso` (492,830,720 bytes, approximately 470.0 MiB).

## Evidence levels

| Classification | Meaning |
| --- | --- |
| **Present in 0.2 ISO / code** | Installer files or implementation source were inspected in the 0.2 image. This does not prove every runtime path works on physical hardware. |
| **Previously project-internally exercised** | Older project documentation describes internal tests around v0.1 / DroidSphere 2.0. Those are not independent repeats of v0.2 certification. |
| **Not verified / roadmap** | No reliable end-to-end result, benchmark or production sign-off is claimed. |

## Observed in the 0.2 image

- ISO9660 boot media with Debian 13 Trixie installer structure, BIOS and EFI boot files, and four role-specific installer configurations.
- Localized startup guides `START.txt`, `START.de.txt`, `START.fr.txt`, `START.es.txt`.
- `linuxsphere/system/` project directory with system units, Python services, Cockpit JavaScript/CSS and host language packs.
- Language packs `en`, `de`, `fr`, `es` and code paths for switching browser language, setting the host locale and adding community translations.
- Interactive terminal implementation in the browser console; source pathways for `virsh`, `incus`, SSH and host shell.
- Modules for guest lifecycle, node pairing, job execution, encrypted backups, SafeChange and DroidSphere capsule import.
- Offline test container image (`sphere-mini.tar.gz`) in the ISO. This documentation/source ZIP intentionally omits that binary.

## Previously reported internal tests

The earlier technical dossier describes internal tests of LinuxSphere 0.1 on multiple simulated nodes and DroidSphere 2.0 in an Android 17 emulator. These historical reports are not a substitute for a published, reproducible v0.2 hardware test suite.

## Outstanding validation

- No independent installation test of **v0.2** on a representative range of real x86-64 servers was performed while assembling this publishing kit.
- No signed ISO release, automated CI workflow, published SBOM, independent vulnerability assessment or reproducible build is included in this package.
- No guarantee of production high availability, automatic fencing, stable long-term clustering, general live VM migration or coherent distributed guest memory.
- No general real-smartphone performance certification for DroidSphere; Android hardware capability depends on the target device.

**Recommended release label:** *Development preview / Pre-release*.
