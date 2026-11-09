#!/bin/bash
# Tải Ubuntu 22.04 Cloud VMDK
DEST="/mnt/c/Users/Admin/VirtualBox VMs/ATT-Lab/ubuntu-22.04-base.vmdk"
URL="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.vmdk"

if [ -f "$DEST" ]; then
    SIZE=$(du -sh "$DEST" | cut -f1)
    echo "VMDK đã tồn tại: $SIZE"
    exit 0
fi

echo "Bắt đầu tải Ubuntu 22.04 Cloud VMDK (~600MB)..."
wget --show-progress -O "$DEST" "$URL"
echo "Tải hoàn tất!"
ls -lh "$DEST"
