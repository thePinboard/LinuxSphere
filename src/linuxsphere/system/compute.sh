#!/bin/sh
set -eu
if ! virsh -c qemu:///system net-info default >/dev/null 2>&1; then
 virsh -c qemu:///system net-define /usr/share/libvirt/networks/default.xml
fi
virsh -c qemu:///system net-autostart default
if ! virsh -c qemu:///system net-list --name | grep -qx default; then virsh -c qemu:///system net-start default; fi
incus admin waitready --timeout=90
if ! incus storage show default >/dev/null 2>&1; then incus storage create default dir; fi
if ! incus network show lsbr0 >/dev/null 2>&1; then incus network create lsbr0 ipv4.address=auto ipv4.nat=true ipv6.address=none; fi
if ! incus profile device get default root path >/dev/null 2>&1; then incus profile device add default root disk path=/ pool=default; fi
if ! incus profile device get default eth0 network >/dev/null 2>&1; then incus profile device add default eth0 nic network=lsbr0 name=eth0; fi
if ! incus image info sphere-mini >/dev/null 2>&1; then incus image import /usr/lib/linuxsphere/sphere-mini.tar.gz --alias sphere-mini; fi
