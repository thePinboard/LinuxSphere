# Frequently asked questions

**Is LinuxSphere a standalone operating-system installation?**  
It is distributed as an installable x86-64 Debian-based server image with LinuxSphere host services and an administrative web interface. It does not replace the Debian/Linux kernel model.

**Is the web dashboard a traditional desktop?**  
No. It is a web administration console for the host and guests.

**Do I need an internet connection to install?**  
The ISO guide describes offline installation and a bundled minimal test container image. Additional packages, updates and guest images may require network access. Verify the exact workflow on your test hardware.

**Which languages are built in?**  
English, German, French and Spanish. Browser interface language and host locale can be configured separately, and additional translation packs can be installed.

**Can I run Windows or Linux guests?**  
LinuxSphere exposes generic x86 PC virtualization through QEMU/libvirt. Actual guest OS compatibility depends on licensing, the image, firmware, drivers and available resources; no blanket compatibility certification is claimed.

**Can multiple servers act as one enormous VM?**  
No. SphereFusion distributes independent jobs among worker containers. A single guest's CPU and RAM stay on its host.

**Is live migration or automatic failover available?**  
Not as a verified general production capability in this preview.

**What does DroidSphere add?**  
A separate Android-based local VM manager. Supported powered-off x86 PC guests can be transferred to LinuxSphere through encrypted SphereLink capsules.

**How is administration secured?**  
Use trusted networks/VPN, host accounts, elevated privileges only when necessary, paired node credentials, fingerprint validation, and independent encryption keys for backups. See `SECURITY.md`.

**Is this production-ready or security-certified?**  
No. Treat v0.2 as a development preview until a published test matrix, long-running hardware trials, recovery testing and external security review are available.

**Is the repository open-source?**  
An explicit reviewed license for the original LinuxSphere sources is required before making that claim. Included third-party libraries and Debian components retain their upstream licenses.
