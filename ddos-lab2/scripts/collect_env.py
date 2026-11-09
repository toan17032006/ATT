#!/usr/bin/env python3
"""Collect real environment facts (VM configs, OS/tool versions, IPs) for the report."""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import vmrun, PF, ssh_web

GC = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
env = dict(os.environ); env["MSYS_NO_PATHCONV"] = "1"
OUT = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\env_data.json"

VMS = ["ATT-Kali1", "ATT-Kali2", "ATT-pfSense", "ATT-WEB1", "ATT-WEB2"]
res = {"vms": {}, "host": {}}

def vminfo(vm):
    try:
        r = subprocess.run([GC, "showvminfo", vm, "--machinereadable"],
                           capture_output=True, text=True, timeout=30, env=env)
        d = {}
        for line in r.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                d[k] = v.strip('"')
        return {k: d.get(k) for k in ("name", "memory", "cpus", "firmware", "ostype",
                                      "graphicscontroller", "vram", "nic1", "nic2",
                                      "nictype1", "nictype2", "hostonlyadapter1",
                                      "hostonlyadapter2", "macaddress1", "macaddress2")}
    except Exception as e:
        return {"error": str(e)}

for vm in VMS:
    res["vms"][vm] = vminfo(vm)
    print(vm, res["vms"][vm])

def kcmd(vm, cmd, t=90):
    return vmrun(vm, cmd, timeout=t).strip()

res["kali1"] = {
    "os": kcmd("ATT-Kali1", ". /etc/os-release; echo $PRETTY_NAME"),
    "java": kcmd("ATT-Kali1", "java -version 2>&1 | head -1"),
    "jmeter": kcmd("ATT-Kali1", "/home/kali/apache-jmeter-5.6.3/bin/jmeter --version 2>&1 | head -3"),
    "ip": kcmd("ATT-Kali1", "ip -br addr; echo ---; ip route"),
    "date": kcmd("ATT-Kali1", "date -u"),
}
print("K1", json.dumps(res["kali1"], ensure_ascii=False))
res["kali2"] = {
    "os": kcmd("ATT-Kali2", ". /etc/os-release; echo $PRETTY_NAME"),
    "java": kcmd("ATT-Kali2", "java -version 2>&1 | head -1"),
    "jmeter": kcmd("ATT-Kali2", "/home/kali/apache-jmeter-5.6.3/bin/jmeter --version 2>&1 | head -3"),
    "ip": kcmd("ATT-Kali2", "ip -br addr; echo ---; ip route"),
    "date": kcmd("ATT-Kali2", "date -u"),
}
print("K2", json.dumps(res["kali2"], ensure_ascii=False))

pf = PF()
def pcmd(c):
    return pf.cmd(c).strip()

res["pfsense"] = {
    "uname": pcmd("uname -a"),
    "version": pcmd("cat /etc/version"),
    "packages": pcmd("pkg info | grep -E 'suricata|haproxy'"),
    "python": pcmd("python3 --version 2>&1"),
    "suricata_v": pcmd("suricata -V 2>&1"),
    "haproxy_v": pcmd("haproxy -v 2>&1 | head -1"),
    "date": pcmd("date -u"),
    "threshold": pcmd("cat /usr/local/etc/suricata/suricata_12985_em0/threshold.config 2>/dev/null"),
    "proc": pcmd("pgrep -fl 'suricata --netmap' | head -3"),
    "wan_ip": pcmd("ifconfig em0 | grep 'inet '"),
    "lan_ip": pcmd("ifconfig em1 | grep 'inet '"),
}
print("PF", json.dumps(res["pfsense"], ensure_ascii=False))

for host, key in (("10.10.20.20", "web1"), ("10.10.20.21", "web2")):
    cmd = ("hostname; . /etc/os-release; echo $PRETTY_NAME; python3 --version; "
           "ip -br addr; date -u; systemctl is-active att-web 2>/dev/null; "
           "systemctl show -p ActiveEnterTimestamp att-web 2>/dev/null")
    res[key] = {"ssh": ssh_web(pf, host, cmd)}
    print(key, res[key]["ssh"][:300])

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", OUT)
