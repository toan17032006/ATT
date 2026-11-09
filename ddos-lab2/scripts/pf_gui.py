#!/usr/bin/env python3
"""Small pfSense webConfigurator client for the DDoS lab (host -> 127.0.0.1:8443)."""
import re
import sys
import requests

BASE = "http://127.0.0.1:8443"


class PF:
    def __init__(self, user="admin", password="pfsense"):
        self.s = requests.Session()
        self.user = user
        self.password = password

    def token(self, html):
        m = re.search(r'name="__csrf_magic"\s+value="([^"]+)"', html)
        if m:
            return m.group(1)
        m = re.search(r'csrfMagicToken\s*=\s*"([^"]+)"', html)
        return m.group(1) if m else None

    def login(self):
        r = self.s.get(BASE + "/", timeout=10)
        t = self.token(r.text)
        r = self.s.post(BASE + "/index.php", data={
            "usernamefld": self.user,
            "passwordfld": self.password,
            "login": "Login",
            "__csrf_magic": t,
        }, timeout=15, allow_redirects=True)
        ok = "Dashboard" in r.text or "Status" in r.text
        return ok, r.status_code, r.text

    def get(self, path):
        r = self.s.get(BASE + path, timeout=15)
        return r.text

    def post(self, path, data):
        page = self.get(path)
        data = dict(data)
        data["__csrf_magic"] = self.token(page)
        r = self.s.post(BASE + path, data=data, timeout=120)
        return r.text

    def exec_cmd(self, cmd):
        """Run a shell command through Diagnostics > Command Prompt (root)."""
        page = self.get("/diag_command.php")
        t = self.token(page)
        r = self.s.post(BASE + "/diag_command.php", data={
            "__csrf_magic": t,
            "txtCommand": cmd,
            "txtRecallBuffer": "",
            "submit": "EXEC",
        }, timeout=900)
        m = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.S)
        return m.group(1) if m else r.text

    def exec_php(self, code):
        """Run PHP inside pfSense context (config.inc etc. must be required)."""
        page = self.get("/diag_command.php")
        t = self.token(page)
        r = self.s.post(BASE + "/diag_command.php", data={
            "__csrf_magic": t,
            "txtPHPCommand": code,
            "submit": "EXECPHP",
        }, timeout=300)
        m = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.S)
        return m.group(1) if m else r.text


if __name__ == "__main__":
    pf = PF()
    ok, code, text = pf.login()
    print("login", ok, code)
    if len(sys.argv) > 1:
        print(pf.exec_cmd(" ".join(sys.argv[1:])))
