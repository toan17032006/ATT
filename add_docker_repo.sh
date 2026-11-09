#!/bin/bash
# Cài Docker trong WSL (chạy với root)
set -e

echo "[1/3] Thêm Docker GPG key..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "GPG key OK"

echo "[2/3] Thêm Docker repository..."
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
echo "Ubuntu codename: $CODENAME"
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $CODENAME stable" > /etc/apt/sources.list.d/docker.list
cat /etc/apt/sources.list.d/docker.list
echo "Repo added"

echo "[3/3] Update apt với repo mới..."
apt-get update -y -q 2>&1 | tail -3
echo "Done! Ready to install Docker."
