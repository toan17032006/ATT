#!/usr/bin/env python3
"""Enable HAProxy internal stats port (for Stats page and CSV)."""
import sys
from pf_gui import PF

pf = PF()
ok, code, _ = pf.login()
if not ok:
    print("LOGIN FAILED", code)
    sys.exit(1)

data = {
    "enable": "yes",
    "maxconn": "5000",
    "nbthread": "2",
    "terminate_on_reload": "yes",
    "hard_stop_after": "",
    "carpdev": "",
    "localstatsport": "2200",
    "localstats_refreshtime": "10",
    "localstats_sticktable_refreshtime": "10",
    "remotesyslog": "",
    "logfacility": "",
    "loglevel": "",
    "log-send-hostname": "",
    "resolver_retries": "",
    "resolver_timeoutretry": "",
    "resolver_holdvalid": "",
    "email_level": "",
    "email_myhostname": "",
    "email_from": "",
    "email_to": "",
    "sslcompatibilitymode": "",
    "ssldefaultdhparam": "",
    "advanced": "",
    "enablesync": "yes",
    "save": "Save",
}
out = pf.post("/haproxy/haproxy_global.php", data)
print("posted, resp len", len(out))
print("stats port in page:", "2200" in out)
