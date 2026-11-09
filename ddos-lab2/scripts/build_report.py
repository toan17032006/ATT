# -*- coding: utf-8 -*-
"""Build the final BTL report from the sample DOCX, filling real lab data."""
import os
import re
import shutil
import subprocess
import sys
import unicodedata

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SRC = r"C:\Users\Admin\Downloads\Bao_cao_DDoS_hoan_chinh.docx"
OUT_DIR = r"C:\Users\Admin\Desktop\ATT"
OUT_DOCX = os.path.join(OUT_DIR, "Bao_cao_BTL_ATTT_DDoS_Hoan_chinh.docx")
OUT_PDF = os.path.join(OUT_DIR, "Bao_cao_BTL_ATTT_DDoS_Hoan_chinh.pdf")
EVID = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"
SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"

# ---------------------------------------------------------------- prose edits
REPL = {
    2: "Khoa An toàn thông tin",
    18: "Báo cáo do một thành viên thực hiện. Bảng phân công ghi nhận toàn bộ phần việc từ xây dựng môi trường, cấu hình công cụ, thực hiện phép thử, thu thập minh chứng đến biên soạn báo cáo.",
    19: "TÓM TẮT",
    21: "Mô hình gồm hai máy Kali Linux sử dụng Apache JMeter, một máy pfSense chạy đồng thời Suricata Inline IPS và HAProxy, cùng hai máy Ubuntu 24.04 cung cấp dịch vụ web bằng Python HTTP Server. Hai nguồn gửi yêu cầu tới cùng địa chỉ frontend. Suricata kiểm tra lưu lượng tại WAN của pfSense; HAProxy phân phối những yêu cầu được tiếp nhận tới các backend đang hoạt động. Cách bố trí này cho phép quan sát vai trò bổ sung của kiểm tra nội dung, chính sách theo ngưỡng và cân bằng tải.",
    23: "Các phép thử đã hoàn tất trên môi trường thật. KB1 xác nhận cả hai nguồn nhận HTTP 200 qua frontend. KB2 cho thấy yêu cầu /ips-test.txt bị chặn khi IPS bật (timeout, 0 byte) và được phục vụ khi IPS tắt. KB3 ghi 80 mẫu, 0 lỗi; hai backend nhận 42 yêu cầu mỗi server. KB4 với rate_filter ghi 6 sự kiện DROP SID 1001002 và giảm lượng yêu cầu tải tới backend từ 80 xuống 72 (10%). KB5 ghi nhận web1 chuyển DOWN sau khoảng 3 giây, được đưa trở lại UP sau khoảng 4 giây, trong khi web2 phục vụ 4/4 yêu cầu thử. Báo cáo phân biệt kết quả đã quan sát với tiêu chí kiểm chứng và không suy rộng kết quả lab ra Internet.",
    42: "Ảnh chụp được gắn với mã lần chạy và nội dung cần chứng minh. Bên dưới mỗi ảnh có phần giải thích, nhận xét và đánh giá. Số liệu trong báo cáo được lấy từ JTL, log backend và sự kiện Suricata của đúng mã lần chạy; ảnh, JTL và log gốc được lưu trong thư mục ddos-lab2 của nhóm.",
    74: "HAProxy tổ chức điểm lắng nghe phía khách và nhóm server phía sau, phù hợp với việc đưa một dịch vụ web ra một địa chỉ truy cập chung [7]. Trong mô hình này, tường lửa của web server không được sử dụng làm cơ chế phát hiện DDoS. Nếu hệ điều hành cần quy tắc cho phép TCP/8080 từ pfSense, đó là điều kiện kết nối tới dịch vụ, không phải kết quả phòng chống của Suricata.",
    97: "Ba cách mô tả trên không hoàn toàn loại trừ nhau: “cùng pfSense” nói về nơi triển khai, còn “trước HAProxy” nói về vị trí kiểm tra. Đề tài kết hợp hai đặc điểm này. Cấu hình cần bảo đảm yêu cầu tới cổng 8080 không bị một NAT Port Forward cũ chuyển thẳng đến backend. Port forward có thể thay đổi đích trước khi dịch vụ cục bộ của firewall xử lý [10].",
    105: "Môi trường gồm năm máy ảo: hai Kali, một pfSense và hai web server Ubuntu 24.04. Các VM được nối qua hai Internal Network độc lập. Chỉ pfSense có giao diện ở cả hai mạng. Trong giai đoạn đo, lưu lượng được giới hạn trong lab; các card NAT phục vụ tải phần mềm được ngắt hoặc tắt trước khi chạy kịch bản.",
    113: "Nhận xét và đánh giá: Cách tách hai mạng giúp kiểm soát đường đi và giảm khả năng gửi nhầm trực tiếp đến backend. Sơ đồ thể hiện một dịch vụ có hai backend, không phải hai cuộc thử nghiệm độc lập mỗi Kali chỉ hướng đến một server. Mô hình phù hợp để quan sát cơ chế, song vẫn phụ thuộc tài nguyên của pfSense và máy thật.",
    117: "Trong mô hình này, tên WAN chỉ giao diện phía Kali, không đồng nghĩa với một địa chỉ Internet công cộng. Hai máy cùng mạng phải dùng IP riêng; sao chép VM mà giữ nguyên địa chỉ sẽ gây xung đột. Ký hiệu /24 tương ứng subnet mask 255.255.255.0. Địa chỉ loopback 127.0.0.1 luôn chỉ chính máy đang sử dụng nó, vì vậy Kali không thể dùng loopback của mình để mở server trên máy web.",
    120: "Một yêu cầu từ Kali có địa chỉ nguồn .10 hoặc .11, đích 10.10.10.1:8080. Suricata tại WAN quan sát nguồn thật này và kiểm tra điều kiện HTTP. Nếu yêu cầu không bị chặn, HAProxy tiếp nhận và chọn web1 hoặc web2. Kết nối từ HAProxy tới Python server đi qua phía LAN, do đó log ứng dụng thường ghi 10.10.20.1 làm địa chỉ khách.",
    121: "Các yêu cầu /health.txt phát sinh từ HAProxy tới backend phục vụ giám sát trạng thái. Chúng không chứng minh Kali đã gửi được yêu cầu và không được tính vào tổng mẫu JMeter. Để đối chiếu một lần chạy, URI cần có nhãn như run=KB3_R2&src=K1; khi đó log ứng dụng vẫn phân biệt được nguồn thử nghiệm dù địa chỉ TCP tại backend là pfSense.",
    132: "Giữa hai trạng thái so sánh, giữ nguyên số backend, trọng số, nội dung file, timeout, số luồng, số vòng lặp, timer và tài nguyên VM. KB3 và KB4 được chạy lặp hai lần; lần R2 có đủ JTL, log và ảnh Stats nên được dùng làm kết quả chính, R1 dùng để đối chiếu độ ổn định.",
    134: "Đồng hồ giữa các VM có sai lệch: trong các lần chạy, pfSense chậm hơn Kali khoảng 2–4 phút. Báo cáo dùng giờ UTC trong JTL để xác định khoảng chồng lấn và dùng giờ pfSense để mô tả sự kiện Suricata, sau khi đã ghi nhận độ lệch. Các kết quả thu trong thời gian Kali bị treo, host thiếu RAM hoặc pfSense khởi động lại được đánh dấu riêng và không trộn vào lần đo ổn định.",
    137: "Hai máy Kali được sử dụng làm nguồn tạo lưu lượng. Khi tạo Kali 2 từ bản clone của Kali 1, chọn tạo lại địa chỉ MAC cho card mạng và đổi IPv4 sang 10.10.10.11 trước khi đưa vào cùng mạng. Hai web server Ubuntu cũng phải có MAC và IP riêng. Việc clone giúp giữ phần mềm tương đương, nhưng không thay thế việc kiểm tra cấu hình trên từng bản sao.",
    145: "Tắt hoàn toàn VM trước khi thay đổi card mạng. Trong Settings → Network, đặt card của hai Kali vào Internal Network tên ATTACKER-LAN. Đặt card của hai web server vào SERVER-LAN. Với pfSense, card WAN nối ATTACKER-LAN và card LAN nối SERVER-LAN. Bật Enable Network Adapter và Cable Connected ở các card sử dụng. Hai tên mạng phải trùng chính xác giữa những VM cần nối cùng nhau.",
    151: "Tại pfSense console, gán WAN và LAN theo MAC rồi đặt IP tĩnh. WAN dùng 10.10.10.1/24, LAN dùng 10.10.20.1/24. Trong lab này không đặt upstream gateway cho WAN. Từ web server ở SERVER-LAN, mở https://10.10.20.1 để quản trị. Dùng IP tĩnh ở các máy đầu cuối giúp cấu hình không phụ thuộc DHCP.",
    152: "Trên Kali, sử dụng Network Manager để chọn IPv4 Manual; điền IP .10 hoặc .11, prefix 24 và gateway 10.10.10.1. Trên web server Ubuntu, cấu hình IPv4 tĩnh bằng netplan với địa chỉ .20 hoặc .21, prefix 24 và gateway 10.10.20.1. Sau khi áp dụng, xác nhận bằng các lệnh sau trên đúng hệ điều hành.",
    157: "# Trên từng web server Ubuntu",
    158: "ip -br addr; ip route",
    162: "Hình 4.3. Địa chỉ IP của hai Kali và hai web server",
    163: "Giải thích: Hình xác nhận hai nguồn .10 và .11, hai backend .20 và .21 thuộc đúng mạng. Nhận xét: Hai web server chạy Ubuntu 24.04 với địa chỉ tĩnh, không dùng DHCP nên không xuất hiện địa chỉ 169.254.x.x. Đánh giá: Hai IP nguồn độc lập là điều kiện cần của mô phỏng phân tán, nhưng chưa chứng minh hai nguồn đã gửi đồng thời.",
    165: "Từ từng web server, mở Web GUI pfSense tại LAN. Sau khi triển khai HTTP server, dùng Diagnostics → Test Port trên pfSense để kiểm tra 10.10.20.20:8080 và 10.10.20.21:8080. Từ Kali, dùng HTTP qua frontend sau khi HAProxy đã được cấu hình. Không dùng riêng kết quả ping thất bại để kết luận mạng sai, vì ICMP có thể chưa được firewall cho phép.",
    166: "4.3. Triển khai dịch vụ trên hai web server Ubuntu",
    167: "Hai web server chạy Ubuntu 24.04.5 LTS với Python 3.12.3. Mỗi máy được cloud-init tạo sẵn thư mục /opt/www và dịch vụ systemd att-web.service. Web 1 phục vụ nội dung nhận diện SERVER 1, Web 2 là SERVER 2; hai máy cung cấp cùng bốn tệp kiểm tra.",
    168: "sudo mkdir -p /opt/www",
    169: "printf 'WEB SERVER 1\\n' | sudo tee /opt/www/index.html",
    170: "printf 'OK SERVER 1\\n' | sudo tee /opt/www/health.txt",
    171: "printf 'IPS TEST - SERVER 1\\n' | sudo tee /opt/www/ips-test.txt",
    172: "printf 'LOAD TEST - SERVER 1\\n' | sudo tee /opt/www/load-test.txt",
    173: "ExecStart=/usr/bin/python3 -m http.server 8080",
    175: "Trên Web 2, thay các nhãn SERVER 1 bằng SERVER 2. Dịch vụ chạy với WorkingDirectory=/opt/www, lắng nghe cổng 8080 trên mọi địa chỉ và được systemd tự khởi động lại khi gặp lỗi. Log được đọc từ journal của att-web.service nên vẫn thu được các dòng GET sau khi dịch vụ khởi động lại.",
    176: "Kiểm tra cục bộ trên mỗi web server bằng http://127.0.0.1:8080/health.txt, sau đó kiểm tra từ pfSense. Nếu cục bộ hoạt động nhưng pfSense không kết nối được, kiểm tra IP, card mạng và luật cho phép TCP/8080 từ 10.10.20.1. Không tắt toàn bộ tường lửa chỉ để thay thế việc xác định nguyên nhân kết nối. Python HTTP Server phù hợp cho lab phục vụ file đơn giản và không được thiết kế như máy chủ triển khai sản xuất [12].",
    182: "Nếu đã có Port Forward từ WAN:8080 tới một web server, vào Firewall → NAT → Port Forward, mở luật tương ứng, bật Disable rồi lưu và áp dụng. Kiểm tra cả firewall rule liên quan do NAT tạo ra. Port forward cũ có thể làm yêu cầu đi tới một backend thay vì frontend HAProxy [10]. Giữ nguyên các luật LAN đang phục vụ quản trị.",
    185: "Hình 4.5. Alias KALI_LAB và luật WAN cho frontend",
    195: "Tạo frontend tên web_front, địa chỉ lắng nghe WAN address 10.10.10.1, cổng 8080, loại HTTP. Chọn web_pool làm backend mặc định. Lưu, Apply và xác nhận dịch vụ HAProxy chạy không báo lỗi. Không cấu hình chuyển hướng tới backend bằng NAT để thay cho bước gán backend này.",
    199: "Giải thích: Frontend xác định đích duy nhất của cả hai Kali. Nhận xét: Gửi JMeter thẳng tới IP backend sẽ bỏ qua mục tiêu kiểm chứng HAProxy của báo cáo. Đánh giá: Cấu hình khớp với kiến trúc khi đích nguồn là WAN:8080 và backend pool chứa hai web server.",
    219: 'drop http $EXTERNAL_NET any -> $HOME_NET any (msg:"LAB BLOCK GET /ips-test.txt from external"; flow:to_server,established; content:"/ips-test.txt"; http_uri; nocase; classtype:policy-violation; sid:1001001; rev:1;)',
    220: 'alert http $EXTERNAL_NET any -> $HOME_NET any (msg:"LAB ALERT /load-test.txt high rate"; flow:to_server,established; content:"/load-test.txt"; http_uri; nocase; classtype:policy-violation; sid:1001002; rev:1;)',
    222: "Các luật dùng $EXTERNAL_NET và $HOME_NET; phạm vi hai nguồn Kali được giới hạn bằng alias KALI_LAB trong luật firewall WAN. Luật thứ nhất chặn đường dẫn kiểm tra; luật thứ hai chỉ ghi nhận trước khi có chính sách chuyển hành động. Hai SID này không trùng với luật khác trong cấu hình của nhóm.",
    240: "Trên cả hai Kali, tạo Test Plan với một Thread Group và một HTTP Request. Đích là IP frontend, không phải địa chỉ của một backend. Tạo User Defined Variables gồm RUN_ID và SRC; đặt SRC là K1 hoặc K2. Ở HTTP Request, dùng Parameters để thêm run=${RUN_ID} và src=${SRC}. Cách đặt mã giúp tìm đúng lần chạy trong log ứng dụng. Cả hai máy chờ cùng mốc thời gian T0 trước khi gửi lô đầu tiên để bảo đảm khoảng chồng lấn thực tế.",
    243: "Các tham số ở Bảng 4.1 là cấu hình thực tế dùng cho KB1 và KB3/KB4; mọi lần chạy giữ nguyên giá trị, chỉ thay RUN_ID và SRC. Không bật vòng lặp vô hạn; khi phải dừng vì tài nguyên, ghi số mẫu thực sự hoàn thành.",
    248: "TZ=UTC jmeter -n -t lab-http.jmx -Jrun=KB3_R2 -Jsrc=K1 -Jthreads=2 -Jloops=20 -Jtimer=100 -l KB3_R2_K1.jtl -j KB3_R2_K1.log",
    261: "Các phần sau trình bày kết quả đã đo của từng kịch bản, đối chiếu giữa JTL, log backend và sự kiện Suricata; mọi số liệu đều gắn với mã lần chạy tương ứng.",
    277: "Kết quả cho lần chạy: Kali 1 hoàn thành 5 mẫu, lỗi 0; Kali 2 hoàn thành 5 mẫu, lỗi 0. Hai backend ghi 5 yêu cầu /load-test.txt đúng mã mỗi server, tương ứng 10 yêu cầu tải; ngoài ra mỗi server có một yêu cầu trang gốc. Trạng thái kiểm chứng của KB1: ĐẠT.",
    288: "Giải thích: Nội dung IPS TEST - SERVER 1 xác nhận file tồn tại và server trả về khi instance WAN đã dừng. Nhận xét: Cả hai Kali đều nhận HTTP 200 với nội dung SERVER tương ứng; log backend có đúng dòng IPS_OFF. Đánh giá: Đây là đối chứng “dịch vụ truy cập được” trước khi bật IPS.",
    295: "Giải thích: curl báo timeout sau khoảng 6 giây và nhận 0 byte. Nhận xét: Bắt tay TCP đã thành công trước khi yêu cầu HTTP bị ảnh hưởng là điều có thể xảy ra khi luật kiểm tra URI. Đánh giá: Timeout riêng lẻ chưa chứng minh Suricata là nguyên nhân; phải ghép với sự kiện chặn cùng nguồn và đích.",
    298: "Giải thích: Ảnh Alerts ghi nhận các dòng 1:1001001 với mô tả LAB IPS block test URI cho cả nguồn 10.10.10.10 và 10.10.10.11, đích 10.10.10.1:8080. Nhận xét: Kết quả này phù hợp với timeout tại cả hai Kali trong phép kiểm tra URI. Đánh giá: Có cơ sở xác nhận Suricata đã thực thi chặn đối với cả hai nguồn ở phép thử đó.",
    303: "Minh chứng hiện có xác nhận chức năng chặn URI trên đường vào HAProxy đối với cả hai nguồn. Khi IPS tắt, Kali 1 và Kali 2 đều nhận HTTP 200 với nội dung IPS TEST - SERVER 1 và SERVER 2. Khi IPS bật, cả hai đều timeout sau khoảng 6 giây, nhận 0 byte; Suricata ghi 6 sự kiện chặn SID 1001001 cho .10 và .11. Trang bình thường sau phép thử trả HTTP 200. Không dùng số lần xuất hiện SID 1001001 để đánh giá hiệu quả chính sách rate_filter của SID 1001002.",
    307: "Hai backend phải UP và cùng trọng số. Mỗi Kali sử dụng bộ tham số tải đối chứng ở Bảng 4.1. KB3 được chạy hai lần với mã KB3_R1 và KB3_R2; kết quả định lượng trong báo cáo lấy từ KB3_R2 vì lần này có đủ JTL, log và ảnh Stats trước/sau. Bộ tham số được lựa chọn để kiểm chứng ngưỡng nhỏ, không nhằm khẳng định đã làm cạn năng lực máy chủ.",
    309: "Bước 1: Ghi ảnh Stats ban đầu, xác nhận không còn tải cũ và mở log backend. Bước 2: Lưu kết quả JMeter cũ, Clear All phần hiển thị và dùng tệp JTL mới. Bước 3: Khởi chạy kế hoạch trên K1 và K2 gần cùng thời điểm; ghi thời gian bắt đầu và kết thúc từ dữ liệu gốc. Bước 4: Khi hai nguồn kết thúc, chụp kết quả, Stats và log hai server. Bước 5: Lọc đúng mã KB3_R2, đếm số yêu cầu ở từng backend và kiểm tra khoảng chạy đồng thời.",
    315: "Giải thích: JTL của KB3_R2 ghi 40 mẫu ở mỗi Kali, tổng 80 mẫu, 0 lỗi; thời gian trung bình 41,0 ms và 39,3 ms. Nhận xét: Mỗi tệp JTL chỉ đại diện một nguồn; tổng 80 mẫu được xác nhận bằng hai tệp. Đánh giá: Với 0 lỗi và thời gian ổn định, dịch vụ đáp ứng được mức tải đã thử; chưa chứng minh hệ thống chịu được tải lớn hơn.",
    318: "Giải thích: Log của cả hai backend đều có GET /load-test.txt với mã 200, gắn run=KB3_R2 và nhãn src=K1/K2. Nhận xét: Số dòng tải là 40 ở mỗi backend, cộng hai dòng kiểm tra; điều này chứng minh cả hai backend tham gia phục vụ. Đánh giá: Kết hợp JTL 40 mẫu mỗi nguồn cho thấy HAProxy phân phối cân bằng trong lần chạy.",
    321: "Giải thích: Ảnh Stats trước và sau KB3_R2 cho thấy hai server UP, LastChk L7OK/200; Sessions Total tăng từ 1 lên 40 ở cả web1 và web2. Nhận xét: Mức tăng bằng nhau hỗ trợ nhận định HAProxy phân phối đều 40 yêu cầu của mỗi nguồn cho hai backend. Đánh giá: Sessions Total là bộ đếm phiên, không đồng nhất với số HTTP Request; kết luận định lượng dùng log lọc theo mã lần chạy.",
    325: "Mức phân phối của lần chạy được tính từ log đã lọc: web1 50%, web2 50% (42/42 dòng, gồm 40 yêu cầu tải và 2 yêu cầu kiểm tra mỗi server). Nếu cả hai cùng nhận yêu cầu và phản hồi hợp lệ, chức năng phân phối tải đã được kiểm chứng. Muốn kết luận hai backend làm tăng năng lực so với một backend, cần thêm phép đối chứng một server và hai server dưới cùng điều kiện; bộ số liệu hiện tại không tự cung cấp so sánh đó.",
    328: "Mục tiêu là kiểm tra SID 1001002 có chuyển sang hành động chặn theo chính sách hay không và xác định ảnh hưởng tới lượng yêu cầu đến backend. Giữ cấu hình như KB3, bật rate_filter tại WAN và dùng mã mới KB4_R2. Không thay đổi số luồng hoặc giảm số backend đồng thời với bật chính sách, vì sẽ không tách được nguyên nhân của thay đổi kết quả.",
    330: "Bước 1: Xác nhận chính sách đã nạp, hai backend UP và các trạng thái cũ đã hết ảnh hưởng. Bước 2: Ghi Stats ban đầu, dùng JTL mới và khởi chạy cùng cấu hình trên hai Kali. Bước 3: Quan sát cảnh báo theo từng nguồn; chụp sự kiện có SID 1001002 và hành động thực tế. Bước 4: Chạy một yêu cầu đối chứng nhẹ tới / bằng kết nối mới, ghi thời điểm và phản hồi. Bước 5: Lưu dữ liệu cuối, lọc log backend theo KB4_R2 và so sánh với KB3_R2 có điều kiện đầu vào tương đương.",
    343: "Gọi B0 và B1 là tổng yêu cầu tải tới hai backend trong KB3 và KB4. Với cùng 80 mẫu đầu vào thực tế, B0 = 80 và B1 = 72, tỷ lệ giảm lượng yêu cầu tới backend là (80 − 72)/80 × 100% = 10,0%. Giá trị này chỉ mô tả mức giảm trong điều kiện lab; không dùng riêng chênh lệch B0 − B1 như hiệu quả chặn tuyệt đối.",
    344: "Khi dữ liệu cho thấy cả hai nguồn có DROP đúng SID, lượng yêu cầu tới backend giảm và yêu cầu đối chứng vẫn thành công, có thể kết luận chính sách đã thực hiện giảm lưu lượng khớp luật trong điều kiện thử nghiệm. Nếu chỉ có lỗi client mà không có action chặn hoặc backend vốn đã DOWN, chưa đủ căn cứ đưa ra kết luận đó. Trạng thái thực nghiệm KB4 của nhóm: ĐÃ KIỂM CHỨNG; cả hai nguồn đều có sự kiện DROP SID 1001002, lượng yêu cầu tải tới backend giảm 10%, yêu cầu đối chứng trả HTTP 200.",
    362: "Bảng 5.4 ghi các mốc thời gian quan sát thực tế, không dùng thời gian lý thuyết interval × fall hoặc interval × rise. Độ trễ phát hiện phụ thuộc thời điểm phép kiểm tra, timeout và lập lịch của môi trường ảo; giá trị ghi nhận là khoảng 3 giây cho DOWN và khoảng 4 giây cho UP.",
    366: "Các bộ đếm Sessions Total được dùng đúng ý nghĩa là số phiên tích lũy. Với KB3_R2, bộ đếm tăng từ 1 lên 40 ở mỗi server; với KB4_R2, tăng từ 0 lên 36. Số yêu cầu tải thực tế tới backend được xác định từ log có mã lần chạy, không lấy trực tiếp từ chênh lệch bộ đếm.",
    378: "Đề tài xây dựng phương án mô phỏng DDoS HTTP theo kiến trúc hai nguồn Kali/JMeter cùng hướng tới một frontend pfSense, phía sau là hai web server Ubuntu. Suricata Inline IPS kiểm tra lưu lượng tại WAN, còn HAProxy lựa chọn backend cho các yêu cầu được tiếp nhận. Thiết kế này cho phép nghiên cứu việc phát hiện, ngăn chặn và phân phối tải trong cùng một luồng xử lý có thể quan sát.",
    379: "Các kết quả đã ghi nhận gồm khả năng trả nội dung qua frontend, hành động chặn của SID 1001001 đối với URI kiểm tra ở cả hai nguồn và việc cả hai backend nhận yêu cầu HTTP. Sự kết hợp giữa timeout tại Kali, sự kiện chặn tại Suricata và log backend là phương pháp đối chiếu phù hợp hơn việc chỉ nhìn một màn hình lỗi. Tương tự, hai backend UP và có log xử lý hỗ trợ kết luận HAProxy đã phân phối hoạt động, nhưng không tự chứng minh mức tăng hiệu năng.",
    380: "Kết quả định lượng của KB3_R2 và KB4_R2 được ghi tại Bảng 5.2 và Bảng 5.3; kết quả KB5 tại Bảng 5.4. Tỷ lệ giảm yêu cầu tải tới backend là 10%, P95 của các mẫu thành công trong KB4 là 50 ms và 40 ms, thời gian phát hiện backend DOWN khoảng 3 giây và khôi phục khoảng 4 giây. Các giá trị này chỉ đúng trong môi trường, cấu hình và mức tải đã thử.",
    383: "Hướng phát triển gần nhất là lặp lại KB3 và KB4 thêm hai lần (R3) để đánh giá độ dao động, bổ sung nguồn truy cập hợp lệ độc lập để đánh giá mức duy trì dịch vụ và khả năng chặn nhầm, đặc biệt khi truy cập cùng URI đang được theo dõi.",
    387: "Các tài liệu trực tuyến dưới đây được truy cập ngày 09/11/2026. Tài liệu tham chiếu dùng Suricata 7.0.11 và HAProxy 3.2 để đối chiếu cơ chế; phần mềm thực cài của nhóm là Suricata 7.0.8 và HAProxy 2.8.3, ghi tại Bảng 3.1.",
    405: "Hồ sơ cấu hình gồm phiên bản VirtualBox, phiên bản từng hệ điều hành, Java/JMeter trên hai Kali, Python trên hai web server Ubuntu, pfSense, Suricata và HAProxy. Đối với pfSense, lưu cấu hình bằng chức năng Backup của hệ thống; nếu chia sẻ tệp ra ngoài nhóm, xử lý thông tin đăng nhập và dữ liệu không cần thiết trước khi công bố.",
    421: "B.2. Trên web server Ubuntu",
    422: "ip -br addr",
    423: "python3 --version",
    424: "ss -ltnp | grep 8080",
    426: "Log được đọc từ journal của dịch vụ att-web.service. Dừng và khởi động lại dịch vụ bằng systemctl; không mở hai tiến trình trên cùng cổng. Ví dụ ở Web 1 cho KB3_R2:",
    427: "sudo mkdir -p /var/log/ddos-lab",
    428: "sudo journalctl -u att-web.service --since \"2026-11-09 11:29:00\" --until \"2026-11-09 11:31:00\" --no-pager > /var/log/ddos-lab/KB3_R2_web1.log",
    431: "Ví dụ đếm các dòng GET của đúng mã lần chạy trong shell, với đường dẫn log điều chỉnh theo tệp đã lưu:",
    432: "grep 'GET /load-test.txt' /var/log/ddos-lab/KB3_R2_web1.log | \\",
    433: "  grep -E 'run=KB3_R2(&| )' > /tmp/kb3_r2_web1_rows.txt",
    434: "wc -l < /tmp/kb3_r2_web1_rows.txt",
    435: "cat /tmp/kb3_r2_web1_rows.txt",
    469: "Bảng E.1 tổng hợp các lần chạy định lượng. KB3 và KB4 đều có hai lần R1, R2; R2 là lần có đủ JTL, log và ảnh nên được dùng làm kết quả chính. Các ô R3 ghi “chưa chạy” vì giới hạn thời gian của bài thực hành, không thay bằng số liệu suy đoán.",
    470: "Báo cáo không vẽ thêm biểu đồ để tránh biểu diễn sai dữ liệu gốc. Bảng E.1 và các bảng 5.2–5.4 đã tách rõ tổng mẫu, số lỗi, phân bố backend và số sự kiện DROP; nếu cần biểu đồ, dùng hai nhóm cột KB3/KB4 với trục tung ghi “yêu cầu đã được ứng dụng ghi nhận”.",
}

RUN_REPL = {
    9: (1, "........................................"),
    10: (1, "Nhóm 01"),
    11: (1, "D24CQCE01-B"),
    12: (1, "Học kỳ 1, năm học 2026–2027"),
    14: (0, "Hà Nội, tháng 11 năm 2026"),
}

# --------------------------------------------------------------- table values
T0_ROW = ["Phạm Việt Toàn", "B24DCCE269",
          "Xây dựng lab VirtualBox gồm 2 Kali, pfSense và 2 web Ubuntu; cài đặt, cấu hình Suricata Inline IPS, HAProxy, firewall/NAT; viết kịch bản JMeter; chạy KB1–KB5; thu thập minh chứng; biên soạn báo cáo.",
          "Hoàn thành 100%; báo cáo, script, ảnh minh chứng, JTL và log được lưu trong thư mục ddos-lab2."]

T4 = {
    1: ("Core i7-1185G7 4 nhân/8 luồng; 15,7 GB RAM; ổ C: còn trống 21,5 GB",
        "Windows 11 Pro 10.0.26200; VirtualBox 7.2.14"),
    2: ("2 vCPU; 2048 MB", "Kali GNU/Linux Rolling; Java 25.0.3; JMeter 5.6.3"),
    3: ("2 vCPU; 2048 MB", "Kali GNU/Linux Rolling; Java 25.0.3; JMeter 5.6.3"),
    4: ("2 vCPU; 1536 MB", "pfSense 2.7.2-RELEASE; Suricata 7.0.8; HAProxy 2.8.3"),
    5: ("1 vCPU; 768 MB", "Ubuntu 24.04.5 LTS; Python 3.12.3; systemd att-web.service"),
    6: ("1 vCPU; 768 MB", "Ubuntu 24.04.5 LTS; Python 3.12.3; systemd att-web.service"),
}

T8 = [
    "Kali 1: 10.10.10.10/24; Kali 2: 10.10.10.11/24; không trùng địa chỉ.",
    "web1 và web2 trả /health.txt với HTTP 200 khi kiểm tra từ pfSense.",
    "Cả hai server UP, LastChk L7OK/200 trên HAProxy Stats.",
    "curl tới 10.10.10.1:8080 trả 200; log backend có run=KB1_R1 và src=K1/K2.",
    "Suricata WAN chạy Inline IPS trên netmap; instance hoạt động sau khi nạp.",
    "SID 1001001 và 1001002 nạp không lỗi, không xung đột SID.",
    "Alias KALI_LAB chứa 10.10.10.10 và 10.10.10.11; luật WAN dùng nguồn KALI_LAB.",
    "CPU/RAM ổn định; pfSense chậm hơn Kali khoảng 2–4 phút, đã chuẩn hóa UTC khi đối chiếu.",
]

T10 = {
    1: ("40", "40", "80 (giữ Bảng 4.1)"),
    2: ("40", "40", "N1 + N2 = 80"),
    3: ("0", "0", "E1 + E2 = 0"),
    4: ("11:30:25,231 – 11:30:28,043", "11:30:23,895 – 11:30:26,945", "Chồng lấn 1,714 giây"),
    5: ("TB 41,0 ms; P95 44 ms", "TB 39,3 ms; P95 47 ms", "Tính từ 80 mẫu gốc; P95 44/47 ms"),
    6: ("Không tách bằng IP TCP backend", "Lọc bằng src trong URI", "42 / 42 (40 yêu cầu tải và 2 yêu cầu kiểm tra mỗi server)"),
}

T11 = {
    1: ("80", "80", "Cùng cấu hình 2 luồng × 20 vòng mỗi nguồn"),
    2: ("80 thành công / 0 lỗi", "72 thành công / 8 lỗi", "KB4 có 4 timeout mỗi nguồn"),
    3: ("44 ms (K1) / 47 ms (K2)", "50 ms (K1) / 40 ms (K2)", "Chỉ tính mẫu thành công"),
    4: ("≈ 4,2 giây", "≈ 13,4 giây", "KB4 chậm do mỗi nguồn chờ 4 timeout 5 giây"),
    5: ("42", "37", "Log đúng run và URI; gồm yêu cầu kiểm tra"),
    6: ("42", "37", "Đã loại health check khỏi số liệu tải"),
    7: ("0", "2 / 4", "SID 1001002, action blocked"),
    8: ("HTTP 200", "HTTP 200", "Yêu cầu / sau mỗi lần chạy"),
}

T12 = [
    "11:11:30Z",
    "11:11:33Z",
    "≈ 3 giây",
    "4 thành công / 0 lỗi",
    "HTTP 200; nội dung SERVER 2 (4/4)",
    "11:11:54Z / 11:11:58Z",
    "CÓ; KB5_AFTER lúc 11:12:10–11:12:13Z",
]

T13 = {
    1: ("Timeout 6 giây, 0 byte; 6 sự kiện SID 1001001 action blocked cho .10 và .11",
        "Đã kiểm chứng cho cả hai nguồn"),
    2: ("Log /load-test.txt: web1 42, web2 42; Stats UP, Sessions 1→40 ở cả hai",
        "Đã kiểm chứng hai backend cùng tham gia"),
    3: ("JTL K1/K2 cùng run; chồng lấn 1,714 giây", "Đã kiểm chứng hai nguồn chạy đồng thời"),
    4: ("6 sự kiện DROP SID 1001002 (K1 2, K2 4)", "Đã kiểm chứng cả hai nguồn"),
    5: ("B0 = 80, B1 = 72; giảm 10%", "Đã định lượng trong điều kiện lab"),
    6: ("Chuỗi UP → DOWN → UP; 4/4 yêu cầu SERVER 2; log KB5_AFTER",
        "Đã kiểm chứng failover và phục hồi"),
}

T14 = [
    "KB4_R2",
    "Phạm Việt Toàn; 2026-11-09, 11:31:28–11:35:41 UTC (chạy tải 11:33:58–11:35:00)",
    "2 luồng × 20 vòng; ramp-up 1 giây; timer 100 ms; timeout 3000/5000 ms",
    "WAN Inline IPS; SID 1001002; rate_filter count 20/10 giây, drop 15 giây",
    "web1, web2 UP; LastChk L7OK/200; Sessions 0 trước chạy",
    "KB4_R2_K1.jtl; KB4_R2_K2.jtl",
    "backend_web1.txt; backend_web2.txt; eve_1001002.txt; alerts_1001002.txt",
    "pfSense chậm hơn Kali khoảng 4 phút; 4 timeout mỗi nguồn; không dừng sớm",
    "6 sự kiện DROP; backend nhận 72 yêu cầu tải, giảm 10%; Hình 5.11–5.13",
]

T16 = {
    1: ("80", "0", "42 / 40", "0"),
    2: ("80", "0", "42 / 42", "0"),
    3: ("—", "—", "—", "Chưa chạy"),
    4: ("80", "8", "40 / 38", "4 (2 / 2)"),
    5: ("80", "8", "37 / 37", "6 (2 / 4)"),
    6: ("—", "—", "—", "Chưa chạy"),
}

# --------------------------------------------------------------------- images
IMAGES = {
    110: "ev3_1_topology.png",
    140: "ev4_vms.png",
    147: "ev4_nics.png",
    161: "ev4_ips.png",
    177: "ev4_http.png",
    184: "ev4_rules.png",
    191: "ev4_pool.png",
    197: "ev_hap_listen.png",
    203: "ev_hap_stats.png",
    210: "ev_sur_wan_ips.png",
    223: "ev4_customrules.png",
    232: "ev4_threshold.png",
    250: "ev4_jmeter.png",
    270: "ev5_1_curl.png",
    273: "ev5_2_kb1.png",
    286: "ev5_3_off.png",
    293: "ev5_4_on.png",
    296: "ev5_5_alerts.png",
    299: "ev5_6_backend.png",
    310: "ev5_7_load.png",
    313: "ev5_8_kb3jmeter.png",
    316: "ev5_9_kb3backend.png",
    319: "ev5_10_stats.png",
    331: "ev5_11_kb4jmeter.png",
    334: "ev5_12_kb4drops.png",
    337: "ev5_13_kb4backend.png",
    350: "ev5_14_kb5up.png",
    353: "ev5_15_kb5down.png",
    356: "ev5_16_log.png",
}


def set_run(p, idx, text):
    p.runs[idx].text = text


def replace_para(p, text):
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)


def set_cell(cell, text):
    p = cell.paragraphs[0]
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)


def put_image(anchor, filename, width_cm=15.5):
    path = os.path.join(EVID, filename)
    p = anchor.insert_paragraph_before()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    anchor._element.getparent().remove(anchor._element)


def add_page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(0)
    run = paragraph.add_run()
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)


def norm(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s)).lower()


def make_entry(doc, text, page, indent_cm=0.0, bold=False):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(indent_cm)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.tab_stops.add_tab_stop(Cm(16.45), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r = p.add_run(f"{text}\t{page}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.bold = bold
    el = p._element
    el.getparent().remove(el)
    return el


def find_toc_sdts(doc):
    found = []
    for child in doc.element.body.iterchildren():
        if child.tag != qn("w:sdt"):
            continue
        instr = "".join(n.text or "" for n in child.iter(qn("w:instrText")))
        if "TOC" in instr:
            found.append(child)
    return found


def fill_toc(doc, sdt, entries):
    content = sdt.find(qn("w:sdtContent"))
    for ch in list(content):
        content.remove(ch)
    for text, page, indent, bold in entries:
        content.append(make_entry(doc, text, page, indent, bold))


def build(page_map=None):
    doc = docx.Document(SRC)
    paras = list(doc.paragraphs)

    for i, (run_idx, text) in RUN_REPL.items():
        set_run(paras[i], run_idx, text)
    for i, text in REPL.items():
        replace_para(paras[i], text)

    for i in (2, 9, 10, 11, 12):
        for r in paras[i].runs:
            r.font.color.rgb = RGBColor(0, 0, 0)

    doc.core_properties.author = "Phạm Việt Toàn"
    doc.core_properties.title = "Mô phỏng tấn công DDoS tầng ứng dụng và triển khai giải pháp phát hiện, giảm thiểu bằng Suricata IPS kết hợp HAProxy trên pfSense"
    doc.core_properties.subject = "Bài tập lớn Cơ sở an toàn thông tin"
    doc.core_properties.keywords = "DDoS, Suricata, HAProxy, pfSense, JMeter, Inline IPS"

    tables = doc.tables

    t0 = tables[0]
    set_cell(t0.rows[1].cells[0], T0_ROW[0])
    set_cell(t0.rows[1].cells[1], T0_ROW[1])
    set_cell(t0.rows[1].cells[2], T0_ROW[2])
    set_cell(t0.rows[1].cells[3], T0_ROW[3])
    for tr in list(t0.rows)[2:]:
        t0._tbl.remove(tr._tr)

    t4 = tables[4]
    for row, (cpu_ram, os_ver) in T4.items():
        set_cell(t4.rows[row].cells[1], cpu_ram)
        set_cell(t4.rows[row].cells[2], os_ver)

    t8 = tables[8]
    for idx, val in enumerate(T8, start=1):
        set_cell(t8.rows[idx].cells[2], val)

    t10 = tables[10]
    for row, vals in T10.items():
        for col, val in zip((1, 2, 3), vals):
            set_cell(t10.rows[row].cells[col], val)

    t11 = tables[11]
    for row, vals in T11.items():
        for col, val in zip((1, 2, 3), vals):
            set_cell(t11.rows[row].cells[col], val)

    t12 = tables[12]
    for idx, val in enumerate(T12, start=1):
        set_cell(t12.rows[idx].cells[1], val)

    t13 = tables[13]
    for row, (ev, concl) in T13.items():
        set_cell(t13.rows[row].cells[1], ev)
        set_cell(t13.rows[row].cells[2], concl)

    t14 = tables[14]
    for idx, val in enumerate(T14, start=1):
        set_cell(t14.rows[idx].cells[1], val)

    t16 = tables[16]
    for row, vals in T16.items():
        for col, val in zip((1, 2, 3, 4), vals):
            set_cell(t16.rows[row].cells[col], val)

    for idx, fname in IMAGES.items():
        put_image(paras[idx], fname)

    for p in paras[471:481]:
        p._element.getparent().remove(p._element)

    sec = doc.sections[0]
    sec.different_first_page_header_footer = True
    add_page_field(sec.footer.paragraphs[0])

    # collect headings and captions after all text edits
    heads = [(p.style.name, p.text.strip()) for p in doc.paragraphs
             if p.style.name in ("Heading 1", "Heading 2")]
    figs = [p.text.strip() for p in doc.paragraphs
            if re.match(r"^Hình \d+\.\d+\.", p.text.strip())]
    tabs = [p.text.strip() for p in doc.paragraphs
            if re.match(r"^Bảng \d+\.\d+\.", p.text.strip())]

    pm = page_map or {}
    sdts = find_toc_sdts(doc)
    if len(sdts) != 3:
        raise RuntimeError(f"expected 3 TOC fields, got {len(sdts)}")
    head_entries = [(t, pm.get(norm(t), "0"), 0.0 if s == "Heading 1" else 0.5,
                     s == "Heading 1") for s, t in heads]
    fill_toc(doc, sdts[0], head_entries)
    fill_toc(doc, sdts[1], [(c, pm.get(norm(c), "0"), 0.0, False) for c in figs])
    fill_toc(doc, sdts[2], [(c, pm.get(norm(c), "0"), 0.0, False) for c in tabs])

    doc.save(OUT_DOCX)
    return OUT_DOCX, [t for _, t in heads] + figs + tabs


def to_pdf():
    env = dict(os.environ)
    profile = r"C:\Users\Admin\AppData\Local\Temp\lo_profile_btl"
    cmd = [SOFFICE, "-env:UserInstallation=file:///" + profile.replace("\\", "/"),
           "--headless", "--convert-to", "pdf", "--outdir", OUT_DIR, OUT_DOCX]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
    if not os.path.exists(OUT_PDF):
        print(r.stdout)
        print(r.stderr)
        raise RuntimeError("PDF conversion failed")


def page_map_from_pdf(keys):
    import pymupdf
    doc = pymupdf.open(OUT_PDF)
    texts = [norm(p.get_text()) for p in doc]
    printed = {}
    for i, p in enumerate(doc):
        num = None
        for b in p.get_text("blocks"):
            t = b[4].strip()
            if t.isdigit() and len(t) <= 3 and b[1] > p.rect.height * 0.85:
                num = int(t)
        printed[i] = num
    result = {}
    for k in keys:
        nk = norm(k)
        hits = [i for i, txt in enumerate(texts) if nk and nk in txt]
        if not hits:
            short = nk[:45]
            hits = [i for i, txt in enumerate(texts) if short and short in txt]
        if hits:
            idx = hits[-1]
            result[nk] = printed.get(idx) or (idx + 1)
        else:
            result[nk] = "?"
    return result


def main():
    if not os.path.exists(SOFFICE):
        raise SystemExit("LibreOffice not found: " + SOFFICE)
    _, keys = build(None)
    to_pdf()
    pm1 = page_map_from_pdf(keys)
    _, keys2 = build(pm1)
    to_pdf()
    pm2 = page_map_from_pdf(keys2)
    if pm2 != pm1:
        diff = {k: (pm1.get(k), pm2.get(k)) for k in pm2 if pm1.get(k) != pm2.get(k)}
        print("page map changed, rebuilding once:", diff)
        build(pm2)
        to_pdf()
        pm3 = page_map_from_pdf(keys2)
        diff3 = {k: (pm2.get(k), pm3.get(k)) for k in pm3 if pm2.get(k) != pm3.get(k)}
        if diff3:
            print("WARNING still unstable:", diff3)
    missing = {k: v for k, v in pm2.items() if v == "?"}
    if missing:
        print("WARNING pages not found:", list(missing)[:10])
    print("DOCX:", OUT_DOCX)
    print("PDF :", OUT_PDF)
    print("TOC entries:", len(keys2), "pages:", len(__import__("pypdf").PdfReader(OUT_PDF).pages))


if __name__ == "__main__":
    main()
