#!/usr/bin/env bash
# Rebuild the cloud-init cidata ISOs for existing VMs and reboot them.
# Use after changing cloud-init templates or network-config.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
source "$HERE/lib_cidata.sh"
require_env

VER="${1:-v2}"
shift || true

if (($#)); then
    TARGETS=("$@")
else
    TARGETS=("${VM_NAMES[@]}")
fi

echo "=== Power off VMs ==="
for vm in "${TARGETS[@]}"; do
    "$VBOX" controlvm "$vm" poweroff >/dev/null 2>&1 || true
    echo "  off: $vm"
done
sleep 3

echo ""
echo "=== Rebuild cidata ISOs (instance-id: <vm>-$VER) ==="
for vm in "${TARGETS[@]}"; do
    i=$(vm_index "$vm")
    iso="$VM_DIR/$vm-cidata.iso"

    "$VBOX" storageattach "$vm" --storagectl "SATA" --port 1 --device 0 \
        --type dvddrive --medium none >/dev/null 2>&1 || true

    make_iso "$i" "$VER"
    "$VBOX" storageattach "$vm" --storagectl "SATA" --port 1 --device 0 \
        --type dvddrive --medium "$(winpath "$iso")" >/dev/null

    echo "  built: $vm -> $iso"
done

echo ""
echo "=== Power on VMs (headless) ==="
for vm in "${TARGETS[@]}"; do
    "$VBOX" startvm "$vm" --type headless >/dev/null
    echo "  on: $vm"
done

echo ""
echo "=== Wait for SSH ==="
for vm in "${TARGETS[@]}"; do
    wait_ssh "$vm" 420
done
