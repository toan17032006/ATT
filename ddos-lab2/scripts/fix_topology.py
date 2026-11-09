# -*- coding: utf-8 -*-
import math
import os
from PIL import Image, ImageDraw, ImageFont

EVID = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"
SANS = r"C:\Windows\Fonts\arial.ttf"
SANSB = r"C:\Windows\Fonts\arialbd.ttf"

W, H = 1650, 920
im = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(im)
f = ImageFont.truetype(SANS, 26)
fb = ImageFont.truetype(SANSB, 28)
fs = ImageFont.truetype(SANS, 22)

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
box(560, 190, 1080, 700, "pfSense 2.7.2 (FreeBSD 14)",
    ["WAN em0: 10.10.10.1/24", "Suricata 7.0.8 - Inline IPS (netmap)", "Firewall: TCP/8080 tu KALI_LAB",
     "HAProxy 2.8.3: web_frontend", "  bind 10.10.10.1:8080", "  backend web_pool: round-robin",
     "LAN em1: 10.10.20.1/24"], fill="#fdf7e8", edge="#8a6d1f")
box(1230, 240, 1580, 452, "Web 1", ["10.10.20.20:8080", "Ubuntu 24.04.5", "Python 3.12.3 http.server", "att-web.service"])
box(1230, 530, 1580, 742, "Web 2", ["10.10.20.21:8080", "Ubuntu 24.04.5", "Python 3.12.3 http.server", "att-web.service"])


def arrow(x1, y1, x2, y2, color="#1f3864", width=4):
    d.line((x1, y1, x2, y2), fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 18
    for s in (-0.45, 0.45):
        d.line((x2, y2, x2 - L * math.cos(ang + s), y2 - L * math.sin(ang + s)), fill=color, width=width)


arrow(432, 360, 558, 360)
arrow(432, 630, 558, 630)
d.text((330, 205), "HTTP :8080", font=fb, fill="#a61b1b")
d.text((332, 235), "/load-test.txt?run=&src=", font=fs, fill="#a61b1b")
arrow(1082, 346, 1226, 346)
arrow(1082, 636, 1226, 636)
d.text((1086, 306), "round-robin", font=fs, fill="#245c2c")
d.text((1086, 596), "round-robin", font=fs, fill="#245c2c")
d.text((80, 858), "Mui ten lien: chieu yeu cau; phan hoi tra nguoc qua HAProxy ve Kali.", font=fs, fill="#374151")

out = os.path.join(EVID, "ev3_1_topology.png")
im.save(out)
print("saved", out, im.size)
