#!/bin/bash
# =====================================================
# Script: Cài đặt môi trường mô phỏng DDoS cho bài ATT
# Môi trường: Ubuntu 26.04 (WSL2)
# Cài: Docker, Docker Compose, .NET SDK 9
# =====================================================

set -e  # Dừng nếu có lỗi

echo "============================================="
echo " ATT - Setup môi trường mô phỏng DDoS"
echo "============================================="

# --- Cập nhật hệ thống ---
echo "[1/5] Cập nhật package list..."
sudo apt-get update -y

# --- Cài đặt .NET SDK 9 ---
echo "[2/5] Cài .NET SDK 9..."
# Thêm Microsoft package repository
wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb -O /tmp/packages-microsoft-prod.deb
sudo dpkg -i /tmp/packages-microsoft-prod.deb
sudo apt-get update -y
sudo apt-get install -y dotnet-sdk-9.0

echo ".NET version: $(dotnet --version)"

# --- Cài đặt Docker ---
echo "[3/5] Cài Docker Engine..."
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Thêm Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Thêm Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Khởi động Docker
sudo service docker start

# Thêm user vào nhóm docker (không cần sudo)
sudo usermod -aG docker $USER

echo "Docker version: $(sudo docker --version)"
echo "Docker Compose: $(sudo docker compose version)"

# --- Cài thêm công cụ network ---
echo "[4/5] Cài công cụ hỗ trợ network..."
sudo apt-get install -y net-tools iputils-ping curl wget nmap iproute2 tcpdump

# --- Tạo thư mục dự án ---
echo "[5/5] Tạo thư mục dự án..."
mkdir -p ~/att-ddos-lab
cd ~/att-ddos-lab

echo ""
echo "============================================="
echo " Cài đặt hoàn tất!"
echo " .NET: $(dotnet --version)"
echo " Docker: $(sudo docker --version)"
echo "============================================="
echo " Chạy tiếp: cd ~/att-ddos-lab"
echo "============================================="
