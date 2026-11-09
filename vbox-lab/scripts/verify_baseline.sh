#!/usr/bin/env bash
# Verify IP addressing, services and the baseline load-balancing path.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

DIR=$(new_evidence_dir baseline)
echo "[*] Evidence: $DIR"

echo ""
echo "=== IP addresses ==="
for i in "${!VM_NAMES[@]}"; do
    echo "--- ${VM_NAMES[$i]} ---"
    save_ssh "${VM_NAMES[$i]}" "$DIR/${VM_NAMES[$i]}-ip.txt" \
        'hostname; ip -br addr; ip route'
    cat "$DIR/${VM_NAMES[$i]}-ip.txt"
done

echo ""
echo "=== Services ==="
save_ssh ATT-C2-Server "$DIR/c2-service.txt" \
    'systemctl is-active att-c2; ss -ltnp | grep -E "9999|9998"'
save_ssh ATT-Bot1 "$DIR/bot1-service.txt" 'systemctl is-active att-bot'
save_ssh ATT-Bot2 "$DIR/bot2-service.txt" 'systemctl is-active att-bot'
save_ssh ATT-Victim "$DIR/victim-services.txt" \
    'systemctl is-active nginx; systemctl is-active suricata; systemctl is-active att-autoblock; sudo ufw status | head -3'
save_ssh ATT-Backend2 "$DIR/backend2-service.txt" \
    'systemctl is-active nginx; curl -s http://127.0.0.1:8081/'
for f in c2-service bot1-service bot2-service victim-services backend2-service; do
    echo "--- $f ---"; cat "$DIR/$f.txt"; echo
done

echo ""
echo "=== Bots registered on C2 ==="
save_ssh ATT-C2-Server "$DIR/c2-bots.txt" \
    "printf 'bots\n' | nc -w 2 127.0.0.1 9998"
cat "$DIR/c2-bots.txt"

echo ""
echo "=== Load balancing baseline (6 requests from Bot1) ==="
save_ssh ATT-Bot1 "$DIR/lb-baseline.txt" \
    'for i in 1 2 3 4 5 6; do curl -s --max-time 5 http://10.10.10.30/; echo; done'
cat "$DIR/lb-baseline.txt"

echo ""
echo "=== Victim defense state (expected: off before step 2) ==="
save_ssh ATT-Victim "$DIR/defense-state.txt" \
    'systemctl is-active suricata; systemctl is-active att-autoblock; sudo ufw status | head -5; ls -l /etc/nginx/sites-enabled/att-lab'
cat "$DIR/defense-state.txt"

echo ""
echo "[OK] Baseline captured in $DIR"
