#!/usr/bin/env bash
# Quick SSH reachability test for every lab VM.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"

for i in "${!VM_NAMES[@]}"; do
    vm="${VM_NAMES[$i]}"
    printf '%-16s %-12s port %-5s ' "$vm" "${VM_IPS[$i]}" "${VM_SSH_PORTS[$i]}"
    if ssh_vm "$vm" 'echo SSH_OK' 2>/dev/null | grep -q SSH_OK; then
        echo "OK"
    else
        echo "FAIL"
    fi
done
