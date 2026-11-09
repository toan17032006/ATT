#!/usr/bin/env python3
"""Summarize JTL and backend logs of KB1/KB3/KB4 into report_data.json."""
import csv, json, os, re, glob
from datetime import datetime, timezone

RUNS = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\runs"
OUT = r"C:\Users\Admin\Desktop\ATT\ddos-lab2\report_data.json"

def pct(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]

def jtl(path):
    rows = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    if not rows:
        return None
    el = [int(x["elapsed"]) for x in rows]
    ok = [int(x["elapsed"]) for x in rows if x.get("responseCode") == "200" and x.get("success", "true") == "true"]
    ts = [int(x["timeStamp"]) for x in rows]
    codes = {}
    for x in rows:
        c = x.get("responseCode") or "none"
        codes[c] = codes.get(c, 0) + 1
    start = min(ts)
    end = max(ts) + max(el)
    return {
        "samples": len(rows),
        "errors": sum(1 for x in rows if x.get("success", "true") != "true"),
        "avg_ms": round(sum(el) / len(el), 1),
        "min_ms": min(el), "max_ms": max(el),
        "p95_ms": pct(el, 95), "p95_ok_ms": pct(ok, 95),
        "start_utc": datetime.fromtimestamp(start / 1000, timezone.utc).strftime("%H:%M:%S"),
        "end_utc": datetime.fromtimestamp(end / 1000, timezone.utc).strftime("%H:%M:%S"),
        "start_iso": datetime.fromtimestamp(start / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_iso": datetime.fromtimestamp(end / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_s": round((end - start) / 1000.0, 1),
        "throughput": round(len(rows) / ((end - start) / 1000.0), 2) if end > start else None,
        "codes": codes,
        "ok_p95": pct(ok, 95), "ok_avg": round(sum(ok) / len(ok), 1) if ok else None,
    }

def backend(path, run_tag, uri="load-test.txt"):
    if not os.path.exists(path):
        return None
    txt = open(path, encoding="utf-8", errors="replace").read()
    lines = [l for l in txt.splitlines() if uri in l and run_tag in l]
    k1 = sum(1 for l in lines if "src=K1" in l)
    k2 = sum(1 for l in lines if "src=K2" in l)
    return {"total": len(lines), "k1": k1, "k2": k2, "sample": lines[:3]}

data = {}
for run in ("KB1_R1", "KB3_R1", "KB4_R1"):
    d = os.path.join(RUNS, run)
    tag = run.split("_")[0]
    data[run] = {
        "K1": jtl(os.path.join(d, run + "_K1.jtl")) if os.path.exists(os.path.join(d, run + "_K1.jtl")) else None,
        "K2": jtl(os.path.join(d, run + "_K2.jtl")) if os.path.exists(os.path.join(d, run + "_K2.jtl")) else None,
        "web1": backend(os.path.join(d, "backend_web1.txt"), tag),
        "web2": backend(os.path.join(d, "backend_web2.txt"), tag),
    }
    print(run, json.dumps(data[run], ensure_ascii=False)[:300])

# KB2 backend evidence
d = os.path.join(RUNS, "KB2_R1")
k2 = {}
for f in glob.glob(os.path.join(d, "curl_*.txt")):
    k2[os.path.basename(f)] = open(f, encoding="utf-8", errors="replace").read()[-600:]
data["KB2_R1"] = {"curls": k2}
data["KB4_R1"]["alerts_window"] = open(os.path.join(RUNS, "KB4_R1", "alerts_window.txt"), encoding="utf-8", errors="replace").read()
data["KB3_R1"]["alerts_window"] = open(os.path.join(RUNS, "KB3_R1", "alerts_window.txt"), encoding="utf-8", errors="replace").read()

json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", OUT)
