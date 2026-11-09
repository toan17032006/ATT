#!/usr/bin/env python3
"""Run a shell command or PHP snippet on the pfSense lab firewall.

Usage: pfcli.py cmd "shell command"   |   pfcli.py php "php code"
"""
import sys
from pf_gui import PF

pf = PF()
ok, code, _ = pf.login()
if not ok:
    print("LOGIN FAILED", code)
    sys.exit(1)

mode = sys.argv[1]
payload = sys.argv[2]
if mode == "cmd":
    print(pf.exec_cmd(payload))
elif mode == "php":
    print(pf.exec_php(payload))
else:
    print("unknown mode")
