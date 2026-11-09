# ATT Lab — DDoS mô phỏng, phòng chống và cân bằng tải

Lab chạy hoàn toàn trên **VirtualBox**, điều khiển từ **WSL (Ubuntu)** bằng
`VBoxManage.exe` và SSH qua port-forward. Mục tiêu bám đúng 3 bước của bài:

| Bước | Nội dung | Công cụ trong lab |
|---|---|---|
| 1 | Botnet tấn công 2 máy | C2 server + 2 bot agent + HTTP flood kiểu LOIC + `hping3` (SYN/UDP) |
| 2 | Công cụ phòng chống | **Suricata** (IDS/IPS rules), **UFW** (firewall), auto-block Suricata → UFW, Nginx rate limiting |
| 3 | Cân bằng tải | **Nginx** round-robin tới 2 backend độc lập + failover khi 1 backend chết |

> **Ghi chú an toàn / pháp lý:** Không tải botnet thật từ Internet. Lab dùng
> **botnet mô phỏng** (C2 + bot agent tự viết, chỉ chạy trong mạng NAT nội bộ
> `10.10.10.0/24`) và các kỹ thuật của công cụ stress-test công khai
> (LOIC/HOIC/hping3/Slowloris). Đây là cách làm hợp pháp, an toàn và vẫn
> chứng minh đầy đủ cơ chế DDoS cho báo cáo. Không bao giờ trỏ công cụ ra
> ngoài mạng lab.

---

## 1. Kiến trúc

```
                         NAT Network: att-lab-net  10.10.10.0/24
 ┌──────────────┐        ┌──────────────┐        ┌───────────────────────────┐
 │ ATT-C2-Server│        │ ATT-Bot1     │        │ ATT-Victim 10.10.10.30    │
 │ 10.10.10.10  │──9999─▶│ 10.10.10.20  │──HTTP─▶│  :80  Nginx LB            │
 │ C2 console   │        └──────────────┘        │   ├─ 127.0.0.1:8081 b1    │
 │ :9999/:9998  │        ┌──────────────┐        │   └─ 10.10.10.40:8081 b2  │
 │              │──9999─▶│ ATT-Bot2     │──HTTP─▶│  Suricata + UFW (bước 2)  │
 └──────────────┘        │ 10.10.10.21  │        └──────────────┬────────────┘
                         └──────────────┘                       │
                                                    ┌───────────▼────────────┐
                                                    │ ATT-Backend2           │
                                                    │ 10.10.10.40:8081       │
                                                    └────────────────────────┘
```

Mỗi VM có thêm NIC2 = **NAT** để `apt-get` ra Internet. NIC1 = NAT Network
nội bộ để các VM nói chuyện với nhau. Host/WSL vào từng VM qua SSH
port-forward (`127.0.0.1:2222..2226`).

| VM | IP | RAM/CPU | User / mật khẩu | SSH từ WSL |
|---|---|---|---|---|
| ATT-C2-Server | 10.10.10.10 | 768 MB / 1 | `attacker` / `Attack@123` | `127.0.0.1:2222` |
| ATT-Bot1 | 10.10.10.20 | 768 MB / 1 | `bot` / `Bot@123` | `127.0.0.1:2223` |
| ATT-Bot2 | 10.10.10.21 | 768 MB / 1 | `bot` / `Bot@123` | `127.0.0.1:2224` |
| ATT-Victim | 10.10.10.30 | 1536 MB / 2 | `defender` / `Defend@123` | `127.0.0.1:2225` |
| ATT-Backend2 | 10.10.10.40 | 768 MB / 1 | `defender` / `Defend@123` | `127.0.0.1:2226` |

SSH key được tạo tự động ở `vbox-lab/keys/attlab_ed25519` và được inject vào
cả 5 VM, nên không cần nhập mật khẩu.

> **Vì sao script dùng `C:\Windows\System32\OpenSSH\ssh.exe`?**
> WSL2 có loopback riêng, nên `127.0.0.1:2222` trong WSL **không** trỏ tới
> port-forward của VirtualBox trên Windows. `config.sh` vì vậy gọi SSH client
> của Windows (tiến trình Windows) để `127.0.0.1` là loopback của Windows.
> Windows OpenSSH lại từ chối key có ACL quá mở, nên `create_vms.sh` tự chạy
> `icacls` để giới hạn quyền cho đúng user hiện tại. Nếu bạn copy key đi nơi
> khác, phải chạy lại `icacls <key> /inheritance:r /grant:r "%USERNAME%:R"`.

---

## 2. Yêu cầu môi trường

- Windows + VirtualBox 7.x (đã kiểm tra với 7.2.14).
- WSL2 Ubuntu (đã kiểm tra với Ubuntu 24.04).
- Base image: `C:\Users\Admin\VirtualBox VMs\ATT-Lab\ubuntu-22.04-base.vmdk`
  (đã có sẵn, ~675 MB). Nếu thiếu: chạy `scripts/download_vmdk.sh`.
- Python trên Windows có `pycdlib` (để tạo ISO cloud-init):
  `python -m pip install --user pycdlib`
- Khoảng **5 GB RAM trống** và **10 GB đĩa** cho 5 VM.

Tất cả script được chạy **từ WSL**. Mở Ubuntu (WSL) rồi:

```bash
cd /mnt/c/Users/Admin/Desktop/ATT/vbox-lab
```

---

## 3. Chạy lab

### 3.1. Tạo VM (chỉ lần đầu, hoặc khi muốn reset sạch)

```bash
bash scripts/create_vms.sh
```

Script sẽ:

1. Tạo NAT Network `att-lab-net` (10.10.10.0/24) + 5 port-forward SSH.
2. Tạo ISO cloud-init cho từng VM (static IP theo MAC, SSH key, cài package).
3. Clone base VMDK thành 5 đĩa riêng, tạo VM, gắn ISO.

### 3.2. Khởi động và chờ cloud-init

```bash
bash scripts/start_lab.sh
```

Lần đầu mỗi VM phải `apt-get update/install`, có thể mất **10–20 phút**.
Script chờ đến khi cả 5 VM ghi `STATUS: READY` vào `/var/log/att-setup.log`.

### 3.3. Kiểm tra baseline (trước khi tấn công)

```bash
bash scripts/verify_baseline.sh
```

Kỳ vọng:

- 5 VM đúng IP (`ip -br addr`).
- C2 báo 2 bot online (`bots` → `["10.10.10.20", "10.10.10.21"]`).
- 6 request từ Bot1 tới `http://10.10.10.30/` xen kẽ
  `{"server":"backend-1"...}` và `{"server":"backend-2"...}`.
- Suricata/UFW/auto-block **chưa bật** (để bước 1 tấn công được).

---

## 4. Ba bước thực hành

### Bước 1 — Botnet tấn công victim

```bash
bash scripts/step1_attack.sh 20
```

Tham số `20` = thời gian flood (giây). Script sẽ:

1. Ghi baseline trước tấn công (4 request từ Bot1).
2. Gửi lệnh từ C2: `attack 10.10.10.30 80 20 http`.
3. C2 gửi lệnh JSON tới **cả 2 bot**; mỗi bot chạy HTTP flood 30 thread.
4. Ghi log C2, log 2 bot, `ss -s`, `uptime`, access log và số lượng
   request/HTTP status trên victim trước – trong – sau tấn công.

Bằng chứng nằm ở `vbox-lab/evidence/<timestamp>-step1-attack/`.

Có thể thử SYN flood (mạnh hơn, cần `sudo` trên bot):

```bash
# trên ATT-C2-Server
printf 'attack 10.10.10.30 80 15 syn\n' | nc -w 3 127.0.0.1 9998
```

### Bước 2 — Bật Suricata + firewall + auto-block

```bash
bash scripts/step2_defense.sh 20
```

Script bật trên victim:

1. **Nginx protected config**: `limit_req` 10 r/s mỗi IP, `limit_conn` 20,
   chặn User-Agent `LOIC|Hping|slowloris`.
2. **Suricata**: `HOME_NET=10.10.10.0/24`, rules phát hiện HTTP flood
   (>50 req/10 s/IP), SYN flood (>100 SYN/5 s/IP), slow connection, UDP flood,
   LOIC UA.
3. **UFW**: default deny incoming, chỉ mở 22 và 80.
4. **Auto-block**: đọc `fast.log`, khi có alert thì
   `ufw insert 1 deny from <IP>` → chặn ngay IP bot.

Sau đó script lặp lại tấn công và chụp:

- `fast.log` có msg `ATT LAB HTTP FLOOD` với source là IP bot.
- `ufw status numbered` có rule DENY cho 10.10.10.20 / 10.10.10.21.
- `/var/log/att-blocks.log` ghi thời điểm block.
- Curl từ bot bị **timeout/connection failed**; curl từ C2 (không tấn công)
  vẫn **200** → chứng minh chặn đúng đối tượng, không chặn oan toàn mạng.

Bằng chứng: `vbox-lab/evidence/<timestamp>-step2-defense/`.

### Bước 3 — Cân bằng tải và failover

```bash
bash scripts/step3_loadbalance.sh
```

Script:

1. Xóa các rule auto-block cũ để client test lại được.
2. Gửi 10 request từ C2 tới `http://10.10.10.30/` → thấy xen kẽ
   `backend-1` / `backend-2` (round-robin).
3. Dừng Nginx trên **ATT-Backend2** → sau ~5–7 s, mọi request chỉ còn
   `backend-1` (failover nhờ `max_fails=1 fail_timeout=5s` +
   `proxy_next_upstream`).
4. Bật lại Backend2 → round-robin quay lại.

Bằng chứng: `vbox-lab/evidence/<timestamp>-step3-loadbalance/`.

---

## 5. Chạy lại / thu thập bằng chứng

```bash
# Đưa victim về trạng thái "chưa phòng thủ" để demo lại từ đầu
bash scripts/reset_lab.sh

# Chụp toàn bộ log/trạng thái 5 VM vào evidence/
bash scripts/collect_evidence.sh
```

Xem nhanh trên victim (từ WSL, dùng SSH client của Windows):

```bash
"/mnt/c/Windows/System32/OpenSSH/ssh.exe" \
  -i "$(wslpath -w keys/attlab_ed25519)" -p 2225 defender@127.0.0.1
sudo /opt/defense/show_stats.sh
```

---

## 6. Ánh xạ sang báo cáo

| Yêu cầu bài | Minh chứng trong lab |
|---|---|
| Botnet có sẵn / mô phỏng | Kiến trúc C2 + 2 bot, lệnh `attack` từ C2, log 2 bot nhận lệnh |
| Tự tấn công 2 máy | 2 bot cùng flood `10.10.10.30`; log C2 ghi `-> 2 bot(s)` |
| Công cụ phòng chống | Suricata alerts (`fast.log`), UFW DENY, auto-block log |
| Tường lửa | `ufw status numbered` trước/sau block |
| Cân bằng tải | 10 response xen kẽ backend-1/2; cấu hình `upstream` |
| Chịu lỗi | Dừng backend-2 → toàn bộ response là backend-1; bật lại → xen kẽ |
| Dùng WSL điều khiển VirtualBox | `VBoxManage.exe` gọi từ WSL, SSH port-forward 2222–2226 |

### Ảnh/log nên chụp

1. `VBoxManage list runningvms` + `ip -br addr` 5 VM.
2. 6 request baseline xen kẽ backend-1/2.
3. Bước 1: C2 log `ATTACK ... -> 2 bot(s)`, bot log, victim `ss -s`/access log.
4. Bước 2: Suricata `fast.log`, `ufw status numbered`, `att-blocks.log`,
   curl từ bot thất bại vs curl từ C2 thành công.
5. Bước 3: 10 request xen kẽ, rồi toàn backend-1 khi backend-2 down, rồi
   xen kẽ lại khi backend-2 up.
6. Cấu hình Nginx `upstream` và rule Suricata.

---

## 7. Xử lý lỗi thường gặp

| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| `UUID ... does not match ... media registry` | Base VMDK bị đăng ký lỗi. Chạy `VBoxManage closemedium disk "<base.vmdk>"` rồi tạo lại VM. |
| SSH từ WSL `Connection refused` | Bạn đang dùng `ssh` của WSL (loopback riêng). Dùng `bash scripts/test_ssh.sh` hoặc gọi `C:\Windows\System32\OpenSSH\ssh.exe` như `config.sh`. |
| SSH báo `UNPROTECTED PRIVATE KEY FILE` / treo ở password | Windows OpenSSH từ chối ACL của key. Chạy `icacls C:\Users\Admin\Desktop\ATT\vbox-lab\keys\attlab_ed25519 /inheritance:r /grant:r "%USERNAME%:R"`. |
| VM không có IP 10.10.10.x, NIC `DOWN` | `network-config` sai: netplan cần MAC dạng `08:00:27:aa:00:01`. Kiểm tra `sudo cat /etc/netplan/50-cloud-init.yaml`; sửa template rồi chạy `bash scripts/rebuild_cidata.sh v4`. |
| `suricata: inactive` | Chạy `sudo journalctl -u suricata -n 50`; kiểm tra interface trong `/etc/systemd/system/suricata.service.d/override.conf` (phải là `enp0s3`). |
| Không thấy alert | Rule chưa load: kiểm tra `suricata -T -c /etc/suricata/suricata.yaml`; xem `default-rule-path` và file `suricata.rules`; chắc chắn bot không nằm trong whitelist. |
| Bot bị chặn nhưng SSH vẫn vào được | Đúng thiết kế: auto-block whitelist NAT gateway `10.10.10.1` (đường SSH từ WSL). |
| `bots` trên C2 trả về `[]`, log bot online/offline liên tục | `socket.create_connection(timeout=10)` giữ timeout cho cả `recv()` khiến bot ngắt sau 10s. Bot agent phải gọi `sock.settimeout(None)` sau khi kết nối (đã có trong template). |
| Round-robin chỉ ra 1 backend | Dùng trình duyệt keep-alive sẽ dính 1 backend; lab dùng `curl` mỗi lần một kết nối mới. |
| NAT Network mất port-forward | Chạy lại `create_vms.sh` (script tạo lại NAT network + forward). |

---

## 8. Cấu trúc thư mục

```
vbox-lab/
├── config.sh                 # IP, MAC, port, helper SSH
├── README.md                 # tài liệu này
├── BAO-CAO-BTTL-ATTT.md      # báo cáo bài tập lớn
├── BAO-CAO-BTTL-ATTT.docx    # bản Word của báo cáo
├── BAO-CAO-BTTL-ATTT.pdf     # bản PDF để xem/in
├── cloud-init/
│   ├── c2/user-data          # C2 server + control port 9998
│   ├── bot/user-data         # bot agent + HTTP flood (dùng cho Bot1/Bot2)
│   ├── victim/user-data      # Nginx LB, Suricata rules, UFW, auto-block
│   └── backend2/user-data    # backend-2 Nginx :8081
├── iso/make_iso.py           # tạo ISO NoCloud (cidata) bằng pycdlib
├── keys/                     # SSH key tự sinh (không commit private key)
├── scripts/
│   ├── create_vms.sh         # tạo NAT network + ISO + 5 VM
│   ├── lib_cidata.sh         # dựng user-data/network-config + ISO (dùng chung)
│   ├── rebuild_cidata.sh     # dựng lại ISO cho VM đã có rồi reboot
│   ├── start_lab.sh          # boot + chờ cloud-init
│   ├── test_ssh.sh           # kiểm tra SSH từng VM
│   ├── verify_baseline.sh    # kiểm tra IP/dịch vụ/LB baseline
│   ├── step1_attack.sh       # Bước 1
│   ├── step2_defense.sh      # Bước 2
│   ├── step3_loadbalance.sh  # Bước 3
│   ├── reset_lab.sh          # reset về trạng thái trước phòng thủ
│   ├── collect_evidence.sh   # snapshot toàn bộ log
│   └── check.sh              # kiểm tra cú pháp
└── evidence/                 # log/minh chứng sinh ra khi chạy
```
