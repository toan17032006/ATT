#!/usr/bin/env bash
# Collect a full snapshot of logs/state from every VM.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

DIR=$(new_evidence_dir full-state)
echo "[*] Evidence: $DIR"

save_ssh ATT-C2-Server "$DIR/c2.txt" \
    'systemctl status att-c2 --no-pager -l | head -30; echo; journalctl -u att-c2 --no-pager -n 80; echo; printf "bots\n" | nc -w 2 127.0.0.1 9998'
save_ssh ATT-Bot1 "$DIR/bot1.txt" 'journalctl -u att-bot --no-pager -n 80'
save_ssh ATT-Bot2 "$DIR/bot2.txt" 'journalctl -u att-bot --no-pager -n 80'
save_ssh ATT-Victim "$DIR/victim.txt" \
    'sudo /opt/defense/show_stats.sh; echo; echo "=== fast.log ==="; tail -50 /var/log/suricata/fast.log 2>/dev/null; echo; echo "=== att-blocks ==="; cat /var/log/att-blocks.log 2>/dev/null'
save_ssh ATT-Victim "$DIR/nginx-access.txt" 'tail -100 /var/log/nginx/att-lab-access.log'
save_ssh ATT-Victim "$DIR/nginx-error.txt" 'tail -50 /var/log/nginx/error.log'
save_ssh ATT-Backend2 "$DIR/backend2.txt" \
    'systemctl is-active nginx; curl -s http://127.0.0.1:8081/; echo; tail -20 /var/log/nginx/att-backend2-access.log'
save_ssh ATT-C2-Server "$DIR/host-ip.txt" 'hostname; ip -br addr'
save_ssh ATT-Bot1 "$DIR/bot1-ip.txt" 'hostname; ip -br addr'
save_ssh ATT-Bot2 "$DIR/bot2-ip.txt" 'hostname; ip -br addr'
save_ssh ATT-Victim "$DIR/victim-ip.txt" 'hostname; ip -br addr'
save_ssh ATT-Backend2 "$DIR/backend2-ip.txt" 'hostname; ip -br addr'

echo "[OK] Snapshot saved in $DIR"
ls -l "$DIR"
