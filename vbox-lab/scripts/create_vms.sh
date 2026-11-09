#!/usr/bin/env bash
# Create the 5 ATT lab VMs (run from WSL).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
source "$HERE/lib_cidata.sh"
require_env

mkdir -p "$LAB_DIR/keys" "$LAB_DIR/evidence"
if [[ ! -f "$KEY_FILE" ]]; then
    echo "[*] Generating SSH key: $KEY_FILE"
    ssh-keygen -q -t ed25519 -N '' -C 'att-lab' -f "$KEY_FILE"
fi

# Windows OpenSSH refuses keys with inherited ACLs; restrict to the current user.
WIN_USER="$(cmd.exe /c 'echo %USERNAME%' 2>/dev/null | tr -d '\r\n')"
if [[ -n "$WIN_USER" ]]; then
    icacls.exe "$(wslpath -w "$KEY_FILE")" /inheritance:r /grant:r "$WIN_USER:R" \
        >/dev/null 2>&1 || echo "[!] icacls on key failed (Windows ssh may reject it)"
fi

setup_natnetwork() {
    echo "[*] Recreating NAT network $NET_NAME ($NET_CIDR)"
    "$VBOX" natnetwork remove --netname "$NET_NAME" >/dev/null 2>&1 || true
    "$VBOX" natnetwork add \
        --netname "$NET_NAME" \
        --network "$NET_CIDR" \
        --enable \
        --dhcp on

    local args=() i
    for i in "${!VM_NAMES[@]}"; do
        args+=(--port-forward-4 \
            "ssh-${VM_NAMES[$i]}:tcp:[]:${VM_SSH_PORTS[$i]}:[${VM_IPS[$i]}]:22")
    done
    if ! "$VBOX" natnetwork modify --netname "$NET_NAME" --network "$NET_CIDR" \
        "${args[@]}" >/tmp/att-nat.log 2>&1; then
        echo "[!] Bulk port-forward failed, trying one rule per call"
        for i in "${!VM_NAMES[@]}"; do
            "$VBOX" natnetwork modify --netname "$NET_NAME" --network "$NET_CIDR" \
                --port-forward-4 \
                "ssh-${VM_NAMES[$i]}:tcp:[]:${VM_SSH_PORTS[$i]}:[${VM_IPS[$i]}]:22"
        done
    fi
    "$VBOX" natnetwork list "$NET_NAME" | sed -n '1,80p'
}

create_vm() {
    local i=$1
    local name="${VM_NAMES[$i]}"
    local disk="$VM_DIR/$name.vmdk"
    local iso="$VM_DIR/$name-cidata.iso"

    echo ""
    echo "================================================"
    echo " $name | role=${VM_ROLES[$i]} | ip=${VM_IPS[$i]}"
    echo " RAM=${VM_RAMS[$i]}MB CPU=${VM_CPUS[$i]} SSH=127.0.0.1:${VM_SSH_PORTS[$i]}"
    echo "================================================"

    "$VBOX" unregistervm "$name" --delete >/dev/null 2>&1 || true
    rm -f "$disk"

    echo "[1/5] Clone base VMDK"
    "$VBOX" clonemedium disk "$WIN_BASE_VMDK" "$(winpath "$disk")" \
        --format VMDK --variant Standard >/dev/null
    "$VBOX" modifymedium disk "$(winpath "$disk")" --resize 10240 >/dev/null 2>&1 || \
        echo "[!] Disk resize skipped"

    echo "[2/5] Create VM"
    "$VBOX" createvm --name "$name" --ostype Ubuntu_64 --register \
        --basefolder "$WIN_VM_DIR" >/dev/null

    echo "[3/5] Hardware + network"
    "$VBOX" modifyvm "$name" \
        --memory "${VM_RAMS[$i]}" \
        --cpus "${VM_CPUS[$i]}" \
        --vram 16 \
        --graphicscontroller vmsvga \
        --boot1 disk --boot2 none --boot3 none --boot4 none \
        --rtcuseutc on \
        --nic1 natnetwork --nat-network1 "$NET_NAME" \
        --nictype1 82540EM --macaddress1 "${VM_MAC1[$i]}" \
        --nic2 nat --nictype2 82540EM --macaddress2 "${VM_MAC2[$i]}" \
        --cableconnected1 on --cableconnected2 on >/dev/null

    echo "[4/5] Storage"
    "$VBOX" storagectl "$name" --name "SATA" --add sata \
        --controller IntelAhci --portcount 2 >/dev/null
    "$VBOX" storageattach "$name" --storagectl "SATA" --port 0 --device 0 \
        --type hdd --medium "$(winpath "$disk")" >/dev/null
    "$VBOX" storageattach "$name" --storagectl "SATA" --port 1 --device 0 \
        --type dvddrive --medium "$(winpath "$iso")" >/dev/null

    echo "[5/5] Done"
}

setup_natnetwork

echo ""
echo "=== Build cloud-init ISOs ==="
for i in "${!VM_NAMES[@]}"; do
    make_iso "$i"
done

echo ""
echo "=== Create VMs ==="
for i in "${!VM_NAMES[@]}"; do
    create_vm "$i"
done

echo ""
echo "================================================"
echo " Lab VMs created:"
"$VBOX" list vms | grep ATT || true
echo ""
echo " Next: wsl -d Ubuntu -- bash $LAB_DIR/scripts/start_lab.sh"
echo "================================================"
