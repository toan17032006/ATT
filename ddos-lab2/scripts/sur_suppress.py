#!/usr/bin/env python3
"""Create the Suricata threshold/suppress list containing the rate_filter."""
import sys
from pf_gui import PF

THRESH = r'''# Rate filter: 20 hits of SID 1001002 within 10 s from one source -> DROP 15 s
rate_filter gen_id 1, sig_id 1001002, track by_src, count 20, seconds 10, new_action drop, timeout 15
'''

pf = PF()
ok, code, _ = pf.login()
if not ok:
    print("LOGIN FAILED", code)
    sys.exit(1)

out = pf.post("/suricata/suricata_suppress_edit.php",
              {"name": "lab_thresholds", "descr": "LAB DDoS rate_filter",
               "suppresspassthru": THRESH, "save": "Save"})
print("posted, resp len", len(out))
print("lab_thresholds in page:", "lab_thresholds" in out)
