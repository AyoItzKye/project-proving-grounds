"""Many live QC matches in a row (tools/live_qc.py), from a plan file of lines "map# category# variant# label". Each
match: pick, play MINUTES, end, one line in logs/live_qc.md. A failed match is retried once. Stops early if MCC is
gone. the player's input is never needed; never run while he plays (check the cursor first).

usage: python -I live_qc_batch.py <plan.txt> [--minutes 4] [--from N] [--game h3]
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def mcc_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq MCC-Win64-Shipping.exe"], capture_output=True, text=True).stdout
    return "MCC-Win64-Shipping" in out


def main():
    a = sys.argv[1:]
    plan = [l.split(None, 3) for l in open(a[0], encoding="utf-8") if l.strip() and not l.startswith("#")]
    minutes = a[a.index("--minutes") + 1] if "--minutes" in a else "4"
    start = int(a[a.index("--from") + 1]) if "--from" in a else 1
    for k, row in enumerate(plan, 1):
        if k < start:
            continue
        m, c, v, label = row[0], row[1], row[2], row[3].strip() if len(row) > 3 else ""
        for attempt in (1, 2):
            if not mcc_running():
                print("MCC is not running: stop", flush=True)
                return
            r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "live_qc.py"), m, c, v, "--minutes", minutes,
                                "--label", f"{k}: {label}"] + (a[a.index("--game"):a.index("--game") + 2] if "--game" in a else []),
                               capture_output=True, text=True, timeout=3600)
            print(f"[{k}/{len(plan)}] {label}: {(r.stdout + r.stderr).strip()[-300:]}", flush=True)
            if r.returncode == 0:
                break
            if r.returncode == 2:            # not in (or not back in) the Reach lobby: no more clicks at all
                print("stopped: MCC is not in the Reach lobby", flush=True)
                return
            time.sleep(10)


if __name__ == "__main__":
    main()
