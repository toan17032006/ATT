#!/usr/bin/env python3
"""KB3/KB4 - two concurrent sources with the rate_filter OFF (KB3) and ON (KB4)."""
import os
import sys
import time
import json
import subprocess
from lab import vmrun, vmstart, PF, kdir, save, utcnow, stats_csv, ssh_web

RUN = sys.argv[1] if len(sys.argv) > 1 else "KB3_R1"
POLICY = sys.argv[2] if len(sys.argv) > 2 else "off"   # off | on
THRESH = "none" if POLICY == "off" else "lab_thresholds"
d = kdir(RUN)
pf = PF()
meta = {"run": RUN, "policy": POLICY, "start": utcnow()}
JM = "/home/kali/apache-jmeter-5.6.3/bin/jmeter"
TH_FILE = "/usr/local/etc/suricata/suricata_12985_em0/threshold.config"


def ps_count():
    return int(pf.cmd("pgrep -f '[s]uricata --netmap' | wc -l").strip() or "0")


def toggle(action):
    try:
        pf.post("/suricata/suricata_interfaces.php", {"toggle": action, "id": "0"})
    except Exception as e:
        meta.setdefault("post_errors", []).append("%s: %s" % (action, e))


def restart_ips():
    if ps_count() > 0:
        toggle("stop")
        deadline = time.time() + 60
        while time.time() < deadline and ps_count() > 0:
            time.sleep(2)
    if ps_count() == 0:
        toggle("start")
        deadline = time.time() + 90
        while time.time() < deadline and ps_count() == 0:
            time.sleep(2)
    time.sleep(12)
    return ps_count()


# 1) Bind / unbind the threshold list, then restart so threshold.config is regenerated
r = subprocess.run([sys.executable, "sur_add.py", THRESH], capture_output=True, text=True)
meta["sur_add"] = (r.stdout or r.stderr).strip()[-300:]
meta["ps"] = restart_ips()
meta["threshold_config"] = pf.cmd("cat %s 2>/dev/null || echo missing" % TH_FILE).strip()
save(d, "threshold_config.txt", meta["threshold_config"])

# 2) Baseline probe from each source
for k in ("K1", "K2"):
    vm = "ATT-Kali1" if k == "K1" else "ATT-Kali2"
    out = vmrun(vm, "curl -sS --noproxy '*' -o /dev/null -w '%%{http_code}' -m 6 "
                     "'http://10.10.10.1:8080/load-test.txt?case=%s_PROBE_%s'" % (RUN, k))
    meta["probe_" + k] = out.strip()

meta["stats_before"] = stats_csv(pf, "before", d)

# 3) Concurrent load from both sources, released by a shared epoch barrier
start = utcnow()
t0 = int(time.time()) + 35
meta["barrier_epoch"] = t0
for k, vm in (("K1", "ATT-Kali1"), ("K2", "ATT-Kali2")):
    cmd = ("while [ $(date +%%s) -lt %d ]; do sleep 0.2; done; cd /home/kali && TZ=UTC %s -n -t lab-http.jmx -Jrun=%s -Jsrc=%s "
           "-Jthreads=2 -Jloops=20 -Jtimer=100 -Jpath=/load-test.txt "
           "-l %s_%s.jtl -j %s_%s.log") % (t0, JM, RUN, k, RUN, k, RUN, k)
    vmstart(vm, cmd)

deadline = time.time() + 300
while time.time() < deadline:
    pat = "[%s]%s" % (RUN[0], RUN[1:])
    r1 = vmrun("ATT-Kali1", "pgrep -f '%s_K1.jtl' || true" % pat, timeout=30)
    r2 = vmrun("ATT-Kali2", "pgrep -f '%s_K2.jtl' || true" % pat, timeout=30)
    if not r1.strip() and not r2.strip():
        break
    time.sleep(2)
meta["load_start"] = start
meta["load_end"] = utcnow()
time.sleep(3)

meta["stats_after"] = stats_csv(pf, "after", d)

# 4) JTLs and summaries
for k, vm in (("K1", "ATT-Kali1"), ("K2", "ATT-Kali2")):
    src = "C:/Users/Admin/Desktop/ATT/ddos-lab2/runs/%s/%s_%s.jtl" % (RUN, RUN, k)
    args = [r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe", "guestcontrol", vm,
            "copyfrom", "/home/kali/%s_%s.jtl" % (RUN, k), src,
            "--username", "kali", "--password", "kali"]
    r = subprocess.run(args, capture_output=True, text=True, env={**os.environ, "MSYS_NO_PATHCONV": "1"})
    print("copy", k, r.returncode)
    summary = vmrun(vm, "cd /home/kali && grep -E 'summary' %s_%s.log | tail -3" % (RUN, k))
    save(d, "jmeter_%s_summary.txt" % k, summary)

# 5) Suricata drop evidence for SID 1001002 (rate_filter events)
al = pf.cmd("grep -h '1001002' /var/log/suricata/suricata_*/alerts.log | tail -40")
save(d, "alerts_1001002.txt", al)
meta["drops_1001002"] = al.count("[Drop]")
meta["drop_src_k1"] = al.count("10.10.10.10")
meta["drop_src_k2"] = al.count("10.10.10.11")
eve = pf.cmd("grep -h 'signature_id\":1001002' /var/log/suricata/suricata_*/eve.json | tail -20")
save(d, "eve_1001002.txt", eve)
meta["eve_1001002"] = len([l for l in eve.splitlines() if l.strip()])

# 6) Backend request counts for this run
for w, host in (("web1", "10.10.20.20"), ("web2", "10.10.20.21")):
    out = ssh_web(pf, host,
                  "sudo -n journalctl -u att-web --since '-12 min' --no-pager | "
                  "grep '%s' || echo 'no %s lines'" % (RUN, RUN))
    save(d, "backend_%s.txt" % w, out)
    meta["backend_%s" % w] = out.count(RUN)
    print("backend", w, meta["backend_%s" % w])

meta["end"] = utcnow()
json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)
print(json.dumps(meta, indent=2))
