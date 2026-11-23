# LinuxSphere v0.2 installer source snapshot

This directory is an **extracted snapshot of the project-specific `linuxsphere/system/` tree inside the existing LinuxSphere VE 0.2 International ISO**. The files were copied without modifying source contents, except that the binary `sphere-mini.tar.gz` offline test image was deliberately excluded from this GitHub source bundle pending its own redistribution review.

Location inside the ISO: `linuxsphere/system/`. After installation: `/usr/lib/linuxsphere/`.

**This is not a verified end-to-end source build:** Debian packages, BIOS/UEFI bootloader integration, original installer build scripts, an explicit dependency lockfile and reproducible-ISO automation are not included here. The existing ISO is a separate release artifact and must be distributed through GitHub Releases after licensing/redistribution checks.

The bundled browser terminal vendor files include the original `xterm.LICENSE` and `addon-fit.LICENSE`; retain those notices.

For repo licensing decisions see [`docs/LICENSING.md`](../docs/LICENSING.md).
