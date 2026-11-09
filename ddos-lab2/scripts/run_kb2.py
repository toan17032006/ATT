#!/usr/bin/env python3
"""KB2 - IPS control test: /ips-test.txt allowed with IPS off, dropped with IPS on."""
import os
import time
import json
from lab import vmrun, PF, kdir, save, utcnow, ssh_web

RUN = "KB2_R1"
d = kdir(RUN)
pf = PF()
meta = {"run": RUN, "start": utcnow()}


def ps_count():
    return pf.cmd("pgrep -f '[s]uricata --netmap' | wc -l").strip()


def set_ips(action):
    want = (action == "start")
    if (int(ps_count()) > 0) == want:
        return ps_count()
    try:
        pf.post("/suricata/suricata_interfaces.php", {"toggle": action, "id": "0"})
    except Exception as e:
        meta.setdefault("post_errors", []).append("%s: %s" % (action, e))
    deadline = time.time() + 60
    while time.time() < deadline:
        n = ps_count()
        if (int(n) > 0) == want:
            break
        time.sleep(2)
    time.sleep(12 if want else 3)
    return ps_count()


def curl_both(tag):
    out = {}
    for k in ("K1", "K2"):
        vm = "ATT-Kali1" if k == "K1" else "ATT-Kali2"
        c = ("curl -sS --noproxy '*' -i -m 6 "
             "'http://10.10.10.1:8080/ips-test.txt?case=%s_%s' 2>&1; echo CURL_RC=$?" % (tag, k))
        out[k] = vmrun(vm, c)
        save(d, "curl_%s_%s.txt" % (tag.lower(), k), out[k])
    return out


# 1) IPS off
meta["ps_before_stop"] = ps_count()
meta["ps_after_stop"] = set_ips("stop")
off = curl_both("IPS_OFF_R1")
meta["off_rc"] = {k: ("CURL_RC=0" in v) for k, v in off.items()}

# 2) IPS on
meta["ps_after_start"] = set_ips("start")
on = curl_both("IPS_ON_R1")
meta["on_timeout"] = {k: ("CURL_RC=28" in v) for k, v in on.items()}

# 3) control URI still reachable
ctl = vmrun("ATT-Kali1", "curl -sS --noproxy '*' -o /dev/null -w '%{http_code}' -m 6 "
                         "'http://10.10.10.1:8080/health.txt?case=KB2_CTRL_R1'")
meta["control_status"] = ctl.strip()
save(d, "curl_control.txt", ctl)

# 4) Suricata evidence
eve = pf.cmd("grep -h '\"sid\":1001001' /var/log/suricata/suricata_*/eve.json | tail -8")
save(d, "eve_1001001.txt", eve)
alerts = pf.cmd("grep -h '1001001' /var/log/suricata/suricata_*/alerts.log | tail -8")
save(d, "alerts_1001001.txt", alerts)
meta["eve_hits"] = len([l for l in eve.splitlines() if l.strip()])

# 5) Backend request log for this scenario
for w, host in (("web1", "10.10.20.20"), ("web2", "10.10.20.21")):
    out = ssh_web(pf, host,
                  "sudo -n journalctl -u att-web --since '-8 min' --no-pager | "
                  "grep -E 'IPS_(OFF|ON)_R1|KB2_CTRL' || echo 'no KB2 lines'")
    save(d, "backend_%s.txt" % w, out)
    meta["backend_%s_off_lines" % w] = out.count("IPS_OFF")
    meta["backend_%s_on_lines" % w] = out.count("IPS_ON")

meta["end"] = utcnow()
json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)
print(json.dumps(meta, indent=2))
