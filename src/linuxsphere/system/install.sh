#!/bin/sh
set -eu
role=$1
case "$role" in hybrid|worker|manager|storage);; *) exit 2;; esac
root=/usr/lib/linuxsphere
install -d -m 0755 /etc/linuxsphere /usr/share/cockpit/linuxsphere /var/lib/linuxsphere /usr/local/bin /etc/issue.d /etc/default/grub.d
install -d -m 0700 /var/lib/linuxsphere/private /var/lib/linuxsphere/backups /var/lib/linuxsphere/droid
printf '%s\n' "$role" > /etc/linuxsphere/role
install -m 0755 "$root/host/dsctl.py" /usr/local/bin/dsctl
install -m 0755 "$root/host/sphere-run" /usr/local/bin/sphere-run
install -m 0644 "$root"/console/*.js "$root"/console/*.html "$root"/console/*.css "$root"/console/*.json /usr/share/cockpit/linuxsphere/
install -d -m 0755 /usr/share/cockpit/linuxsphere/vendor /etc/linuxsphere/languages
install -m 0644 "$root"/console/vendor/* /usr/share/cockpit/linuxsphere/vendor/
install -m 0644 "$root"/units/*.service /etc/systemd/system/
install -d /etc/cockpit
cat > /etc/cockpit/cockpit.conf <<'EOF'
[WebService]
LoginTitle = LinuxSphere VE
[Session]
IdleTimeout = 30
EOF
cat > /etc/issue.d/60-linuxsphere.issue <<'EOF'
LinuxSphere VE 0.2   |   https://\4:9090/linuxsphere
Sign in with the account created during installation.
EOF
cat > /etc/profile.d/linuxsphere.sh <<'EOF'
if [ -n "${PS1:-}" ]; then
  ipaddr=$(hostname -I | awk '{print $1}')
  printf '\nLinuxSphere VE  |  %s  |  https://%s:9090/linuxsphere\n' "$(cat /etc/linuxsphere/role)" "${ipaddr:-localhost}"
  printf '  sudo dsctl --help\n\n'
fi
EOF
# Keep Debian's upstream identity in /usr/lib; publish the derivative in /etc.
rm -f /etc/os-release
cat > /etc/os-release <<'EOF'
PRETTY_NAME="LinuxSphere VE 0.2 (Debian 13)"
NAME="LinuxSphere VE"
ID=linuxsphere
ID_LIKE=debian
VERSION_ID="0.2"
VERSION_CODENAME=trixie
DEBIAN_CODENAME=trixie
EOF
cat > /etc/default/grub.d/90-linuxsphere.cfg <<'EOF'
GRUB_DISTRIBUTOR="LinuxSphere VE"
EOF
# Enable signed Debian updates for future network access. The medium is self-contained.
cat > "$root/debian-sources.list" <<'EOF'
deb https://deb.debian.org/debian trixie main non-free-firmware
deb https://deb.debian.org/debian trixie-updates main non-free-firmware
deb https://security.debian.org/debian-security trixie-security main non-free-firmware
EOF
systemctl enable cockpit.socket ssh.service linuxsphere-api.service linuxsphere-sources.service linuxsphere-language.service
case "$role" in hybrid|worker)
  install -d -m 0755 /var/lib/libvirt/images/linuxsphere /var/lib/libvirt/boot/linuxsphere
  systemctl enable linuxsphere-compute.service
;; esac

case "$role" in storage|hybrid)
 getent group linuxsphere-vault >/dev/null || addgroup --system linuxsphere-vault
 install -d -m 0755 /var/lib/linuxsphere/vault /etc/ssh/sshd_config.d
 cat > /etc/ssh/sshd_config.d/80-linuxsphere-vault.conf <<'EOF'
Match Group linuxsphere-vault
    ChrootDirectory /var/lib/linuxsphere/vault/%u
    ForceCommand internal-sftp -d /data
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    AllowTcpForwarding no
    AllowAgentForwarding no
    PermitTTY no
    X11Forwarding no
Match all
EOF
;; esac
