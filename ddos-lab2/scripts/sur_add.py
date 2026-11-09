#!/usr/bin/env python3
"""Create a Suricata instance on WAN in Inline IPS mode via webConfigurator POST."""
import re
import sys
from pf_gui import PF

# Usage: sur_add.py [threshold-list-name|none]
suppress = sys.argv[1] if len(sys.argv) > 1 else "lab_thresholds"
if suppress.lower() == "none":
    suppress = ""

pf = PF()
ok, code, _ = pf.login()
if not ok:
    print("LOGIN FAILED", code)
    sys.exit(1)

html = pf.get("/suricata/suricata_interfaces_edit.php?id=0")
form = {
    "id": "0",
    "action": "",
    "enable": "on",
    "interface": "wan",
    "descr": "WAN inline IPS",
    "ips_mode": "ips_mode_inline",
    "ips_netmap_threads": "1",
    "blockoffenders": "on",
    "blockoffendersip": "both",
    "blockoffenderskill": "on",
    "block_drops_only": "on",
    "runmode": "autofp",
    "autofp_scheduler": "hash",
    "detect_eng_profile": "medium",
    "mpm_algo": "auto",
    "spm_algo": "auto",
    "sgh_mpm_context": "auto",
    "inspect_recursion_limit": "3000",
    "max_pending_packets": "1024",
    "delayed_detect": "on",
    "intf_promisc_mode": "on",
    "intf_snaplen": "1518",
    "suppresslistname": suppress,
    "enable_stats_collection": "on",
    "stats_upd_interval": "10",
    "enable_eve_log": "on",
    "eve_output_type": "regular",
    "eve_log_alerts": "on",
    "eve_log_alerts_http": "on",
    "eve_log_alerts_metadata": "on",
    "eve_log_alerts_packet": "on",
    "eve_log_alerts_payload": "on",
    "eve_log_drops": "on",
    "eve_log_alert_drops": "on",
    "eve_log_http": "on",
    "eve_log_dns": "on",
    "eve_log_flow": "on",
    "eve_log_stats": "on",
    "eve_log_stats_totals": "on",
    "eve_log_ssh": "on",
    "eve_log_tls": "on",
    "eve_log_files": "on",
    "enable_verbose_logging": "on",
    "alertsystemlog": "on",
    "alertsystemlog_facility": "local1",
    "alertsystemlog_priority": "notice",
    "save": "Save",
}
out = pf.post("/suricata/suricata_interfaces_edit.php?id=0", form)
print("posted, resp len", len(out))
for pat in (r'id="inputerrors"[\s\S]{0,600}', r'class="alert[^"]*"[\s\S]{0,300}'):
    m = re.search(pat, out)
    if m:
        print("MSG:", re.sub(r"<[^>]+>", " ", m.group(0))[:500])
print("has 'Inline':", "Inline" in out, "| has 'WAN inline IPS':", "WAN inline IPS" in out)
