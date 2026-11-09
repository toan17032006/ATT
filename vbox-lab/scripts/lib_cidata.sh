#!/usr/bin/env bash
# Shared cloud-init (NoCloud cidata) ISO builder.
# Sourced by create_vms.sh and rebuild_cidata.sh; expects config.sh already loaded.

LAB_IF="enp0s3"          # NIC1 (lab network) inside Ubuntu guests
LAST_IF="enp0s8"         # NIC2 (NAT/internet)

# make_iso <index> [instance-version]
make_iso() {
    local i=$1
    local ver=${2:-v1}
    local vm="${VM_NAMES[$i]}"
    local role="${VM_ROLES[$i]}"
    local ip="${VM_IPS[$i]}"
    local mac1 mac2
    mac1="$(colonmac "${VM_MAC1[$i]}")"
    mac2="$(colonmac "${VM_MAC2[$i]}")"
    local tmp="$VM_DIR/.cidata-$vm"
    local iso="$VM_DIR/$vm-cidata.iso"

    rm -rf "$tmp"
    mkdir -p "$tmp"

    sed -e "s|__SSH_PUBKEY__|$(cat "$KEY_FILE.pub")|g" \
        -e "s|__HOSTNAME__|$vm|g" \
        -e "s|__LAB_IF__|$LAB_IF|g" \
        "$LAB_DIR/cloud-init/$role/user-data" > "$tmp/user-data"

    cat > "$tmp/meta-data" <<EOF
instance-id: $vm-$ver
local-hostname: $vm
EOF

    cat > "$tmp/network-config" <<EOF
version: 2
ethernets:
  lab:
    match:
      macaddress: "$mac1"
    dhcp4: false
    addresses: [$ip/24]
    routes:
      - to: default
        via: $LAB_GW
        metric: 100
    nameservers:
      addresses: [8.8.8.8, 1.1.1.1]
  wan:
    match:
      macaddress: "$mac2"
    dhcp4: true
    dhcp4-overrides:
      route-metric: 200
EOF

    rm -f "$iso"
    "$WIN_PYTHON" "$(winpath "$LAB_DIR/iso/make_iso.py")" \
        "$(winpath "$tmp")" "$(winpath "$iso")"
    rm -rf "$tmp"
}
