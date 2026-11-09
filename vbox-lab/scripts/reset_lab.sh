#!/usr/bin/env bash
# Reset the lab to a clean "before defense" state for a new demo run.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

echo "[*] Disabling defenses on victim"
ssh_vm ATT-Victim 'sudo /opt/defense/disable_defense.sh' || true

echo "[*] Restarting backend-2"
ssh_vm ATT-Backend2 'sudo systemctl start nginx' || true

echo "[*] Restarting bot agents and C2"
ssh_vm ATT-C2-Server 'sudo systemctl restart att-c2' || true
ssh_vm ATT-Bot1 'sudo systemctl restart att-bot' || true
ssh_vm ATT-Bot2 'sudo systemctl restart att-bot' || true

sleep 5
echo ""
echo "[*] Current state"
ssh_vm ATT-Victim 'systemctl is-active nginx suricata att-autoblock; sudo ufw status | head -4'
ssh_vm ATT-C2-Server "printf 'bots\n' | nc -w 2 127.0.0.1 9998"
echo "[OK] Lab reset"
