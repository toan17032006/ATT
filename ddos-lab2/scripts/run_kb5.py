#!/usr/bin/env python3
"""KB5 - web1 backend outage and recovery, with HAProxy failover evidence."""
import os
import time
import json
from lab import vmrun, PF, kdir, save, utcnow, stats_csv, ssh_web, EVID

RUN = "KB5_R1"
d = kdir(RUN)
pf = PF()
meta = {"run": RUN, "start": utcnow()}
HOST1 = "10.10.20.20"
BASE = "http://127.0.0.1:8443"

from playwright.sync_api import sync_playwright
_pw = sync_playwright().start()
b = _pw.chromium.launch(channel="chrome", headless=True)
pg = b.new_page(viewport={"width": 1600, "height": 1000})
pg.goto(BASE + "/", wait_until="domcontentloaded", timeout=30000)
pg.fill("#usernamefld", "admin")
pg.fill("#passwordfld", "pfsense")
pg.press("#passwordfld", "Enter")
pg.wait_for_load_state("networkidle", timeout=30000)


def shot(name):
    pg.goto(BASE + "/haproxy/haproxy_stats.php?haproxystats=1",
            wait_until="networkidle", timeout=30000)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(EVID, name), full_page=True)


def curl_k1(tag, n):
    out = vmrun("ATT-Kali1", "curl -sS --noproxy '*' -i -m 6 "
                             "'http://10.10.10.1:8080/?case=%s&n=%s'" % (tag, n))
    save(d, "curl_%s_%s.txt" % (tag.lower(), n), out)
    if "SERVER 1" in out:
        return "web1"
    if "SERVER 2" in out:
        return "web2"
    return "?"


def wait_status(target, timeout_s=60):
    t0 = time.time()
    seen = None
    while time.time() - t0 < timeout_s:
        st = stats_csv(pf, "poll", d)
        s1 = st.get("web1", {}).get("status", "?")
        if s1 == target:
            seen = utcnow()
            break
        time.sleep(1)
    return seen, round(time.time() - t0, 1)


# baseline
meta["stats_up"] = stats_csv(pf, "up", d)
shot("KB5_R1_up.png")
meta["base_dist"] = [curl_k1("KB5_BASE_R1", i) for i in range(1, 5)]

# stop att-web on web1
meta["stop_t0"] = utcnow()
meta["stop_out"] = ssh_web(pf, HOST1, "echo T0=$(date -u +%H:%M:%S); sudo -n systemctl stop att-web; "
                                        "echo T1=$(date -u +%H:%M:%S); systemctl is-active att-web || true")
meta["stop_t1"] = utcnow()
down_at, down_wait = wait_status("DOWN", 60)
meta["down_at"] = down_at
meta["down_wait_s"] = down_wait
time.sleep(2)
shot("KB5_R1_down.png")
meta["stats_down"] = stats_csv(pf, "down", d)
meta["during_dist"] = [curl_k1("KB5_DURING_R1", i) for i in range(1, 5)]
meta["during_sample"] = open(os.path.join(d, "curl_kb5_during_r1_1.txt"), encoding="utf-8").read()

# restart att-web on web1
meta["start_t0"] = utcnow()
meta["start_out"] = ssh_web(pf, HOST1, "echo T0=$(date -u +%H:%M:%S); sudo -n systemctl start att-web; "
                                        "echo T1=$(date -u +%H:%M:%S); systemctl is-active att-web")
meta["start_t1"] = utcnow()
up_at, up_wait = wait_status("UP", 60)
meta["up_at"] = up_at
meta["up_wait_s"] = up_wait
time.sleep(3)
shot("KB5_R1_up2.png")
meta["stats_after"] = stats_csv(pf, "after", d)
meta["after_dist"] = [curl_k1("KB5_AFTER_R1", i) for i in range(1, 7)]

for w, host in (("web1", HOST1), ("web2", "10.10.20.21")):
    out = ssh_web(pf, host,
                  "sudo -n journalctl -u att-web --since '-12 min' --no-pager | "
                  "grep -E 'KB5|Stopping|Started|Stopped' | tail -30 || true")
    save(d, "backend_%s.txt" % w, out)

meta["end"] = utcnow()
json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)
b.close()
_pw.stop()
print(json.dumps(meta, indent=2))
