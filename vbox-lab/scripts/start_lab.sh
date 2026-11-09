#!/usr/bin/env bash
# Boot all lab VMs and wait until cloud-init finishes.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

echo "=== Starting ATT lab VMs ==="
for i in "${!VM_NAMES[@]}"; do
    vm="${VM_NAMES[$i]}"
    state=$("$VBOX" showvminfo "$vm" --machinereadable 2>/dev/null | \
        awk -F= '/^VMState=/{gsub(/"/,"",$2); print $2}')
    if [[ "$state" == "running" ]]; then
        echo "[=] $vm already running"
    else
        echo "[*] Starting $vm"
        "$VBOX" startvm "$vm" --type headless >/dev/null
    fi
    sleep 2
done

echo ""
echo "=== Waiting for SSH ==="
for i in "${!VM_NAMES[@]}"; do
    wait_ssh "${VM_NAMES[$i]}" 600 || exit 1
done

echo ""
echo "=== Waiting for cloud-init setup (apt install can take a while) ==="
for i in "${!VM_NAMES[@]}"; do
    wait_setup "${VM_NAMES[$i]}" 1800 || exit 1
done

echo ""
echo "=== Lab ready ==="
printf '%-16s %-12s %-8s %s\n' "VM" "IP" "SSH" "USER"
for i in "${!VM_NAMES[@]}"; do
    printf '%-16s %-12s %-8s %s\n' \
        "${VM_NAMES[$i]}" "${VM_IPS[$i]}" \
        "127.0.0.1:${VM_SSH_PORTS[$i]}" "${VM_USERS[$i]}"
done

echo ""
echo "Next: wsl -d Ubuntu -- bash $LAB_DIR/scripts/verify_baseline.sh"
