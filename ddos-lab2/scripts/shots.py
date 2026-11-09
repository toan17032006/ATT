#!/usr/bin/env python3
"""Capture pfSense webConfigurator screenshots as report evidence."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8443"
OUT = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"

PAGES = [
    ("pf-sur1.png", "/suricata/suricata_interfaces.php"),
    ("pf-sur2.png", "/suricata/suricata_rules.php?id=0&openruleset=custom.rules"),
    ("pf-sur3.png", "/suricata/suricata_alerts.php"),
    ("pf-hap1.png", "/haproxy/haproxy_pools.php"),
    ("pf-hap2.png", "/haproxy/haproxy_listeners.php"),
]

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(BASE + "/", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#usernamefld", "admin")
    pg.fill("#passwordfld", "pfsense")
    pg.press("#passwordfld", "Enter")
    pg.wait_for_load_state("networkidle", timeout=30000)
    assert "Dashboard" in pg.content() or "Status" in pg.content(), "login failed"
    pg.screenshot(path=OUT + r"\pf-dash1.png")
    for name, path in PAGES:
        pg.goto(BASE + path, wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(800)
        pg.screenshot(path=OUT + "\\" + name)
        print("saved", name)
    b.close()
