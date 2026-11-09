# Lab DDoS — Phát hiện & Giảm thiểu tác động với Suricata + Cân bằng tải (pfSense + HAProxy)

> Tài liệu tổng hợp cho bài tập lớn môn Cơ sở An toàn thông tin.
> Soạn ngày 2026-11-01 dựa trên hội thoại ChatGPT "Hướng dẫn thực hành DDoS an toàn"
> (https://chatgpt.com/s/cx_6ae6eee403d48191a494d057424a73c6) và tài liệu chính thức của Netgate (pfSense) và Suricata.
> Môi trường: VirtualBox — Kali Linux, Windows 11, pfSense.

---

## 1. Tóm tắt tình trạng lab (dựa trên hội thoại ChatGPT)

### Đã hoàn thành (có xác nhận trong hội thoại)

- Hai máy ảo **Kali Linux (10.10.10.10)** và **Windows 11** nối nhau qua **Internal Network** của VirtualBox (mạng ảo chỉ các VM trong cùng một tên mạng nhìn thấy nhau, không ra Internet), ban đầu đặt IP tĩnh Kali `10.10.10.10`, Windows `10.10.10.20`. Các lỗi đã xử lý: từng mở nhầm `127.0.0.1` từ Kali, Windows từng dính địa chỉ tự gán `169.254.72.113`, sau đó đặt IP tĩnh đúng và **Kali truy cập được web server trên Windows**.
- Windows chạy web server thử nghiệm bằng Python: `py -3 -m http.server 8080` phục vụ thư mục `C:\ddos-lab`, kèm quy tắc Windows Firewall cho phép riêng IP Kali vào cổng 8080.
- **JMeter** (công cụ kiểm thử tải) đã cài trên Kali, đã xử lý lỗi Java (`sun.awt.X11`) bằng các tùy chọn `--add-opens`, và đã xác nhận "tấn công được" — bước tạo lưu lượng chạy thành công.

### Được hướng dẫn NHƯNG KHÔNG có bằng chứng đã làm xong

- **Suricata trên Kali** chạy IPS qua NFQUEUE (chặn lưu lượng ngay trên máy Kali) — đã hỏi, được hướng dẫn chi tiết, nhưng chưa thấy ảnh/log xác nhận chạy được.
- **Phương án gateway thứ ba (clone Kali)** — đã từ chối vì khó hiểu.
- **pfSense làm gateway + gói Suricata trên pfSense** — hướng dẫn cuối cùng (6 chặng). Hội thoại chuyển sang mô hình IP mới: `ATTACKER-LAN` (10.10.10.0/24) và `SERVER-LAN` (10.10.20.0/24), pfSense WAN `10.10.10.1`, LAN `10.10.20.1`, Windows đổi thành `10.10.20.20`. **Tin nhắn cuối là câu hỏi về cân bằng tải — không có ảnh/log xác nhận pfSense đã cài xong, Suricata đã bật hay đã chặn được.**
- **HAProxy** — lần đầu hướng dẫn chạy trên Kali (chưa có xác nhận cài), sau đó chuyển hướng sang "HAProxy trên pfSense" nhưng mới chỉ nêu ý tưởng 4 giai đoạn, **chưa có hướng dẫn chi tiết và chưa làm**.

**Kết luận:** điểm chắc chắn là "2 VM cơ bản hoạt động + JMeter tạo tải được"; điểm chưa chắc chắn là "pfSense + Suricata đã dựng tới đâu". Phần 5 bắt đầu bằng **Bước 0 tự kiểm tra hiện trạng**.

---

## 2. Cân bằng tải là gì?

**Ví dụ đơn giản:** một quầy bán vé có 1 cửa vào nhưng 3 nhân viên phục vụ. Nếu tất cả khách dồn vào một nhân viên, người đó quá tải trong khi hai người kia đứng không. **Cân bằng tải (load balancing)** là đặt một "người điều phối" ở cửa vào, luân chuyển khách tới các nhân viên đang rảnh.

Áp vào web:

- **Bộ cân bằng tải (load balancer)** = người điều phối. Trong lab này là **HAProxy** (phần mềm mã nguồn mở rất phổ biến làm proxy/cân bằng tải). Nó có một địa chỉ duy nhất cho khách gọi là **frontend** (cửa vào), và danh sách các **backend** (các máy chủ thực sự chạy website phía sau).
- **Thuật toán phân phối** phổ biến nhất là **round-robin**: yêu cầu số 1 cho máy A, số 2 cho máy B, số 3 cho máy A… luân phiên.
- **Health check** (kiểm tra sức khỏe): HAProxy định kỳ "gõ cửa" từng backend (gửi một yêu cầu HTTP nhỏ). Máy nào không trả lời bị đánh dấu chết và tạm không nhận yêu cầu — khách không bị gửi tới máy hỏng. Đây là chỗ tạo ra khả năng **chịu lỗi (failover)**.

### Phân biệt 3 vai trò

| | Làm gì | KHÔNG làm gì |
|---|---|---|
| **Cân bằng tải (HAProxy)** | Chia các **yêu cầu hợp lệ** cho nhiều máy chủ để không máy nào quá tải; tự động bỏ máy hỏng nhờ health check | **Không phân biệt yêu cầu tốt/xấu.** Nếu lưu lượng xấu vẫn đến được nó, nó sẽ "công bằng" phân phối cả lưu lượng xấu cho tất cả backend |
| **Suricata** | **Phát hiện** (IDS — chỉ cảnh báo) và **chặn** (IPS — chủ động chặn) lưu lượng khớp luật/ngưỡng đáng ngờ, ví dụ một IP gửi quá nhiều GET/10 giây | Không phân phối tải, không giúp backend xử lý nhanh hơn |
| **Cả hai** | Bổ sung cho nhau: Suricata lọc ở cửa, HAProxy chia việc cho phần lưu lượng còn lại | Cân bằng tải **không phải là giải pháp chống DDoS** |

**Điểm quan trọng cho báo cáo:** cân bằng tải giúp hệ thống *chịu được tải lớn hơn* với lưu lượng bình thường, nhưng nếu không có biện pháp lọc phía trước, HAProxy sẽ **chuyển tiếp cả lưu lượng tấn công** tới các backend — tấn công nhắm thẳng vào HAProxy thậm chí chỉ cần "gục" một điểm duy nhất. Vì vậy: **Suricata = phát hiện/chặn, HAProxy = phân phối và duy trì dịch vụ**, và thứ tự đặt chúng rất quan trọng (mục 4).

---

## 3. Công cụ phù hợp cho lab VirtualBox

**Khuyến nghị: HAProxy cài dưới dạng package trên chính pfSense.**

| Phương án | Ưu điểm | Nhược điểm |
|---|---|---|
| **HAProxy trên pfSense** ✅ | Nằm đúng vị trí "cửa vào" của mạng, cùng chỗ với Suricata → đúng nguyên lý "lọc trước, phân phối sau"; giao diện web pfSense; là package chính thức — tài liệu Netgate mô tả hỗ trợ "high availability, load balancing, and proxying for TCP, HTTP and HTTPS"; có health check và trang thống kê (stats) để chụp hình báo cáo | Cần thêm RAM/CPU cho VM pfSense (khuyến nghị 2 GB RAM, 2 CPU); cấu hình GUI nhiều mục; tính năng có thể khác nhau giữa các phiên bản package |
| HAProxy trực tiếp trên Kali | Dễ nhất, cấu hình 1 file text | Sai vị trí: bộ cân bằng tải nằm **trên chính máy tấn công**; Suricata/pfSense trở nên thừa; không minh họa mô hình thực tế |
| Nginx / phần cứng / CDN | — | Không cần thiết cho lab; CDN là giải pháp "thế giới thực" vượt phạm vi bài tập |

### Cần bao nhiêu backend?

Ít nhất **2 máy chủ độc lập** — nếu chỉ có 1 backend thì không có gì để "cân bằng", cũng không chứng minh được health check/failover.

**Nếu chỉ có một máy Windows:** vẫn có thể chạy **hai tiến trình web server trên cùng VM ở hai cổng khác nhau** (ví dụ 8080 và 8081, mỗi cổng một thư mục, nội dung khác nhau). Cách này:

- ✅ Chứng minh được: HAProxy nhận yêu cầu ở frontend rồi **chia yêu cầu cho cả hai cổng** — nhìn thấy round-robin hoạt động.
- ❌ **KHÔNG chứng minh được khả năng chịu lỗi giữa hai máy độc lập**, và báo cáo không được ghi là "hai máy chủ". Lý do: hai "backend" vẫn dùng chung một VM — cùng CPU, RAM, ổ đĩa, card mạng. VM tắt là **cả hai** cùng chết. Đây là **mô phỏng hai dịch vụ, không phải hai máy chủ**.

**Khuyến nghị cho báo cáo:** clone Windows VM hiện có thành **backend thứ hai là một VM thật sự** (Full Clone, đổi IP trước khi bật cùng lúc — xem Bước 4). Khi đó mới trình diễn được kịch bản chịu lỗi thật: tắt server trên VM2 → HAProxy nhận ra qua health check → toàn bộ yêu cầu được phục vụ bởi VM1.

---

## 4. Thứ tự đặt Suricata và bộ cân bằng tải

Bối cảnh kỹ thuật: trong pfSense, **Suricata package có 2 chế độ**:

- **Legacy Mode** — Suricata theo dõi bản sao lưu lượng; khi một luật phát sinh cảnh báo và **Block Offenders** bật, Suricata *chèn block của máy phát sinh cảnh báo vào tường lửa pf*. Tài liệu Netgate ghi: *"When checked, Snort will automatically insert a firewall block of the host generating an alert"*, kèm tùy chọn **Kill States** và **Which IP to Block: SOURCE / DESTINATION / BOTH**.
- **Inline IPS Mode** — theo tài liệu Suricata: netmap tạo *cầu tầng 2 giữa 2 card mạng*, gói bị drop "không được truyền tiếp" (chặn ngay trên đường đi); cần card mạng/driver hỗ trợ netmap và có cảnh báo *"bạn có thể tự khóa mình khỏi hệ thống"*.

Đường đi gói tin và "Suricata nhìn thấy gì" **phụ thuộc chế độ này**.

### Phương án A — Lọc phía trước: Suricata đứng trước bộ cân bằng tải

```
Kali 10.10.10.10 ──> [Suricata chặn/lọc] ──> [HAProxy] ──┬──> Backend 1
                                                          └──> Backend 2
```

- **Luồng gói:** Kali gửi gói → Suricata kiểm tra → hợp lệ thì đến HAProxy → HAProxy **mở kết nối mới** tới backend.
- **Suricata thấy IP gì:** IP nguồn **thật của client** (10.10.10.10) — vì lọc diễn ra trước khi proxy can thiệp. Rule giới hạn "3 request/10 giây theo IP nguồn" hoạt động đúng nghĩa.
- **Ưu:** lưu lượng xấu bị chặn **trước khi** chạm HAProxy/backend; đây là mô hình thực tế (CDN/ISP luôn scrubbing — "rửa" lưu lượng — trước khi đưa vào máy chủ).
- **Nhược:** rule quá chặt sẽ chặn nhầm client hợp lệ; cần chỉnh ngưỡng cẩn thận.

### Phương án B — Bộ cân bằng tải đứng trước, Suricata đứng sau

```
Kali 10.10.10.10 ──> [HAProxy] ──> [Suricata] ──┬──> Backend 1
                                                 └──> Backend 2
```

- **Luồng gói:** Kali → HAProxy nhận kết nối → HAProxy mở kết nối mới đi ra phía sau → Suricata kiểm tra → backend.
- **Suricata thấy IP gì:** **IP của chính proxy**, không phải của client! Với HAProxy trên pfSense, mọi kết nối đi ra LAN mang IP nguồn `10.10.20.1`. Hệ quả: rule "chặn theo IP nguồn" không phân biệt được kẻ tấn công với người dùng thật — tất cả đều "là 10.10.20.1". Giải pháp thực tế là HAProxy gắn header **X-Forwarded-For** (chứa IP thật) hoặc **PROXY protocol**, nhưng Suricata phải được cấu hình đọc header đó, chỉ áp dụng cho HTTP, dễ lỗi — không phù hợp lab người mới.
- **Ưu:** Suricata kiểm soát chặt "cái gì được phép chạm backend".
- **Nhược:** lưu lượng xấu **vẫn đã vào tới** LB và chiếm tài nguyên; mất IP nguồn thật khiến phát hiện theo từng kẻ tấn công gần như bất khả thi; kẻ tấn công có thể đánh sập trực tiếp LB. Thực tế không ai đặt scrubbing sau LB.

### Phương án C — Suricata và HAProxy cùng chạy trên pfSense ✅

```
Kali 10.10.10.10 ──WAN──> pfSense [ Suricata | tường lửa pf | HAProxy ] ──LAN──┬──> 10.10.20.20:8080
                                                                                └──> 10.10.20.21:8080
```

- **Luồng gói (Legacy Mode + Block Offenders):** gói vào WAN → Suricata giám sát bản sao và, khi luật phát cảnh báo, chèn IP nguồn vào bảng chặn của pf (pf chặn ở tầng tường lửa, Kill States cắt các kết nối đang treo) → gói hợp lệ được pf cho qua → HAProxy (dịch vụ trong pfSense, lắng nghe IP WAN cổng 80) nhận kết nối → HAProxy mở kết nối mới ra LAN tới backend.
- **Luồng gói (Inline IPS Mode/netmap):** gói bị dẫn trực tiếp xuyên qua Suricata; gói khớp luật drop bị vứt ngay, không đến pf lẫn HAProxy. Cần card hỗ trợ netmap, cẩn trọng mất kết nối quản trị.
- **Suricata thấy IP gì:** với lưu lượng client→frontend, là **IP thật của Kali** (10.10.10.10, đích là IP WAN của pfSense) — rule rate-limit hoạt động đúng.
- **Vấn đề "proxy che IP nguồn" cần biết:** backend **không** nhìn thấy IP Kali nữa — log web server trên Windows sẽ hiện mọi yêu cầu đến từ `10.10.20.1` (IP LAN của pfSense). Trong báo cáo: đây là hành vi đúng của proxy; HAProxy có thể gắn X-Forwarded-For để lưu IP thật vào header HTTP (web server Python mặc định không hiển thị header này trong log, ghi nhận qua cấu hình HAProxy là đủ).
- **Ưu cho lab:** chỉ cần 3 VM; một hộp làm đủ cả "cửa lọc" lẫn "người điều phối"; mô tả được cả hai vai trò trong báo cáo; quản trị tập trung.
- **Nhược/cẩn trọng:** Legacy Mode block theo **IP nguồn** — khi Kali bị block thì **cả truy cập HAProxy từ Kali cũng đứt** (đây đúng ra là chứng minh tốt: kẻ tấn công bị cắt khỏi mọi dịch vụ). Biết chỗ xóa block: tab Blocked/Blocks của Suricata.

### Kết luận cho lab

Chọn **Phương án C: Suricata (Legacy Mode + Block Offenders) đứng trước, HAProxy đứng sau, cùng trên pfSense**. Lý do: đúng nguyên lý "lọc trước — phân phối sau", Suricata giữ được IP nguồn thật, tiết kiệm VM, mỗi thành phần đúng vai trò. Dùng **Legacy Mode + Block Offenders làm chế độ chính** (ổn định trong VirtualBox); **Inline Mode (netmap) chỉ thử thêm khi lab đã chạy trơn** — phụ thuộc driver card mạng (trong VirtualBox nên dùng card **Intel PRO/1000 MT**) và có nguy cơ mất kết nối quản trị nếu cấu hình sai. Chi tiết hành vi có thể khác nhau giữa các phiên bản pfSense CE/Plus và phiên bản package — nếu tùy chọn nào trong GUI không có đúng như mô tả, chụp hình lại và điều chỉnh theo thực tế.

---

## 5. Hướng dẫn cấu hình từng bước

**Giới hạn an toàn (giữ nguyên trong toàn bộ lab):** chỉ gửi HTTP yêu cầu nhẹ (curl/JMeter vài chục request), chỉ trong mạng Internal Network cô lập của VirtualBox, chỉ nhắm vào các máy của bạn. Không tải botnet, không tấn công máy ngoài lab, không tạo flood lớn. Vừa an toàn vừa đủ tạo minh chứng cho báo cáo.

### Sơ đồ mạng đích và bảng IP

```
Kali (JMeter)                 pfSense                        Windows backend 1 (VM gốc)
10.10.10.10 ──ATTACKER-LAN──> WAN 10.10.10.1   (Suricata + HAProxy ở đây)
                              LAN 10.10.20.1 ──SERVER-LAN──┬──> 10.10.20.20:8080
                                                            └──> 10.10.20.21:8080  (Windows backend 2 — clone)
```

| Máy | Mạng VirtualBox | IP | Gateway mặc định |
|---|---|---|---|
| Kali (chạy JMeter) | Adapter 1 = Internal **ATTACKER-LAN** | 10.10.10.10/24 | 10.10.10.1 |
| pfSense — Adapter 1 (WAN) | Internal **ATTACKER-LAN** | 10.10.10.1/24 | để trống |
| pfSense — Adapter 2 (LAN) | Internal **SERVER-LAN** | 10.10.20.1/24 | để trống |
| Windows backend 1 | Adapter 1 = Internal **SERVER-LAN** | 10.10.20.20/24 | 10.10.20.1 |
| Windows backend 2 (clone) | Adapter 1 = Internal **SERVER-LAN** | 10.10.20.21/24 | 10.10.20.1 |

> Nếu máy đang dùng IP khác (ví dụ Windows còn ở 10.10.10.20 như giai đoạn đầu) thì thay theo đúng bảng này; tên `ATTACKER-LAN`/`SERVER-LAN` phải gõ **chính xác từng ký tự** ở mọi adapter cùng một đoạn mạng. Cả hai mạng đều là Internal Network, không dùng Bridged, đánh dấu **Cable Connected**.

---

### Bước 0 — Kiểm tra hiện trạng

- **Làm trên:** máy thật (VirtualBox Manager) + từng VM.
- **Mục tiêu:** biết chính xác đã có gì để không làm lại.
- **Cách kiểm tra:**
  1. VirtualBox Manager: có VM nào tên pfSense chưa? Danh sách adapter từng VM đang nối Internal Network nào?
  2. Nếu có pfSense: bật lên, từ Windows truy cập `https://10.10.20.1` — đăng nhập được không? Vào **System → Package Manager** xem đã cài Suricata/HAProxy chưa?
  3. Trên Kali: `ip -br addr` (xem IP); `curl http://10.10.20.20:8080/` (nếu Windows đã đổi sang 10.10.20.20) hoặc `curl http://10.10.10.20:8080/` (nếu chưa).
- **Kết luận:** theo các bước dưới, **bỏ qua bước nào đã làm xong và xác nhận chạy được**. Nếu chưa cài pfSense → làm từ Bước 1.

### Bước 1 — Nối mạng các VM đúng sơ đồ

- **Làm trên:** VirtualBox Manager (máy thật), với **mọi VM ở trạng thái Powered Off** (không phải Saved).
- **Mục tiêu:** dựng đúng hai đoạn mạng cô lập như bảng trên.
- **Cấu hình:** theo bảng "Mạng VirtualBox" ở trên — pfSense cần **2 adapter** (Adapter 1 → ATTACKER-LAN, Adapter 2 → SERVER-LAN, loại card **Intel PRO/1000 MT Desktop**); pfSense tạm thêm **Adapter 3 = NAT** chỉ để tải package (Bước 3), sau đó tắt đi. Windows tạm đổi sang NAT khi cần tải phần mềm rồi đổi lại.
- **Kiểm tra:** trong Settings → Network của từng VM, tên mạng hiện đúng như bảng; mọi adapter đang dùng đều tick Cable Connected.
- **Lỗi thường gặp:** Adapter 2 chỉnh không được → vì VM đang Running/Saved, hoặc chưa tick **Enable Network Adapter**; hai VM không thấy nhau → tên Internal Network lệch một ký tự.

### Bước 2 — Cài pfSense (bỏ qua nếu đã xong)

- **Làm trên:** máy thật + VM pfSense mới.
- **Mục tiêu:** có gateway giữa hai mạng, chạy Suricata + HAProxy trên đó.
- **Cấu hình:** tải **pfSense CE** (ISO amd64) từ trang chính thức của Netgate; tạo VM: Type **BSD / FreeBSD (64-bit)**, RAM 2 GB, 2 CPU, đĩa 20 GB; gắn ISO vào ổ CD ảo và cài. Sau khi cài, ở console pfSense chọn **2) Set interface(s) IP address** → đặt **LAN = 10.10.20.1/24**, DHCP server trên LAN: **No**. Tạm nối Windows vào SERVER-LAN với IP 10.10.20.20 để mở giao diện quản trị `https://10.10.20.1` từ trình duyệt Windows (chấp nhận cảnh báo chứng chỉ tự ký; đăng nhập mặc định `admin`/`pfsense` và **đổi mật khẩu ngay**).
- **Kiểm tra:** đăng nhập được giao diện web pfSense từ Windows; console pfSense hiện WAN lấy được IP từ NAT (khi Adapter 3 = NAT).
- **Lỗi thường gặp:** quên gắn ISO → VM không boot được trình cài; mở giao diện bằng `http` thay vì `https` → không vào được.

### Bước 3 — Cài package Suricata và HAProxy

- **Làm trên:** giao diện web pfSense (khi pfSense còn Adapter 3 = NAT để có Internet).
- **Mục tiêu:** có sẵn hai công cụ cần dùng.
- **Cấu hình:** **System → Package Manager → Available Packages** → tìm và cài **Suricata**, rồi cài **HAProxy**. Sau khi cài xong: tắt pfSense, **tắt/hủy Adapter 3 (NAT)**, chỉ giữ WAN = ATTACKER-LAN và LAN = SERVER-LAN.
- **Kiểm tra:** menu **Services** xuất hiện mục **Suricata** và **HAProxy** (tên hiển thị có thể hơi khác giữa các phiên bản).
- **Lỗi thường gặp:** không thấy package trong danh sách → pfSense chưa có Internet (kiểm tra Adapter 3 NAT), hoặc repo package chưa cập nhật (nhấn nút cập nhật trong trang Available Packages).

### Bước 4 — Chuẩn bị hai backend

**4a. Backend 1 (Windows gốc):**

- **Làm trên:** Windows VM gốc.
- **Mục tiêu:** máy chủ web thứ nhất, IP mới đúng sơ đồ.
- **Cấu hình:** đặt IP tĩnh **10.10.20.20/24, gateway 10.10.20.1** (ncpa.cpl → Ethernet → IPv4 Properties). Tạo nội dung phân biệt:
  ```powershell
  New-Item -ItemType Directory -Force C:\ddos-lab\backend1
  Set-Content -Path C:\ddos-lab\backend1\index.html -Value "Response from backend 1"
  ```
  Mở firewall cho đúng các nguồn sẽ gọi đến (Kali gọi trực tiếp khi test baseline, và pfSense gọi khi HAProxy phân phối — lưu ý **backend sẽ thấy IP nguồn là 10.10.20.1**):
  ```powershell
  New-NetFirewallRule -DisplayName "DDoS-Lab backends" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080 -RemoteAddress 10.10.10.10,10.10.20.1 -Profile Any
  ```
  Chạy server (để cửa sổ mở):
  ```powershell
  py -3 -m http.server 8080 --bind 0.0.0.0 --directory C:\ddos-lab\backend1
  ```
- **Kiểm tra:** kiểm tra sau Bước 6 bằng Kali.

**4b. Backend 2 — khuyến nghị clone Windows:**

- **Làm trên:** VirtualBox Manager + Windows clone.
- **Mục tiêu:** có backend thứ hai **độc lập thật sự** để chứng minh cân bằng tải và failover.
- **Cách làm:** tắt Windows gốc → nhấp phải → **Clone…** → **Full Clone**, MAC policy "Generate New MAC Addresses For All Network Adapters" → bật **riêng clone lên trước** (Windows gốc giữ tắt) → đổi IP clone thành **10.10.20.21/24, gateway 10.10.20.1** (tránh trùng IP!) → tạo thư mục `C:\ddos-lab\backend2` với nội dung "Response from backend 2", tạo firewall rule như 4a, chạy `py -3 -m http.server 8080 --bind 0.0.0.0 --directory C:\ddos-lab\backend2`.
- **Kiểm tra:** cả hai VM backend bật cùng lúc không báo xung đột; mỗi máy `ipconfig` ra đúng IP riêng.
- **Lỗi thường gặp:** clone xong quên đổi IP → trùng 10.10.20.20, mạng loạn; quên tạo firewall rule trên clone → pfSense không gọi được.

> Phương án thay thế nếu thiếu dung lượng: chạy **hai cổng trên một VM** (8080 và 8081). Chỉ dùng để xem HAProxy chia yêu cầu; **không trình diễn được failover giữa hai máy** — ghi rõ giới hạn này trong báo cáo (mục 3).

### Bước 5 — Chuyển WAN pfSense sang mạng Kali, đặt IP cho Kali

- **Làm trên:** VirtualBox Manager + pfSense web UI + Kali.
- **Mục tiêu:** hoàn thiện đường đi Kali → pfSense → backend.
- **Cấu hình:** pfSense: **Interfaces → WAN** → IPv4 Configuration Type = **Static IPv4**, địa chỉ **10.10.10.1/24**, upstream gateway để trống, **bỏ tick "Block private networks"** trên WAN (vì 10.10.10.0/24 là dải private — nếu không bỏ, pfSense sẽ drop lưu lượng từ Kali). Kali: IP tĩnh **10.10.10.10/24, gateway 10.10.10.1**.
- **Kiểm tra:** từ Kali `ip route get 10.10.20.20` phải chỉ đường qua 10.10.10.1; `ping 10.10.10.1` thành công.
- **Lỗi thường gặp:** quên bỏ "Block private networks" → Kali ping/pfSense không thông; gateway Kali chưa đặt → không đi qua pfSense được.

### Bước 6 — Cho phép lưu lượng thử nghiệm qua tường lửa pfSense

- **Làm trên:** giao diện web pfSense.
- **Mục tiêu:** pfSense mặc định chặn mọi kết nối vào WAN; cần rule cho phép đúng luồng lab.
- **Cấu hình:** **Firewall → Rules → WAN → Add** (thêm **⬆** lên trên cùng), tạo **hai** rule:
  1. Cho phép Kali vào thẳng backend (dùng cho test Suricata và baseline): Action **Pass**, Protocol **TCP**, Source **10.10.10.10**, Destination **10.10.20.20**, Destination port **8080**.
  2. Cho phép Kali vào frontend HAProxy (dùng cho test cân bằng tải): Action **Pass**, Protocol **TCP**, Source **10.10.10.10**, Destination **"WAN address"** (chính pfSense), Destination port **80**.
  Nhấn **Save → Apply Changes** sau mỗi rule.
- **Kiểm tra (baseline):** từ Kali, `curl http://10.10.20.20:8080/` — phải thấy "Response from backend 1". Đây là mốc quan trọng: **mạng thông, chưa có ai chặn gì**.
- **Lỗi thường gặp:** quên Apply Changes → rule chưa có hiệu lực; Destination chọn nhầm "any" → mở rộng quá cần thiết.

### Bước 7 — Cấu hình Suricata trên pfSense để phát hiện và chặn

- **Làm trên:** giao diện web pfSense.
- **Mục tiêu:** Suricata giám sát lưu lượng vào WAN và tự chặn IP gửi quá ngưỡng (Legacy Mode + Block Offenders — chế độ ổn định nhất trong VirtualBox).
- **Cấu hình:**
  1. **Services → Suricata → Global Settings:** đặt **HOME_NET** bao gồm `10.10.20.0/24` (mạng được bảo vệ).
  2. **Interfaces → Add** → chọn **WAN** → tick Enable. Trong cài đặt giao diện WAN: chế độ để **Legacy Mode** (nếu thử **Inline IPS Mode**: đảm bảo card là Intel PRO/1000; nếu Suricata không khởi động hoặc mất kết nối quản trị thì quay lại Legacy); tick **Block Offenders**, tick **Kill States**, **Which IP to Block = SOURCE**.
  3. **Pass Lists:** kiểm tra danh sách pass được gán cho giao diện WAN **không chứa 10.10.10.10** (Pass List là "danh sách IP Suricata không bao giờ block" — nếu Kali nằm trong đó thì mọi thử nghiệm không chặn được).
  4. **Rules → Defined Custom Rules** (của giao diện WAN), thêm rule thử nghiệm:
     ```
     alert http 10.10.10.10 any -> 10.10.20.20 8080 (msg:"LAB IPS: HTTP request rate exceeded"; flow:established,to_server; http.method; content:"GET"; detection_filter:track by_src,count 3,seconds 10; sid:1000001; rev:1;)
     ```
     Giải thích cho báo cáo: **trong Legacy Mode dùng hành động `alert`** — Suricata phát sinh cảnh báo rồi Block Offenders chèn block vào pf; hành động `drop` chỉ drop gói ngay trên đường đi ở **Inline Mode**. `detection_filter` nghĩa là: khi 1 IP nguồn gửi quá 3 GET trong 10 giây, các yêu cầu khớp tiếp theo phát sinh cảnh báo → bị block.
  5. Lưu → **Apply** → nhấn nút start/restart Suricata trên giao diện WAN.
- **Kiểm tra:** từ Kali chạy `curl http://10.10.20.20:8080/` liên tục (hoặc JMeter: 2 thread, 5 loop, timer 500–1000 ms, nhắm `10.10.20.20:8080`). Kỳ vọng: vài request đầu trả về 200; sau ngưỡng, curl/JMeter bị treo/lỗi; trong **Services → Suricata → Alerts** xuất hiện "LAB IPS: HTTP request rate exceeded" với Source 10.10.10.10; trong tab **Blocked/Blocks** xuất hiện 10.10.10.10. Sau đó `curl` từ Kali không vào được **bất kỳ** dịch vụ nào qua pfSense (block theo IP nguồn) — xóa block trong tab Blocked để tiếp tục lab.
- **Lỗi thường gặp:** không thấy alert → kiểm tra rule đã lưu vào đúng giao diện WAN chưa, Kali có nằm trong Pass List không, Suricata có đang chạy trên WAN không; sau khi block, tưởng lab lỗi → nhớ kiểm tra tab Blocked.

### Bước 8 — Cấu hình HAProxy trên pfSense

- **Làm trên:** giao diện web pfSense.
- **Mục tiêu:** frontend nhận yêu cầu ở WAN:80, phân phối round-robin cho 2 backend, có health check.
- **Cấu hình:** **Services → HAProxy**:
  1. Tạo **Backend pool**: tên `be_lab`; **Server 1** = `10.10.20.20`, port 8080; **Server 2** = `10.10.20.21`, port 8080; health check dạng HTTP (kiểm tra GET `/`, kỳ vọng phản hồi thành công); chế độ **HTTP (mode http)**.
  2. Tạo **Frontend**: tên `fe_lab`; **bind trên địa chỉ WAN (10.10.10.1), port 80**; default backend = `be_lab`; bật tùy chọn thêm **X-Forwarded-For** nếu có (để lưu IP thật của client vào header).
  3. Bật trang **Stats** của HAProxy (tùy chọn stats trong cấu hình) — dùng để chụp hình.
- **Kiểm tra:** từ Kali gửi 6 yêu cầu lần lượt, **mỗi lệnh curl là một kết nối mới**:
  ```bash
  for i in 1 2 3 4 5 6; do curl -s http://10.10.10.1/ ; echo; done
  ```
  Kỳ vọng: xen kẽ "Response from backend 1" / "Response from backend 2".
- **Lỗi thường gặp:** quên rule tường lửa số 2 (Bước 6) → Kali không vào được cổng 80; dùng trình duyệt giữ kết nối keep-alive → thấy toàn 1 backend (hành vi đúng của HTTP keep-alive, không phải lỗi); backend firewall chưa allow `10.10.20.1` → health check báo DOWN trong stats.

### Bước 9 — Trình diễn failover (chỉ làm được khi có 2 VM backend độc lập)

- **Làm trên:** Windows backend 2 + Kali + pfSense stats.
- **Mục tiêu:** chứng minh health check phát hiện backend chết và hệ thống vẫn phục vụ.
- **Cách làm:** mở trang Stats của HAProxy (cả hai server **UP**) → trên backend 2 nhấn **Ctrl+C** để dừng server → chờ vài giây (health check chu kỳ) → chạy lại vòng curl từ Kali: **tất cả phản hồi là "backend 1"**, stats hiện server 2 **DOWN** → bật lại server 2 → stats về UP và round-robin quay lại.
- **Kiểm tra:** chụp stats ở từng thời điểm + kết quả curl.
- **Lỗi thường gặp:** đánh giá quá sớm (chưa chờ health check); sau khi bật lại server, phải đợi nó UP mới thấy phân phối trở lại.

### Bước 10 (tùy chọn, nâng cao) — Suricata bảo vệ cả frontend HAProxy

Thêm một rule custom nữa nhắm vào `10.10.10.1 80` để chứng minh "lọc đứng trước cả bộ cân bằng tải": kẻ tấn công bị block trước khi chạm HAProxy. Làm sau khi mọi thứ trên chạy ổn, không làm cùng lúc khi đang gỡ lỗi.

---

## 6. Ảnh/log cần chụp để làm minh chứng báo cáo

### Chứng minh 1 — Suricata phát hiện/chặn lưu lượng thử nghiệm

- Trang cấu hình rule custom trong Suricata (hiện rõ msg, ngưỡng count 3/seconds 10).
- Tab **Alerts** của Suricata: dòng cảnh báo "LAB IPS: HTTP request rate exceeded" với **Source = 10.10.10.10**.
- Tab **Blocked/Blocks**: IP 10.10.10.10 xuất hiện sau khi vượt ngưỡng.
- Kali: kết quả curl/JMeter **trước** khi bị block (HTTP 200) và **sau** (timeout/lỗi) — chụp cả hai.
- Nếu chạy được Inline Mode: thêm ảnh log drop (so sánh hai chế độ là điểm cộng lớn).

### Chứng minh 2 — HAProxy phân phối yêu cầu tới các backend

- Kết quả vòng `curl` xen kẽ "Response from backend 1" / "Response from backend 2" từ một địa chỉ frontend duy nhất (10.10.10.1).
- Trang **Stats** của HAProxy: 2 server **UP**, số request counter tăng ở **cả hai** backend.
- Cửa sổ PowerShell trên **từng** backend hiện log GET request nhận được (ghi chú: log hiện IP nguồn là `10.10.20.1` — kèm giải thích proxy ở mục 4).
- Ảnh cấu hình frontend + backend pool trong pfSense.

### Chứng minh 3 — Chịu lỗi khi một backend dừng (cần 2 VM backend)

- Stats **trước**: 2 server UP, màu xanh.
- Stats **sau khi dừng server trên backend 2**: server 2 hiện **DOWN** trong khi curl từ Kali vẫn nhận phản hồi 200 từ backend 1 liên tục.
- Cửa sổ PowerShell backend 2 đang dừng (thể hiện server đã tắt thật).
- Stats **sau khi bật lại**: server 2 UP và phân phối quay lại.

### Bổ sung

- Sơ đồ mạng + `ipconfig`/`ip -br addr` các máy, 2 rule WAN trong pfSense.
- Một đoạn văn giới hạn thí nghiệm (một nguồn gửi, tải nhỏ, mạng cô lập — không phải DDoS phân tán thực) để phần trình bày chặt chẽ.

---

## Nguồn tham khảo đã kiểm tra

- Netgate Docs — IDS/IPS (Snort & Suricata trên pfSense): https://docs.netgate.com/pfsense/en/latest/packages/snort/index.html
- Netgate Docs — Block Offenders / Kill States / Which IP to Block: https://docs.netgate.com/pfsense/en/latest/packages/snort/interface-settings.html
- Netgate Docs — Pass Lists: https://docs.netgate.com/pfsense/en/latest/packages/snort/setup.html
- Netgate Docs — Package List (Suricata, HAProxy): https://docs.netgate.com/pfsense/en/latest/packages/list.html
- Netgate Docs — HAProxy package: https://docs.netgate.com/pfsense/en/latest/packages/haproxy.html
- Suricata Docs — Netmap/IPS mode: https://docs.suricata.io/en/latest/capture-hardware/netmap.html
- Suricata Docs — thresholding/detection_filter: https://docs.suricata.io/en/latest/rules/thresholding.html
- Suricata Docs — IPS inline cho Linux (NFQUEUE): https://docs.suricata.io/en/suricata-6.0.20/setting-up-ipsinline-for-linux.html
- VirtualBox User Manual (Internal Networking): https://download.virtualbox.org/virtualbox/6.1.50/UserManual.pdf
- HAProxy Docs — backends/round-robin: https://www.haproxy.com/documentation/haproxy-configuration-tutorials/proxying-essentials/configuration-basics/backends/
- Netgate Docs — Block private networks: https://docs.netgate.com/pfsense/en/latest/interfaces/configure.html
