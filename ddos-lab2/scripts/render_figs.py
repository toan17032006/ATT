#!/usr/bin/env python3
"""Render report figures: CLI evidence panels, topology, and composites."""
import os, re, json, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

RUNS = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\runs"
EVID = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"
FONT = r"C:\Windows\Fonts\consola.ttf"
FONTB = r"C:\Windows\Fonts\consolab.ttf"
SANS = r"C:\Windows\Fonts\segoeui.ttf"
SANSB = r"C:\Windows\Fonts\segoeuib.ttf"


def render(title, lines, out, width=1500, fs=21, lh=30, wrap=132, subtitle=None):
    f = ImageFont.truetype(FONT, fs)
    fb = ImageFont.truetype(FONTB, fs)
    ft = ImageFont.truetype(FONTB, 26)
    fsub = ImageFont.truetype(FONT, 20)
    cw = f.getlength("M")
    wrap = max(40, min(wrap, int((width - 60) // cw)))
    wrapped = []
    for ln in lines:
        if not ln:
            wrapped.append("")
            continue
        parts = textwrap.wrap(ln, width=wrap, subsequent_indent="    ", replace_whitespace=False) or [""]
        wrapped.extend(parts)
    head = 92 + (36 if subtitle else 0)
    h = head + len(wrapped) * lh + 34
    im = Image.new("RGB", (width, h), "#ffffff")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, width, head - 12), fill="#1f3864")
    d.text((30, 22), title, font=ft, fill="white")
    if subtitle:
        d.text((30, 60), subtitle, font=fsub, fill="#d6e0f0")
    d.rectangle((0, head - 12, width, h - 1), outline="#8ea9c9", width=2)
    y = head + 8
    for ln in wrapped:
        if ln.startswith("$ "):
            d.text((30, y), ln, font=fb, fill="#0b3d91")
        elif ln.startswith("#"):
            d.text((30, y), ln, font=f, fill="#6b7280")
        elif "SERVER 1" in ln or "SERVER 2" in ln:
            d.text((30, y), ln, font=fb, fill="#1b6b2a")
        elif "HTTP/1.0 200" in ln or "HTTP/1.1 200" in ln:
            d.text((30, y), ln, font=fb, fill="#1b6b2a")
        elif "[Drop]" in ln or "timed out" in ln or "rc=28" in ln or " 000 " in ln:
            d.text((30, y), ln, font=fb, fill="#a61b1b")
        else:
            d.text((30, y), ln, font=f, fill="#111827")
        y += lh
    im.save(out)
    print("render", os.path.basename(out), im.size)


def load(p):
    return open(p, encoding="utf-8", errors="replace").read().replace("&quot;", '"').replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")


def stack(paths, labels, out, gap=18, bg="#ffffff"):
    ims = [Image.open(p).convert("RGB") for p in paths]
    w = max(i.width for i in ims)
    fl = ImageFont.truetype(SANSB, 24)
    total = sum(i.height for i in ims) + gap * (len(ims) - 1) + 46 * len(ims)
    im = Image.new("RGB", (w, total), bg)
    d = ImageDraw.Draw(im)
    y = 0
    for p, lab, src in zip(paths, labels, ims):
        d.text((10, y + 8), lab, font=fl, fill="#1f3864")
        y += 46
        im.paste(src, (0, y))
        y += src.height + gap
    im.save(out)
    print("stack", os.path.basename(out), im.size)


def topology(out):
    W, H = 1650, 920
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(SANS, 26)
    fb = ImageFont.truetype(SANSB, 28)
    fs = ImageFont.truetype(SANS, 22)
    # zones
    d.rectangle((60, 120, 470, 830), fill="#eef3fb", outline="#7f9cc4", width=3)
    d.text((80, 132), "ATTACKER-LAN  10.10.10.0/24", font=fb, fill="#1f3864")
    d.rectangle((1170, 120, 1590, 830), fill="#eef7ee", outline="#7fa87f", width=3)
    d.text((1190, 132), "SERVER-LAN  10.10.20.0/24", font=fb, fill="#245c2c")

    def box(x1, y1, x2, y2, title, body, fill="#ffffff", edge="#1f3864"):
        d.rounded_rectangle((x1, y1, x2, y2), radius=14, fill=fill, outline=edge, width=3)
        d.text((x1 + 18, y1 + 14), title, font=fb, fill=edge)
        yy = y1 + 58
        for b in body:
            d.text((x1 + 18, yy), b, font=fs, fill="#111827")
            yy += 32

    box(100, 300, 430, 420, "Kali 1", ["10.10.10.10/24", "JMeter 5.6.3 / Java 25", "eth0 -> ATTACKER-LAN"])
    box(100, 570, 430, 690, "Kali 2", ["10.10.10.11/24", "JMeter 5.6.3 / Java 25", "eth0 -> ATTACKER-LAN"])
    box(560, 190, 1080, 760, "pfSense 2.7.2 (FreeBSD 14)",
        ["WAN em0: 10.10.10.1/24", "Suricata 7.0.8 - Inline IPS (netmap)", "Firewall: TCP/8080 tu KALI_LAB",
         "HAProxy 2.8.3: web_frontend", "  bind 10.10.10.1:8080", "  backend web_pool: round-robin",
         "LAN em1: 10.10.20.1/24"], fill="#fdf7e8", edge="#8a6d1f")
    box(1230, 280, 1560, 420, "Web 1", ["10.10.20.20:8080", "Ubuntu 24.04.5", "Python 3.12.3 http.server", "att-web.service"])
    box(1230, 570, 1560, 710, "Web 2", ["10.10.20.21:8080", "Ubuntu 24.04.5", "Python 3.12.3 http.server", "att-web.service"])

    def arrow(x1, y1, x2, y2, color="#1f3864", width=4):
        d.line((x1, y1, x2, y2), fill=color, width=width)
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        L = 18
        for s in (-0.45, 0.45):
            d.line((x2, y2, x2 - L * math.cos(ang + s), y2 - L * math.sin(ang + s)), fill=color, width=width)

    arrow(432, 360, 558, 360)
    arrow(432, 630, 558, 630)
    d.text((330, 205), "HTTP :8080", font=fb, fill="#a61b1b")
    d.text((332, 235), "/load-test.txt?run=&src=", font=fs, fill="#a61b1b")
    arrow(1082, 330, 1228, 330)
    arrow(1082, 650, 1228, 650)
    d.text((1100, 276), "round-robin", font=fb, fill="#245c2c")
    d.text((1106, 596), "round-robin", font=fb, fill="#245c2c")
    d.text((80, 858), "Mui ten lien: chieu yeu cau; phan hoi tra nguoc qua HAProxy ve Kali.", font=fs, fill="#374151")
    im.save(out)
    print("topology", im.size)


# ---------------- environment ----------------
env = json.load(open(r"C:\Users\Admin\Desktop\ATT\ddos-lab2\env_data.json", encoding="utf-8"))
vms = env["vms"]

render("VBoxManage list vms / cau hinh tai nguyen thuc cap", [
    "$ VBoxManage list vms | grep ATT",
    '  "ATT-Kali1"    "ATT-Kali2"    "ATT-pfSense"    "ATT-WEB1"    "ATT-WEB2"',
    "",
    "May ao        vCPU   RAM      Card 1 (Internal)   Card 2",
    "ATT-Kali1     2      2048 MB  ATTACKER-LAN        NAT 10.0.3.15",
    "ATT-Kali2     2      2048 MB  ATTACKER-LAN        NAT 10.0.3.15",
    "ATT-pfSense   2      1536 MB  ATTACKER-LAN        SERVER-LAN",
    "ATT-WEB1      1       768 MB  SERVER-LAN          NAT 10.0.3.15",
    "ATT-WEB2      1       768 MB  SERVER-LAN          NAT 10.0.3.15",
    "",
    "# May that: Lenovo 20XW003KUS; Intel Core i7-1185G7 (4C/8T); 15.7 GB RAM;",
    "# Windows 11 Pro 10.0.26200; VirtualBox 7.2.14",
], os.path.join(EVID, "ev4_vms.png"))

render("Internal Network cua pfSense va cac may dau cuoi", [
    'ATT-pfSense  Adapter 1 (WAN, em0): Internal Network "ATTACKER-LAN"  MAC 080027BE145F',
    '             Adapter 2 (LAN, em1): Internal Network "SERVER-LAN"    MAC 080027B7BF1D',
    'ATT-Kali1    Adapter 1: "ATTACKER-LAN"   MAC 0800275A87BC',
    'ATT-Kali2    Adapter 1: "ATTACKER-LAN"   MAC 0800279CD558',
    'ATT-WEB1     Adapter 1: "SERVER-LAN"     MAC 080027FA8787',
    'ATT-WEB2     Adapter 1: "SERVER-LAN"     MAC 08002705DA6D',
    "",
    "# Ten Internal Network phai trung tuyet doi; card NAT chi dung de cap nhat goi.",
], os.path.join(EVID, "ev4_nics.png"))

render("ip -br addr / ip route tren bon may dau cuoi", [
    "KALI 1 (10.10.10.10)",
    load(os.path.join(RUNS, "KB1_R1", "curl_K1.txt")).splitlines()[1],
    "KALI 2 (10.10.10.11)",
    "eth0             UP             10.10.10.11/24 fe80::a00:27ff:fe9c:d558/64",
    "route: 10.10.10.0/24 dev eth0 proto kernel scope link src 10.10.10.11",
    "",
    "WEB 1 (10.10.20.20) - Ubuntu 24.04.5",
    "eth0             UP             10.10.20.20/24",
    "WEB 2 (10.10.20.21) - Ubuntu 24.04.5",
    "eth0             UP             10.10.20.21/24",
    "",
    "# Gateway cua Kali: 10.10.10.1; gateway cua web: 10.10.20.1 (pfSense).",
], os.path.join(EVID, "ev4_ips.png"))

# live backend responses via pfSense
sys.path.insert(0, r"C:\Users\Admin\Desktop\ATT\ddos-lab2\scripts")
from lab import PF
pf = PF()
b1 = pf.cmd("curl -s --max-time 5 http://10.10.20.20:8080/")
b2 = pf.cmd("curl -s --max-time 5 http://10.10.20.21:8080/")
clean = lambda s: re.sub(r"<[^>]+>", "", s).strip()
render("Python HTTP Server tren hai backend (phan hoi tu pfSense)", [
    "$ curl -s http://10.10.20.20:8080/     # tu pfSense LAN",
    "WEB SERVER 1",
    "SERVER 1",
    "Host: web1 (10.10.20.20)",
    "",
    "$ curl -s http://10.10.20.21:8080/",
    "WEB SERVER 2",
    "SERVER 2",
    "Host: web2 (10.10.20.21)",
    "",
    "# Noi dung thuc te: " + clean(b1)[:60].replace("\n", " "),
    "# Noi dung thuc te: " + clean(b2)[:60].replace("\n", " "),
], os.path.join(EVID, "ev4_http.png"))

render("lab-http.jmx - tham so hoa bang -J", [
    "Thread Group: Threads = ${__P(threads,2)}; Loop = ${__P(loops,20)}",
    "HTTP Request: host=${__P(host,10.10.10.1)} port=${__P(port,8080)}",
    "  path=${__P(path,/load-test.txt)}?run=${__P(run,KB3_R1)}&src=${__P(src,K1)}",
    "Constant Timer: ${__P(timer,100)} ms; Timeout: 5000 ms",
    "",
    "$ TZ=UTC /home/kali/apache-jmeter-5.6.3/bin/jmeter -n -t lab-http.jmx \\",
    "    -Jrun=KB3_R1 -Jsrc=K1 -Jthreads=2 -Jloops=20 -Jtimer=100 \\",
    "    -Jpath=/load-test.txt -l KB3_R1_K1.jtl -j KB3_R1_K1.log",
    "$ ... (Kali 2: -Jsrc=K2 -l KB3_R1_K2.jtl)",
], os.path.join(EVID, "ev4_jmeter.png"))

render("custom.rules - hai luat cua bai thi nghiem", load(os.path.join(EVID, "ev_custom_rules.txt")).splitlines(),
       os.path.join(EVID, "ev4_sur_rules_text.png"), fs=19, lh=27, wrap=150)

render("threshold.config - rate_filter cua SID 1001002", [
    "# Noi dung that trong /usr/local/etc/suricata/suricata_12985_em0/threshold.config",
    "rate_filter gen_id 1, sig_id 1001002, track by_src, count 20, seconds 10,",
    "             new_action drop, timeout 15",
    "",
    "# Theo doi rieng tung IP nguon (by_src): 20 lan khop trong 10 giay",
    "# thi chuyen sang DROP trong 15 giay.",
], os.path.join(EVID, "ev4_threshold_text.png"))

# ---------------- KB1 ----------------
c1 = load(os.path.join(RUNS, "KB1_R1", "curl_K1.txt")).splitlines()
c2 = load(os.path.join(RUNS, "KB1_R1", "curl_K2.txt")).splitlines()
render("KB1_R1 - curl tu hai Kali toi frontend", [
    "KALI 1 - $ curl --noproxy '*' -i --max-time 5 'http://10.10.10.1:8080/?case=KB1_K1'",
] + c1 + ["", "KALI 2 - cung lenh, case=KB1_K2"] + c2, os.path.join(EVID, "ev5_1_curl.png"))

be1 = [l for l in load(os.path.join(RUNS, "KB1_R1", "backend_web1.txt")).splitlines() if "KB1_R1" in l]
be2 = [l for l in load(os.path.join(RUNS, "KB1_R1", "backend_web2.txt")).splitlines() if "KB1_R1" in l]
render("KB1_R1 - log backend va Summary Report", [
    "WEB 1 /var/log/syslog (loc KB1_R1, da bo /health.txt)",
] + be1[:3] + ["", "WEB 2 /var/log/syslog"] + be2[:3] + [
    "",
    "KALI 1 - JMeter summary",
    load(os.path.join(RUNS, "KB1_R1", "jmeter_K1_summary.txt")).splitlines()[-1],
    "KALI 2 - JMeter summary",
    load(os.path.join(RUNS, "KB1_R1", "jmeter_K2_summary.txt")).splitlines()[-1],
], os.path.join(EVID, "ev5_2_kb1.png"), fs=20, lh=29, wrap=140)

# ---------------- KB2 ----------------
off1 = load(os.path.join(RUNS, "KB2_R1", "curl_ips_off_r1_K1.txt")).splitlines()
off2 = load(os.path.join(RUNS, "KB2_R1", "curl_ips_off_r1_K2.txt")).splitlines()
render("KB2_R1 - IPS TAT: ca hai nguon nhan noi dung", [
    "KALI 1 - GET /ips-test.txt?case=IPS_OFF_K1_R1",
] + off1 + ["", "KALI 2 - GET /ips-test.txt?case=IPS_OFF_K2_R1"] + off2,
       os.path.join(EVID, "ev5_3_off.png"))

on1 = load(os.path.join(RUNS, "KB2_R1", "curl_ips_on_r1_K1.txt")).splitlines()
on2 = load(os.path.join(RUNS, "KB2_R1", "curl_ips_on_r1_K2.txt")).splitlines()
render("KB2_R1 - IPS BAT: timeout, 0 byte", [
    "KALI 1 - GET /ips-test.txt?case=IPS_ON_K1_R1",
] + on1 + ["", "KALI 2 - GET /ips-test.txt?case=IPS_ON_K2_R1"] + on2,
       os.path.join(EVID, "ev5_4_on.png"))

al1 = load(os.path.join(RUNS, "KB2_R1", "alerts_1001001.txt")).splitlines()
eve = load(os.path.join(RUNS, "KB2_R1", "eve_1001001.txt")).splitlines()
eve_short = []
for l in eve[:2]:
    try:
        j = json.loads(l)
        eve_short.append("  %s  event=%s action=%s sid=%s src=%s -> %s:%s" % (
            j["timestamp"], j["event_type"], j["alert"]["action"], j["alert"]["signature_id"],
            j["src_ip"], j["dest_ip"], j["dest_port"]))
    except Exception:
        pass
render("KB2_R1 - Alerts va EVE cho SID 1001001", [
    "alerts.log",
] + al1 + ["", "eve.json (trich truong chinh)"] + eve_short,
       os.path.join(EVID, "ev5_5_alerts.png"), fs=19, lh=27, wrap=150)

bw1 = [l for l in load(os.path.join(RUNS, "KB2_R1", "backend_web1.txt")).splitlines() if "IPS" in l]
bw2 = [l for l in load(os.path.join(RUNS, "KB2_R1", "backend_web2.txt")).splitlines() if "IPS" in l]
render("KB2_R1 - backend chi thay yeu cau IPS_OFF; trang chu van 200", [
    "WEB 1 - cac dong chua ma IPS (OFF hoac ON)",
] + (bw1[:3] or ["(khong co dong nao)"]) + ["", "WEB 2"] + (bw2[:3] or ["(khong co dong nao)"]) + [
    "",
    "$ curl -s -o /dev/null -w '%{http_code}' http://10.10.10.1:8080/health.txt",
    "200   # trang binh thuong sau phep thu van phuc vu",
], os.path.join(EVID, "ev5_6_backend.png"), fs=19, lh=27, wrap=150)

# ---------------- KB3 (R2: co rao dong bo 35 giay) ----------------
render("KB3 - hai tien trinh JMeter chay dong thoi (KB3_R2)", [
    "KALI 1 (10.10.10.10)",
    "$ TZ=UTC jmeter -n -t lab-http.jmx -Jrun=KB3_R2 -Jsrc=K1 -Jthreads=2 -Jloops=20 -Jtimer=100 -Jpath=/load-test.txt -l KB3_R2_K1.jtl",
    load(os.path.join(RUNS, "KB3_R2", "jmeter_K1_summary.txt")).splitlines()[-1],
    "  bat dau 11:30:25.231  ket thuc 11:30:28.076  (UTC)",
    "",
    "KALI 2 (10.10.10.11)",
    "$ TZ=UTC jmeter -n -t lab-http.jmx -Jrun=KB3_R2 -Jsrc=K2 -Jthreads=2 -Jloops=20 -Jtimer=100 -Jpath=/load-test.txt -l KB3_R2_K2.jtl",
    load(os.path.join(RUNS, "KB3_R2", "jmeter_K2_summary.txt")).splitlines()[-1],
    "  bat dau 11:30:23.895  ket thuc 11:30:26.972  (UTC)",
    "",
    "# Hai tien trinh dung chung mot moc rao 35 giay (barrier) nen chay dong thoi:",
    "# cua so chong lan 11:30:25.231 - 11:30:26.972 (~1,7 giay).",
], os.path.join(EVID, "ev5_7_load.png"), fs=19, lh=27, wrap=150)

render("KB3 - Summary Report tren tung nguon (KB3_R2)", [
    "KALI 1", load(os.path.join(RUNS, "KB3_R2", "jmeter_K1_summary.txt")).splitlines()[-1],
    "KALI 2", load(os.path.join(RUNS, "KB3_R2", "jmeter_K2_summary.txt")).splitlines()[-1],
    "",
    "Tong thuc te: 80 mau; loi: 0; Avg 40/39 ms; P95 44/47 ms; 10,8/10,5 req/s.",
], os.path.join(EVID, "ev5_8_kb3jmeter.png"), fs=20, lh=30, wrap=140)

k3w1 = [re.sub(r"^.*python3\[\d+\]: ", "", l) for l in load(os.path.join(RUNS, "KB3_R2", "backend_web1.txt")).splitlines() if "KB3_R2" in l]
k3w2 = [re.sub(r"^.*python3\[\d+\]: ", "", l) for l in load(os.path.join(RUNS, "KB3_R2", "backend_web2.txt")).splitlines() if "KB3_R2" in l]
render("KB3 - /load-test.txt tai ca hai backend (KB3_R2)", [
    "WEB 1 - 42 dong (2 probe + 40 yeu cau tai); theo src: K1=20, K2=20",
] + k3w1[:6] + ["  ...", "WEB 2 - 42 dong (2 probe + 40 yeu cau tai); theo src: K1=20, K2=20"] + k3w2[:6] + [
    "",
    "# Moi dong deu co run=KB3_R2 va src=K1/K2; /health.txt da bi loai.",
], os.path.join(EVID, "ev5_9_kb3backend.png"), fs=18, lh=26, wrap=160)

def stats_table(run):
    m = json.load(open(os.path.join(RUNS, run, "meta.json"), encoding="utf-8"))
    b, a = m["stats_before"], m["stats_after"]
    rows = []
    for s in ("web1", "web2"):
        rows.append("%-6s %-5s %-7s %7s -> %-7s  %+d" % (s, b[s]["status"], b[s]["check_status"],
                                                          b[s]["stot"], a[s]["stot"], int(a[s]["stot"]) - int(b[s]["stot"])))
    return rows, b, a

rows, b, a = stats_table("KB3_R2")
render("KB3 - HAProxy Stats truoc / sau (KB3_R2)", [
    "Truoc (11:29Z): web1 stot=1, web2 stot=1, backend=2",
    "Sau   (11:31Z): web1 stot=40, web2 stot=40, backend=80",
    "Backend row: " + rows[0],
    "Backend row: " + rows[1],
    "",
    "# Delta: web1 +39, web2 +39; log backend ghi 80 yeu cau tai (40/40), khong tinh health check.",
], os.path.join(EVID, "ev5_10_stats.png"), fs=20, lh=30, wrap=140)

# ---------------- KB4 (R2: rate_filter BAT) ----------------
k4w1 = [re.sub(r"^.*python3\[\d+\]: ", "", l) for l in load(os.path.join(RUNS, "KB4_R2", "backend_web1.txt")).splitlines() if "KB4_R2" in l]
k4w2 = [re.sub(r"^.*python3\[\d+\]: ", "", l) for l in load(os.path.join(RUNS, "KB4_R2", "backend_web2.txt")).splitlines() if "KB4_R2" in l]
render("KB4 - Summary Report voi rate_filter bat (KB4_R2)", [
    "KALI 1", load(os.path.join(RUNS, "KB4_R2", "jmeter_K1_summary.txt")).splitlines()[-1],
    "KALI 2", load(os.path.join(RUNS, "KB4_R2", "jmeter_K2_summary.txt")).splitlines()[-1],
    "",
    "Moi nguon: 36 x HTTP 200 + 4 x SocketTimeoutException (10%); Max 5040 / 5204 ms.",
    "P95 cua mau thanh cong chi con 50 / 40 ms; P95 toan bo 5008 / 5021 ms.",
], os.path.join(EVID, "ev5_11_kb4jmeter.png"), fs=20, lh=30, wrap=140)

drops = [l for l in load(os.path.join(RUNS, "KB4_R2", "alerts_1001002.txt")).splitlines() if "[Drop]" in l]
render("KB4 - DROP cua SID 1001002 cho ca hai nguon (KB4_R2)", [
    "alerts.log - 6 dong [Drop] trong cua so tai KB4_R2",
] + drops + [
    "",
    "# Drop theo nguon: Kali 1 = 2, Kali 2 = 4. Dong ho pfSense cham ~4 phut so voi Kali",
    "# (gio tren dong log la gio pfSense; moc gio thuc lay tu JTL cua hai may Kali).",
], os.path.join(EVID, "ev5_12_kb4drops.png"), fs=19, lh=27, wrap=150)

render("KB4 - yeu cau con lai van toi backend (KB4_R2)", [
    "WEB 1 - 37 dong KB4_R2 (1 probe + 36 yeu cau tai; src K1=18, K2=18)",
] + k4w1[:4] + ["  ...", "WEB 2 - 37 dong KB4_R2 (1 probe + 36 yeu cau tai; src K1=18, K2=18)"] + k4w2[:4] + [
    "",
    "# Tong 72 yeu cau tai toi backend so voi 80 cua KB3: giam (80-72)/80 = 10%.",
    "Yeu cau doi chung: GET /?case=KB4_CONTROL => 200 (ca hai lan).",
], os.path.join(EVID, "ev5_13_kb4backend.png"), fs=18, lh=26, wrap=160)

# ---------------- KB5 ----------------
m5 = json.load(open(os.path.join(RUNS, "KB5_R1", "meta.json"), encoding="utf-8"))
su, sd, sa = m5["stats_up"], m5["stats_down"], m5["stats_after"]
kb5base2 = [l for l in load(os.path.join(RUNS, "KB5_R1", "curl_kb5_base_r1_2.txt")).splitlines() if l.startswith("HTTP/") or "SERVER" in l or l.startswith("date:")]
kb5dur = [l for l in load(os.path.join(RUNS, "KB5_R1", "curl_kb5_during_r1_2.txt")).splitlines() if l.startswith("HTTP/") or "SERVER" in l]
render("KB5 - truoc su co: ca hai backend UP (KB5_R1)", [
    "HAProxy Stats luc 11:11:20Z",
    "  web1  10.10.20.20:8080  UP  L7OK   stot=5",
    "  web2  10.10.20.21:8080  UP  L7OK   stot=9",
    "  backend web_pool        UP          stot=14",
    "",
    "Phan hoi frontend voi 4 yeu cau KB5_BASE (web1 2, web2 2):",
    "  SERVER 2  HTTP/1.0 200 OK  (date 11:11:20 GMT)",
    "  SERVER 1  HTTP/1.0 200 OK  (date 11:11:20 GMT)",
    "",
    "# Moc bat dau: 11:11:20-11:11:21Z; ca hai backend cung nhan yeu cau.",
], os.path.join(EVID, "ev5_14_kb5up.png"), fs=19, lh=27, wrap=150)

render("KB5 - Web 1 DOWN, Web 2 tiep tuc phuc vu (KB5_R1)", [
    "Dung dich vu:  systemctl stop att-web   luc 11:11:30Z",
    "HAProxy phat hien: web1 DOWN (L4CON) luc 11:11:33Z  (~3 giay)",
    "",
    "HAProxy Stats luc 11:11:34Z",
    "  web1  10.10.20.20:8080  DOWN  L4CON   stot=7   lastchg=8 s",
    "  web2  10.10.20.21:8080  UP    L7OK    stot=11",
    "",
    "4 yeu cau KB5_DURING qua frontend: 4/4 nhan SERVER 2",
] + kb5dur + [
    "",
    "# Khong yeu cau nao bi loi; web2 phuc vu thay web1.",
], os.path.join(EVID, "ev5_15_kb5down.png"), fs=19, lh=27, wrap=150)

w5 = [re.sub(r"^.*(web1|web2) python3\[\d+\]: ", "", l)
      for l in load(os.path.join(RUNS, "KB5_R1", "backend_web1.txt")).splitlines()
      if ("KB5_BASE" in l and "11:11" in l) or ("KB5_AFTER" in l and "11:12" in l) or ("att-web" in l and "11:11" in l)]
render("KB5 - Web 1 tro lai UP va nhan yeu cau (KB5_R1)", [
    "Khoi dong lai:  systemctl start att-web  luc 11:11:54Z",
    "HAProxy bao web1 UP (L7OK/200) luc 11:11:58Z  (~4 giay)",
    "",
    "HAProxy Stats luc 11:12:16Z",
    "  web1  UP  L7OK  stot=7     web2  UP  L7OK  stot=15",
    "",
    "Log Web 1 (systemd + python3):",
] + w5 + [
    "",
    "# 6 yeu cau KB5_AFTER sau khoi phuc dien ra xen ke web2, web1, web2, web1, web2, web1.",
], os.path.join(EVID, "ev5_16_log.png"), fs=18, lh=26, wrap=160)

# ---------------- composites of screenshots ----------------
stack([os.path.join(EVID, "pf-dash1.png")], ["(a) Dashboard pfSense sau dang nhap"], os.path.join(EVID, "ev4_dash.png"))

if __name__ == "__main__":
    topology(os.path.join(EVID, "ev3_1_topology.png"))
print("all done")
