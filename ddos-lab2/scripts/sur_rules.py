#!/usr/bin/env python3
"""Save Suricata custom rules for interface instance 0 (WAN)."""
import sys
from pf_gui import PF

RULES = r'''# Lab custom rules - DDoS mitigation exercise (pfSense + Suricata Inline IPS)
# SID 1001001: hard-block the test URI used in KB1/KB2/KB4
drop http $EXTERNAL_NET any -> $HOME_NET any (msg:"LAB BLOCK GET /ips-test.txt from external"; flow:to_server,established; content:"/ips-test.txt"; http_uri; nocase; classtype:policy-violation; sid:1001001; rev:1;)
# SID 1001002: alert on the load-test URI; rate_filter turns it into a drop (see suppress list)
alert http $EXTERNAL_NET any -> $HOME_NET any (msg:"LAB ALERT /load-test.txt high rate"; flow:to_server,established; content:"/load-test.txt"; http_uri; nocase; classtype:policy-violation; sid:1001002; rev:1;)
'''

pf = PF()
ok, code, _ = pf.login()
if not ok:
    print("LOGIN FAILED", code)
    sys.exit(1)

out = pf.post("/suricata/suricata_rules.php?id=0&openruleset=custom.rules",
              {"customrules": RULES, "save": "Save"})
print("posted, resp len", len(out))
print("SID 1001001 in page:", "1001001" in out)
print("SID 1001002 in page:", "1001002" in out)
