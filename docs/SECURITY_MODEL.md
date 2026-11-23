# Security model and deployment boundaries

This is an architectural summary, not an audited security specification.

## Trust domains

1. **Host:** Debian services and administrative users; privileged operations require appropriately authorized elevation.
2. **Management:** Cockpit session on HTTPS TCP 9090 and node API on HTTPS TCP 9443.
3. **Guests:** QEMU/libvirt VMs and Incus containers, isolated according to their virtual networking and host configurations.
4. **Storage/recovery:** Restic archives, encrypted repository secrets and transfer destinations over SSH/SFTP.
5. **Mobile peer:** Separately administered DroidSphere Android app, whose HTTPS service should be explicitly enabled and authenticated.

## Operational controls

- Keep administration behind **trusted LAN and/or VPN**; do not expose 9090, 9443 or SSH without a deliberate firewall and authentication design.
- Verify TLS certificate fingerprints and SSH host keys out of band when pairing.
- Use short-lived node invitations and revoke credentials after device disposal or compromise.
- Rotate/restrict host accounts and review sudo rights. A paired node does not automatically imply unrestricted shell login.
- Back up and protect Restic keys and host SSH credentials separately from backup data.
- Before a backup, stop a guest cleanly where guest consistency is required. Regularly test restores as new guests.
- Do not upload live secrets, credentials, paired tokens, SSH private keys or guest images containing sensitive data to GitHub.
- Disable or firewall unused listening services and track security updates.

## Design constraints

A backup snapshot is not a guaranteed application-consistent restore. An encrypted transfer is not a substitute for endpoint trust. Incus containers share the host kernel. Guest isolation depends on the hypervisor, kernel, configuration and host hardening. No formal security certification is claimed.

For reporting vulnerabilities, see [SECURITY.md](../SECURITY.md).
