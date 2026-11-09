#!/usr/bin/env bash
# Shared configuration and helpers for the ATT DDoS lab.
# Run all lab scripts from WSL:  wsl -d Ubuntu -- bash vbox-lab/scripts/<script>.sh

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LAB_DIR

# --- VirtualBox (Windows binary, invoked from WSL) ---
VBOX="/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"
WIN_VM_DIR='C:\Users\Admin\VirtualBox VMs\ATT-Lab'
VM_DIR="/mnt/c/Users/Admin/VirtualBox VMs/ATT-Lab"
BASE_VMDK="$VM_DIR/ubuntu-22.04-base.vmdk"
WIN_BASE_VMDK='C:\Users\Admin\VirtualBox VMs\ATT-Lab\ubuntu-22.04-base.vmdk'
WIN_PYTHON='/mnt/c/Users/Admin/AppData/Local/Programs/Python/Python312/python.exe'

# --- Lab network ---
NET_NAME='att-lab-net'
NET_CIDR='10.10.10.0/24'
NET_MASK='255.255.255.0'
LAB_GW='10.10.10.1'

# --- SSH key injected into every VM ---
KEY_FILE="$LAB_DIR/keys/attlab_ed25519"

# WSL2 has its own loopback, so VirtualBox port-forwards on the Windows
# host are unreachable from WSL's 127.0.0.1. Use the Windows OpenSSH client
# (a Windows process) so 127.0.0.1 resolves to the Windows host loopback.
SSH_BIN="${SSH_BIN:-/mnt/c/Windows/System32/OpenSSH/ssh.exe}"

# netplan requires colon-separated MACs, e.g. 08:00:27:aa:00:01
colonmac() {
    echo "$1" | sed -E 's/(..)(..)(..)(..)(..)(..)/\1:\2:\3:\4:\5:\6/'
}

# --- VM inventory (parallel arrays) ---
VM_NAMES=(ATT-C2-Server ATT-Bot1 ATT-Bot2 ATT-Victim ATT-Backend2)
VM_ROLES=(c2 bot bot victim backend2)
VM_IPS=(10.10.10.10 10.10.10.20 10.10.10.21 10.10.10.30 10.10.10.40)
VM_MAC1=(080027AA0001 080027AA0002 080027AA0003 080027AA0004 080027AA0005)
VM_MAC2=(080027AA0101 080027AA0102 080027AA0103 080027AA0104 080027AA0105)
VM_SSH_PORTS=(2222 2223 2224 2225 2226)
VM_USERS=(attacker bot bot defender defender)
VM_RAMS=(768 768 768 1536 768)
VM_CPUS=(1 1 1 2 1)

vm_index() {
    local want=$1 i
    for i in "${!VM_NAMES[@]}"; do
        if [[ "${VM_NAMES[$i]}" == "$want" ]]; then
            echo "$i"
            return 0
        fi
    done
    echo "Unknown VM: $want" >&2
    return 1
}

vm_ip()        { echo "${VM_IPS[$(vm_index "$1")]}"; }
vm_user()      { echo "${VM_USERS[$(vm_index "$1")]}"; }
vm_ssh_port()  { echo "${VM_SSH_PORTS[$(vm_index "$1")]}"; }
vm_role()      { echo "${VM_ROLES[$(vm_index "$1")]}"; }

winpath() { wslpath -w "$1"; }

ssh_vm() {
    local vm=$1
    shift
    local i
    i=$(vm_index "$vm")
    "$SSH_BIN" -i "$(wslpath -w "$KEY_FILE")" \
        -p "${VM_SSH_PORTS[$i]}" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=NUL \
        -o ConnectTimeout=5 \
        -o LogLevel=ERROR \
        "${VM_USERS[$i]}@127.0.0.1" "$@"
}

ssh_vm_tty() {
    local vm=$1
    shift
    local i
    i=$(vm_index "$vm")
    "$SSH_BIN" -tt -i "$(wslpath -w "$KEY_FILE")" \
        -p "${VM_SSH_PORTS[$i]}" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=NUL \
        -o ConnectTimeout=5 \
        -o LogLevel=ERROR \
        "${VM_USERS[$i]}@127.0.0.1" "$@"
}

wait_ssh() {
    local vm=$1 timeout=${2:-600}
    local start=$SECONDS
    while true; do
        if ssh_vm "$vm" 'echo SSH_READY' 2>/dev/null | grep -q SSH_READY; then
            echo "[OK] SSH $vm (port $(vm_ssh_port "$vm"))"
            return 0
        fi
        if (( SECONDS - start >= timeout )); then
            echo "[FAIL] SSH $vm timeout after ${timeout}s" >&2
            return 1
        fi
        sleep 5
    done
}

wait_setup() {
    local vm=$1 timeout=${2:-1200}
    local start=$SECONDS
    while true; do
        if ssh_vm "$vm" 'tail -1 /var/log/att-setup.log 2>/dev/null' 2>/dev/null | grep -q 'STATUS: READY'; then
            echo "[OK] cloud-init $vm ready"
            return 0
        fi
        if (( SECONDS - start >= timeout )); then
            echo "[FAIL] cloud-init $vm timeout; last log:" >&2
            ssh_vm "$vm" 'tail -20 /var/log/cloud-init-output.log 2>/dev/null' 2>&1 || true
            return 1
        fi
        sleep 10
    done
}

new_evidence_dir() {
    local tag=$1 dir
    dir="$LAB_DIR/evidence/$(date +%Y%m%d-%H%M%S)-$tag"
    mkdir -p "$dir"
    echo "$dir"
}

save_ssh() {
    local vm=$1 out=$2
    shift 2
    ssh_vm "$vm" "$@" > "$out" 2>&1 || true
}

require_env() {
    [[ -x "$VBOX" ]] || { echo "VBoxManage not found: $VBOX" >&2; exit 1; }
    [[ -f "$BASE_VMDK" ]] || { echo "Base VMDK not found: $BASE_VMDK" >&2; exit 1; }
    command -v wslpath >/dev/null || { echo "Run this from WSL (wslpath missing)" >&2; exit 1; }
}
