#!/bin/sh
# netcfg writes a generic Ethernet profile before copying it to the installed system.
# Keep its addresses and DNS, and bind it to the interface used for installation.
set -eu
nic=$(awk '$2 == "00000000" && $8 == "00000000" {print $1; exit}' /proc/net/route)
if [ -z "$nic" ] && [ -f /etc/network/interfaces ]; then
    nic=$(awk '$1 == "iface" && $2 != "lo" && ($3 == "inet" || $3 == "inet6") {print $2; exit}' /etc/network/interfaces)
fi
[ -n "$nic" ] && [ -f "/sys/class/net/$nic/address" ] || exit 0
[ ! -d "/sys/class/net/$nic/wireless" ] || exit 0
mac=$(cat "/sys/class/net/$nic/address")
echo "$mac" | grep -Eq '^([0-9a-f]{2}:){5}[0-9a-f]{2}$' || exit 0
profile=
for file in /etc/NetworkManager/system-connections/*; do
    [ -f "$file" ] || continue
    grep -Eq '^\[(802-3-ethernet|ethernet)\]$' "$file" || continue
    grep -Eq '^(interface-name|mac-address)=.+|^\[match\]$' "$file" && continue
    [ -z "$profile" ] || exit 0
    profile=$file
done
[ -n "$profile" ] || exit 0
umask 077
tmp=$(mktemp "$profile.XXXXXX")
trap 'rm -f "$tmp"' EXIT
awk -v mac="$mac" '{print; if ($0 == "[ethernet]" || $0 == "[802-3-ethernet]") print "mac-address=" mac}' "$profile" > "$tmp"
mv "$tmp" "$profile"
