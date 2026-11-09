#!/usr/bin/env python3
"""Helpers to drive the DDoS lab VMs and pfSense from the Windows host."""
import os
import subprocess
import time
import json

GC = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
RUNS = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\runs"
EVID = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\evidence"


def vmrun(vm, cmd, user="kali", password="kali", timeout=180, wait=True):
    args = [GC, "guestcontrol", vm, "run",
            "--username", user, "--password", password,
            "--exe", "/bin/bash", "--wait-stdout", "--wait-stderr",
            "--timeout", str(int(timeout * 1000)), "--", "-c", cmd]
    env = dict(os.environ)
    env["MSYS_NO_PATHCONV"] = "1"
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout + 60, env=env)
        return (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        return "TIMEOUT: " + str(e)


def vmstart(vm, cmd, user="kali", password="kali"):
    """Run a command detached (nohup) and return immediately."""
    full = "nohup bash -c " + shquote(cmd) + " >/tmp/lab_last.log 2>&1 & echo $!"
    return vmrun(vm, full, user=user, password=password, timeout=30)


def vmrun_web(vm, cmd, timeout=120):
    return vmrun(vm, cmd, user="ubuntu", password="ubuntu", timeout=timeout)


def shquote(s):
    return "'" + s.replace("'", "'\\''") + "'"


class PF:
    def __init__(self):
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from pf_gui import PF as PFClient
        self.pf = PFClient()
        ok, code, _ = self.pf.login()
        if not ok:
            raise RuntimeError("pfSense login failed: %s" % code)

    def cmd(self, command):
        return self.pf.exec_cmd(command)

    def php(self, code):
        return self.pf.exec_php(code)

    def post(self, path, data):
        return self.pf.post(path, data)

    def get(self, path):
        return self.pf.get(path)


def kdir(name):
    d = os.path.join(RUNS, name)
    os.makedirs(d, exist_ok=True)
    return d


def save(d, name, text):
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(text)


def utcnow():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ssh_web(pf, host, cmd, user="ubuntu", pw="ubuntu"):
    """Run a shell command on a backend VM through pfSense (password SSH over a pty)."""
    import base64
    payload = base64.b64encode(("echo __BEGIN__; " + cmd + " 2>&1; echo __END__").encode()).decode()
    line = ("( sleep 2; echo %s; sleep 6; echo 'echo %s | base64 -d | sh'; sleep 8; echo exit ) | "
            "script -q /dev/null /usr/bin/ssh -o StrictHostKeyChecking=no "
            "-o PubkeyAuthentication=no -o ConnectTimeout=5 %s@%s 2>&1") % (pw, payload, user, host)
    raw = pf.cmd(line)
    if "__BEGIN__" in raw:
        body = raw.split("__BEGIN__", 1)[1]
        body = body.split("__END__", 1)[0]
        return body.strip("\r\n")
    return raw


def stats_csv(pf, label, d):
    raw = pf.cmd("curl -s --max-time 10 'http://127.0.0.1:2200/haproxy/haproxy_stats.php?haproxystats=1;csv'")
    save(d, "stats_%s.csv" % label, raw)
    return parse_stats(raw)


def parse_stats(raw):
    lines = raw.splitlines()
    if not lines or not lines[0].startswith("#"):
        return {}
    header = lines[0][1:].strip().split(",")
    out = {}
    for line in lines[1:]:
        cols = line.split(",")
        if len(cols) < len(header):
            continue
        row = dict(zip(header, cols))
        if row.get("pxname") in ("web_pool_ipvANY", "web_pool") and row.get("svname") in ("web1", "web2"):
            out[row["svname"]] = {k: row.get(k) for k in
                                  ("status", "check_status", "stot", "req_tot", "lastchg", "weight", "addr")}
        if row.get("pxname") in ("web_pool_ipvANY", "web_pool") and row.get("svname") == "BACKEND":
            out["BACKEND"] = {k: row.get(k) for k in ("status", "stot", "req_tot")}
    return out
