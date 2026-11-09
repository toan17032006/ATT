#!/usr/bin/env python3
"""KB1 - normal HTTP access from both Kali sources."""
import os
import time
import json
import subprocess
from lab import vmrun, vmstart, PF, kdir, save, utcnow, stats_csv, ssh_web

RUN = "KB1_R1"
d = kdir(RUN)
pf = PF()
meta = {"run": RUN, "start": utcnow()}
JM = "/home/kali/apache-jmeter-5.6.3/bin/jmeter"

ps = pf.cmd("ps auxww | grep -c '[s]uricata --netmap'")
meta["suricata_before"] = ps.strip()
if ps.strip() in ("0", ""):
    pf.post("/suricata/suricata_interfaces.php", {"toggle": "start", "id": "0"})
    time.sleep(12)

meta["stats_before"] = stats_csv(pf, "before", d)

# Step 1: one curl per source
for k, ip in (("K1", "10.10.10.10"), ("K2", "10.10.10.11")):
    vm = "ATT-Kali1" if k == "K1" else "ATT-Kali2"
    out = vmrun(vm, "echo SRC=%s; ip -4 -br addr show eth0; "
                     "curl -sS --noproxy '*' -i -m 5 'http://10.10.10.1:8080/?case=KB1_%s'" % (ip, k))
    save(d, "curl_%s.txt" % k, out)
    print("curl", k, "done", len(out))

# Step 2: low-load JMeter on both sources at the same time
start = utcnow()
for k, vm in (("K1", "ATT-Kali1"), ("K2", "ATT-Kali2")):
    cmd = ("cd /home/kali && TZ=UTC %s -n -t lab-http.jmx -Jrun=%s -Jsrc=%s "
           "-Jthreads=1 -Jloops=5 -Jtimer=1000 -Jpath=/load-test.txt "
           "-l %s_%s.jtl -j %s_%s.log") % (JM, RUN, k, RUN, k, RUN, k)
    vmstart(vm, cmd)

deadline = time.time() + 90
while time.time() < deadline:
    r1 = vmrun("ATT-Kali1", "pgrep -f '[K]B1_R1_K1.jtl' || true", timeout=30)
    r2 = vmrun("ATT-Kali2", "pgrep -f '[K]B1_R1_K2.jtl' || true", timeout=30)
    if not r1.strip() and not r2.strip():
        break
    time.sleep(2)
meta["load_start"] = start
meta["load_end"] = utcnow()
time.sleep(3)

meta["stats_after"] = stats_csv(pf, "after", d)

for k, vm in (("K1", "ATT-Kali1"), ("K2", "ATT-Kali2")):
    src = "C:/Users/Admin/Desktop/ATT/ddos-lab2/runs/%s/%s_%s.jtl" % (RUN, RUN, k)
    args = [r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe", "guestcontrol", vm,
            "copyfrom", "/home/kali/%s_%s.jtl" % (RUN, k), src,
            "--username", "kali", "--password", "kali"]
    r = subprocess.run(args, capture_output=True, text=True, env={**os.environ, "MSYS_NO_PATHCONV": "1"})
    print("copy", k, r.returncode, (r.stdout or r.stderr).strip()[:100])
    summary = vmrun(vm, "cd /home/kali && grep -E 'summary' %s_%s.log | tail -2" % (RUN, k))
    save(d, "jmeter_%s_summary.txt" % k, summary)

for w, host in (("web1", "10.10.20.20"), ("web2", "10.10.20.21")):
    out = ssh_web(pf, host,
                  "sudo -n journalctl -u att-web --since '-20 min' --no-pager | "
                  "grep -E 'KB1' | tail -40 || echo 'no KB1 lines'")
    save(d, "backend_%s.txt" % w, out)
    print("backend", w, len(out))

meta["end"] = utcnow()
json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)
print(json.dumps(meta, indent=2))
