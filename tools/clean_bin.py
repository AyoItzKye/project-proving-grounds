"""Remove old builds from native/bin: every botcore*.dll but the newest two (tools/launch.py injects the newest by
date; the one before may still be loaded in a running MCC), the per-run copies tools/watch_write.py makes of watch.dll
(watch_<n>.dll), filemon's copies, and objects / test programs whose sources are gone. Locked files (loaded in MCC)
are skipped and listed.

usage: python -I clean_bin.py [--dry]
"""
import glob
import os
import sys

BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "native", "bin")
SRC = os.path.join(BIN, "..")


def stale():
    cores = sorted(glob.glob(os.path.join(BIN, "botcore*.dll")), key=os.path.getmtime)
    out = cores[:-2]
    out += glob.glob(os.path.join(BIN, "watch_*.dll")) + glob.glob(os.path.join(BIN, "filemon_*.dll"))
    out += [os.path.join(BIN, f) for f in ("diag2.dll", "filemon2.dll") if os.path.exists(os.path.join(BIN, f))]
    for obj in glob.glob(os.path.join(BIN, "*.obj")):            # an object whose source file is gone
        name = os.path.splitext(os.path.basename(obj))[0]
        if not any(os.path.exists(os.path.join(SRC, name + ext)) for ext in (".cpp", ".c", ".asm")) \
                and not glob.glob(os.path.join(SRC, "third_party", "**", name + ".c*"), recursive=True):
            out.append(obj)
    for exe in glob.glob(os.path.join(BIN, "test_*.exe")):
        if not os.path.exists(os.path.join(SRC, os.path.splitext(os.path.basename(exe))[0] + ".cpp")):
            out.append(exe)
    return out


def old_logs(removed):
    """The removed DLLs' logs: kept (the docs cite them as evidence, e.g. botcore_s83.log), moved to logs/botcore_logs."""
    return [os.path.splitext(d)[0] + ".log" for d in removed
            if d.endswith(".dll") and os.path.exists(os.path.splitext(d)[0] + ".log")]


ARCHIVE = os.path.join(BIN, "..", "..", "logs", "botcore_logs")

if __name__ == "__main__":
    dry = "--dry" in sys.argv
    gone, locked = 0, []
    files = stale()
    for f in files:
        if dry:
            print("would remove", os.path.basename(f))
            continue
        try:
            os.remove(f)
            gone += 1
        except OSError:
            locked.append(os.path.basename(f))
    logs = old_logs(files)
    if not dry:
        os.makedirs(ARCHIVE, exist_ok=True)
        for log in logs:
            os.replace(log, os.path.join(ARCHIVE, os.path.basename(log)))
        print(f"removed {gone} files, moved {len(logs)} logs to logs/botcore_logs"
              + (f"; in use, kept: {', '.join(locked)}" if locked else ""))
    else:
        print(f"would move {len(logs)} logs to logs/botcore_logs")
