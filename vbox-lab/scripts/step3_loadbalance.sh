#!/usr/bin/env bash
# STEP 3 - Nginx load balancing across two backends + failover test.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../config.sh"
require_env

DIR=$(new_evidence_dir step3-loadbalance)
echo "[*] Evidence: $DIR"

count_servers() {
    local file=$1
    echo "backend-1 responses: $(grep -c 'backend-1' "$file" || true)"
    echo "backend-2 responses: $(grep -c 'backend-2' "$file" || true)"
}

echo ""
echo "=== [1] Clear any auto-block entries and ensure both backends are up ==="
save_ssh ATT-Victim "$DIR/00-reset-blocks.txt" 'sudo /opt/defense/reset_blocks.sh'
cat "$DIR/00-reset-blocks.txt"
save_ssh ATT-Backend2 "$DIR/00-backend2-start.txt" \
    'sudo systemctl start nginx; sleep 1; systemctl is-active nginx; curl -s http://127.0.0.1:8081/'
cat "$DIR/00-backend2-start.txt"

echo ""
echo "=== [2] Load-balancing proof: 10 requests to 10.10.10.30 ==="
save_ssh ATT-C2-Server "$DIR/01-round-robin.txt" \
    'for i in $(seq 1 10); do curl -s --max-time 5 http://10.10.10.30/; echo; sleep 0.3; done'
cat "$DIR/01-round-robin.txt"
count_servers "$DIR/01-round-robin.txt" | tee "$DIR/01-count.txt"

echo ""
echo "=== [3] Failover: stop backend-2 (10.10.10.40) ==="
save_ssh ATT-Backend2 "$DIR/02-backend2-stop.txt" \
    'sudo systemctl stop nginx; sleep 1; systemctl is-active nginx || true'
cat "$DIR/02-backend2-stop.txt"
sleep 7
save_ssh ATT-C2-Server "$DIR/03-after-backend2-down.txt" \
    'for i in $(seq 1 6); do curl -s --max-time 5 http://10.10.10.30/; echo; sleep 0.3; done'
cat "$DIR/03-after-backend2-down.txt"
count_servers "$DIR/03-after-backend2-down.txt" | tee "$DIR/03-count.txt"

echo ""
echo "=== [4] Recovery: start backend-2 again ==="
save_ssh ATT-Backend2 "$DIR/04-backend2-restart.txt" \
    'sudo systemctl start nginx; sleep 1; systemctl is-active nginx'
cat "$DIR/04-backend2-restart.txt"
sleep 7
save_ssh ATT-C2-Server "$DIR/05-after-backend2-up.txt" \
    'for i in $(seq 1 6); do curl -s --max-time 5 http://10.10.10.30/; echo; sleep 0.3; done'
cat "$DIR/05-after-backend2-up.txt"
count_servers "$DIR/05-after-backend2-up.txt" | tee "$DIR/05-count.txt"

echo ""
echo "=== [5] Nginx upstream configuration ==="
save_ssh ATT-Victim "$DIR/06-nginx-upstream.txt" \
    "grep -A4 'upstream att_backend' /etc/nginx/sites-enabled/att-lab"
cat "$DIR/06-nginx-upstream.txt"

echo ""
echo "=== [6] Backend access logs ==="
save_ssh ATT-Backend2 "$DIR/07-backend2-access.txt" \
    'tail -10 /var/log/nginx/att-backend2-access.log'
cat "$DIR/07-backend2-access.txt"

echo ""
echo "[OK] Step 3 evidence saved in $DIR"
