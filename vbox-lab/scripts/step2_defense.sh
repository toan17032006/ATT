#!/usr/bin/env bash
# STEP 2 - Enable Suricata + UFW + auto-block, then repeat the attack.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

DURATION=${1:-20}
DIR=$(new_evidence_dir step2-defense)
echo "[*] Evidence: $DIR"

echo ""
echo "=== [1] Enable defenses on victim ==="
save_ssh ATT-Victim "$DIR/01-enable-defense.txt" \
    'sudo /opt/defense/enable_defense.sh'
cat "$DIR/01-enable-defense.txt"

save_ssh ATT-Victim "$DIR/02-defense-status.txt" \
    'sudo /opt/defense/show_stats.sh; echo; ls -l /etc/nginx/sites-enabled/att-lab; echo; sudo suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -5'
cat "$DIR/02-defense-status.txt"

echo ""
echo "=== [2] Baseline through protected frontend (Bot1) ==="
save_ssh ATT-Bot1 "$DIR/03-baseline-bot1.txt" \
    'for i in 1 2 3; do curl -s --max-time 5 http://10.10.10.30/; echo; sleep 0.3; done'
cat "$DIR/03-baseline-bot1.txt"

echo ""
echo "=== [3] Repeat the botnet attack ==="
save_ssh ATT-C2-Server "$DIR/04-attack-command.txt" \
    "printf 'attack 10.10.10.30 80 ${DURATION} http\n' | nc -w 3 127.0.0.1 9998"
cat "$DIR/04-attack-command.txt"

sleep 8
echo ""
echo "=== [4] Detection and blocking during attack ==="
save_ssh ATT-Victim "$DIR/05-suricata-alerts.txt" \
    'echo "=== fast.log ==="; tail -25 /var/log/suricata/fast.log 2>/dev/null; echo; echo "=== ufw ==="; sudo ufw status numbered | head -40; echo; echo "=== autoblock log ==="; tail -20 /var/log/att-blocks.log 2>/dev/null'
cat "$DIR/05-suricata-alerts.txt"

save_ssh ATT-Victim "$DIR/06-during-nginx.txt" \
    'awk "{print \$9}" /var/log/nginx/att-lab-access.log 2>/dev/null | sort | uniq -c; tail -5 /var/log/nginx/att-lab-access.log'
cat "$DIR/06-during-nginx.txt"

echo ""
echo "Waiting for the attack to finish..."
sleep $((DURATION + 5))

echo ""
echo "=== [5] Post-attack: attacker blocked, management still works ==="
save_ssh ATT-Bot1 "$DIR/07-bot1-after-block.txt" \
    'echo "curl from blocked bot:"; curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 5 http://10.10.10.30/ || echo "CONNECTION FAILED (blocked)"'
cat "$DIR/07-bot1-after-block.txt"

save_ssh ATT-C2-Server "$DIR/08-c2-after-block.txt" \
    'echo "curl from non-attacking C2:"; for i in 1 2; do curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 5 http://10.10.10.30/; sleep 0.5; done'
cat "$DIR/08-c2-after-block.txt"

save_ssh ATT-Victim "$DIR/09-final-state.txt" \
    'sudo /opt/defense/show_stats.sh'
cat "$DIR/09-final-state.txt"

echo ""
echo "[OK] Step 2 evidence saved in $DIR"
echo "Next: wsl -d Ubuntu -- bash $LAB_DIR/scripts/step3_loadbalance.sh"
