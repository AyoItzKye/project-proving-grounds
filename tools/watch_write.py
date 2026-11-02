"""Find the code that writes a game address: hardware write breakpoint via native/bin/watch.dll
(injected as a fresh copy each run) while an optional key is held. Prints watch.log (module+offset
call stacks with hit counts).

usage: python -I watch_write.py <hex address> [key] [ms=4000] [len=4]
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "native", "bin")
sys.path.insert(0, HERE)
import mcc_nav  # noqa: E402
from input_replay import key  # noqa: E402


def main():
    addr = sys.argv[1]
    k = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    ms = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
    ln = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    open(os.path.join(BIN, "watch.txt"), "w").write(f"{addr} {ms} {ln}\n")
    log = os.path.join(BIN, "watch.log")
    if os.path.exists(log):
        os.remove(log)
    dll = os.path.join(BIN, f"watch_{int(time.time())}.dll")
    shutil.copy(os.path.join(BIN, "watch.dll"), dll)
    if k:
        mcc_nav.focus(mcc_nav.mcc_window())
        time.sleep(0.3)
        s, e = mcc_nav.KEYS[k]
        key({"scan": s, "extended": e, "down": True})
    subprocess.run([os.path.join(BIN, "inject.exe"), os.path.abspath(dll), "--force"], capture_output=True)
    time.sleep(ms / 1000 + 1.0)
    if k:
        key({"scan": s, "extended": e, "down": False})
    for _ in range(20):
        if os.path.exists(log):
            break
        time.sleep(0.25)
    print(open(log).read() if os.path.exists(log) else "no watch.log")


if __name__ == "__main__":
    main()
