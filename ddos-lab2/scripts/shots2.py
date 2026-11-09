#!/usr/bin/env python3
"""Capture cropped pfSense pages for report figures."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image

EVID = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"
PAGES = [
    ("ev_sur_alerts_full.png", "/suricata/suricata_alerts.php", 1500),
    ("ev_sur_blocks_full.png", "/suricata/suricata_blocks.php", 1200),
    ("ev_sur_suppress_full.png", "/suricata/suricata_suppress.php", 1200),
    ("ev_hap_pool_edit_full.png", "/haproxy/haproxy_pool_edit.php?id=0", 1400),
    ("ev_hap_listen_edit_full.png", "/haproxy/haproxy_listeners_edit.php?id=web_front", 1300),
    ("ev_hap_global_full.png", "/haproxy/haproxy_global.php", 1100),
    ("ev_hap_stats_full.png", "/haproxy/haproxy_stats.php?haproxystats=1", 950),
    ("ev_wan_rules_full.png", "/firewall_rules.php?if=wan", 1000),
    ("ev_aliases_full.png", "/firewall_aliases.php", 900),
    ("ev_nat_full.png", "/firewall_nat.php", 900),
    ("ev_sur_wan_full.png", "/suricata/suricata_interfaces_edit.php?id=0", 1500),
    ("ev_sur_rules_full.png", "/suricata/suricata_rules.php?id=0&openruleset=custom.rules", 1000),
]

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1500, "height": 1000})
    pg.goto("http://127.0.0.1:8443/", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#usernamefld", "admin")
    pg.fill("#passwordfld", "pfsense")
    pg.press("#passwordfld", "Enter")
    pg.wait_for_load_state("networkidle", timeout=30000)
    for name, path, crop_h in PAGES:
        try:
            pg.goto("http://127.0.0.1:8443" + path, wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(600)
            full = os.path.join(EVID, name)
            pg.screenshot(path=full, full_page=True)
            im = Image.open(full)
            w, h = im.size
            im.crop((0, 0, w, min(crop_h, h))).save(full.replace("_full", ""))
            print("ok", name, w, h)
        except Exception as e:
            print("FAIL", name, e)
    b.close()
