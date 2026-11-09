#!/usr/bin/env python3
"""Generate fresh IPS evidence + pfSense GUI screenshots for the report figures."""
import json, os, sys, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import vmrun, PF

EVID = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"
os.makedirs(EVID, exist_ok=True)

pf = PF()

now = datetime.datetime.now(datetime.timezone.utc)
stamp = now.strftime("%Y%m%d%H%M.%S")
print("host utc", now.isoformat())
print("set pf clock:", pf.cmd("date -u " + stamp)[:200])
print(pf.cmd("date -u")[:200])

probe = ("curl --noproxy '*' -sS -m 5 -o /tmp/fig_body.txt -w 'HTTP=%{http_code} bytes=%{size_download} time=%{time_total}\\n' "
         "'http://10.10.10.1:8080/ips-test.txt?case=FIG_IPS_K1'; echo rc=$?; head -c 200 /tmp/fig_body.txt; echo")
probe2 = probe.replace("FIG_IPS_K1", "FIG_IPS_K2")
out1 = vmrun("ATT-Kali1", "date -u; " + probe, timeout=40)
out2 = vmrun("ATT-Kali2", "date -u; " + probe2, timeout=40)
print("PROBE K1:\n", out1)
print("PROBE K2:\n", out2)
open(os.path.join(EVID, "ev_probe_ips.txt"), "w", encoding="utf-8").write(
    "Kali 1 (10.10.10.10)\n" + out1 + "\n\nKali 2 (10.10.10.11)\n" + out2 + "\n")

burst = ("for i in $(seq 1 30); do curl --noproxy '*' -s -m 2 -o /dev/null "
         "-w '%{http_code} ' 'http://10.10.10.1:8080/load-test.txt?run=FIG1001002&src=K1'; done; echo; date -u")
burst2 = burst.replace("src=K1", "src=K2")
b1 = vmrun("ATT-Kali1", burst, timeout=120)
b2 = vmrun("ATT-Kali2", burst2, timeout=120)
print("BURST K1:\n", b1)
print("BURST K2:\n", b2)
open(os.path.join(EVID, "ev_burst_1001002.txt"), "w", encoding="utf-8").write(
    "Kali 1 burst 30 requests\n" + b1 + "\n\nKali 2 burst 30 requests\n" + b2 + "\n")

time.sleep(2)
print("threshold:", pf.cmd("cat /usr/local/etc/suricata/suricata_12985_em0/threshold.config")[:300])
print("alerts tail:", pf.cmd("tail -6 /var/log/suricata/suricata_em012985/alerts.log")[:800])

# ---- GUI screenshots ----
from playwright.sync_api import sync_playwright

PAGES = [
    ("ev_sur_wan.png", "/suricata/suricata_interfaces_edit.php?id=0"),
    ("ev_sur_rules.png", "/suricata/suricata_rules.php?id=0&openruleset=custom.rules"),
    ("ev_sur_alerts.png", "/suricata/suricata_alerts.php"),
    ("ev_sur_suppress.png", "/suricata/suricata_suppress.php"),
    ("ev_wan_rules.png", "/firewall_rules.php?if=wan"),
    ("ev_aliases.png", "/firewall_aliases.php"),
    ("ev_nat.png", "/firewall_nat.php"),
    ("ev_hap_pools.png", "/haproxy/haproxy_pools.php"),
    ("ev_hap_listen.png", "/haproxy/haproxy_listeners.php"),
    ("ev_hap_settings.png", "/haproxy/haproxy_settings.php"),
    ("ev_hap_stats.png", "/haproxy/haproxy_stats.php?haproxystats=1"),
]

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1500, "height": 1100})
    pg.goto("http://127.0.0.1:8443/", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#usernamefld", "admin")
    pg.fill("#passwordfld", "pfsense")
    pg.press("#passwordfld", "Enter")
    pg.wait_for_load_state("networkidle", timeout=30000)
    for name, path in PAGES:
        try:
            pg.goto("http://127.0.0.1:8443" + path, wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(700)
            title = pg.title()
            pg.screenshot(path=os.path.join(EVID, name), full_page=True)
            print("shot", name, "|", title)
        except Exception as e:
            print("FAIL", name, e)
    b.close()
print("done")
