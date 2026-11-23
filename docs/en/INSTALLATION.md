# LinuxSphere VE 0.2 — Installation guide

> Intended for a **lab / development environment**. Back up important data first. Installation may overwrite the selected physical or virtual disk.

## Requirements

- x86-64 PC, server or virtual machine capable of booting an ISO in BIOS or UEFI mode.
- **Initial lab planning:** at least 2 logical CPUs, 4 GiB RAM and 20 GiB for the system; guest storage is additional. These are sizing suggestions, not a hardware certification matrix.
- Intel VT-x / AMD-V if KVM acceleration is desired; without available KVM access, QEMU may use slower software emulation.
- A trusted LAN and an administrative account. Ethernet is preferable during initial setup.

## 1 — Verify and boot

1. Download `LinuxSphere-VE-0.2-International-amd64.iso` from the v0.2 release **after it has been published**.
2. Verify the SHA-256 hash using the value supplied in [release asset checksums](../RELEASE_ASSET_SHA256.txt). Linux: `sha256sum LinuxSphere-VE-0.2-International-amd64.iso`; PowerShell: `Get-FileHash .\LinuxSphere-VE-0.2-International-amd64.iso -Algorithm SHA256`.
3. Mount as an ISO in a test VM, or write the ISO as an image to a **dedicated, expendable** USB stick. Imaging replaces that stick's contents.
4. Boot the test machine. Select **Install Hybrid** for the simplest first test.

## 2 — Installer choices

- Set the installer language, country and keyboard layout.
- Create a local administrative user and a strong password.
- Select the destination disk. **Double-check disk identity and partition changes**; guided use of an entire disk is destructive.
- Complete the installer, remove media and reboot.

Roles:

| Hybrid | Manager | Worker | Storage |
| --- | --- | --- | --- |
| Management + local guests | Node coordination | Local guests + jobs | Remote backup destination |

## 3 — First login

On the installed machine use `ip -br a` to find its IP address, then visit:

```text
https://SERVER-IP:9090/linuxsphere
```

Accept the HTTPS certificate **only after checking its fingerprint through a trusted local channel**. Sign in using the account created during installation. Cockpit may require enabling elevated administration for system-changing actions. Keep 9090, 9443 and 22 inside a trusted network or VPN, not directly on the public internet.

## 4 — Initial operations

- Check the Overview page: host memory, CPUs, storage and whether KVM is available.
- Open **Guests**, upload a supported guest ISO and create a small test VM; or create an Incus container from an available image.
- Open **CLI** for a full interactive host terminal. Examples: `sudo dsctl status`, `sudo virsh -c qemu:///system list --all`, `sudo incus list`.
- Open **Language** to set the current browser's UI language, or configure the Debian host locale independently.
- Use **Nodes** for invitation-based pairing; a one-time invitation is designed to expire after ten minutes.
- For first backups, power off a test guest, create a restore point and verify it by restoring under a new name.

## Network overview

| Service | Default | Recommendation |
| --- | --- | --- |
| Browser management (Cockpit) | HTTPS TCP 9090 | Restricted LAN or VPN |
| Node API | HTTPS TCP 9443 | Allow only paired / authorized nodes |
| SSH/SFTP | TCP 22 | Public-key auth and restrictive ACLs |
| VM graphics | Loopback-bound VNC | Access via management interface, not a public VNC port |

## Useful commands

```bash
sudo dsctl status
sudo dsctl nodes
sudo dsctl invite
sudo dsctl --help
sudo virsh -c qemu:///system list --all
sudo incus list
sudo nmtui
journalctl -u linuxsphere-api -u linuxsphere-compute
```

`dsctl invite` creates pairing material and must be treated as a temporary secret. Some commands and operations depend on the installed node role.

## Important limitations

Not validated as a production deployment guide. No guarantee of all-hardware guest compatibility, general live VM migration, automatic failover or transparent cross-host RAM sharing. For data integrity, use a stopped guest and test the restore path.
