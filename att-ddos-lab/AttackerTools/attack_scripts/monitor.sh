#!/bin/bash
# ============================================
# Script: Monitor thời gian thực trong quá trình tấn công
# Hiển thị: Request/s, Active connections, Response time
# ============================================

TARGET=${1:-"http://localhost:8080"}
INTERVAL=${2:-2}

echo "========================================"
echo " MONITOR - Victim Web API Stats"
echo " Target: $TARGET"
echo " Refresh: ${INTERVAL}s"
echo " Nhấn Ctrl+C để dừng"
echo "========================================"
echo ""

while true; do
    TIMESTAMP=$(date +"%H:%M:%S")
    
    # Gọi /stats từ victim
    RESPONSE=$(curl -s --connect-timeout 2 --max-time 3 "$TARGET/stats" 2>/dev/null)
    
    if [ -z "$RESPONSE" ]; then
        echo "[$TIMESTAMP] ❌ VICTIM KHÔNG PHẢN HỒI! (Có thể đã bị crash/overwhelmed)"
    else
        TOTAL=$(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_requests',0))" 2>/dev/null)
        ACTIVE=$(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('active_requests',0))" 2>/dev/null)
        RPS=$(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('requests_per_second',0))" 2>/dev/null)
        
        echo "[$TIMESTAMP] Total: $TOTAL req | Active: $ACTIVE conn | Avg RPS: $RPS req/s"
    fi
    
    sleep $INTERVAL
done
