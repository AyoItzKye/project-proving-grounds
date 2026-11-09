"""The launcher's "Bots in MCC" line on Linux / Steam Deck (tools/launcher.py linux_play, from logs/linux_play.txt that
installer/linux/ppg-run.sh writes): a Deck player saw no BOTS tile in any game and nothing said why (Nov 8).
  1. off Linux: None (no line)
  2. no log: never started through the launch option (the line to paste, from a Z: install path)
  3. the last start loaded the bots: ready, even after an earlier start that failed
  4. the last start failed: not ready, its last line shown
And the app windows' tools end with their window (tools/appwindow.py when_closed): stop runs once the window process ends.

usage: python -I test_launcher_linux.py      -> "launcher linux OK"
"""
import os
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import launcher  # noqa: E402
import appwindow  # noqa: E402
from brain import paths  # noqa: E402


def main():
    fails = []
    real_root, real_wine = launcher.ROOT, paths.wine
    with tempfile.TemporaryDirectory() as d:
        launcher.ROOT = d
        paths.wine = lambda: False
        if launcher.linux_play() is not None:
            fails.append("1: a line off Linux")
        paths.wine = lambda: True
        launcher.ROOT = "Z:\\home\\deck\\.local\\share\\project-proving-grounds\\app"
        lp = launcher.linux_play()
        if lp["started"] or lp["option"] != '"/home/deck/.local/share/project-proving-grounds/app/installer/linux/ppg-run.sh" %command%':
            fails.append(f"2: {lp}")
        launcher.ROOT = d
        os.makedirs(os.path.join(d, "logs"))
        log = os.path.join(d, "logs", "linux_play.txt")
        open(log, "w").write("starting MCC with the bots: C:\\mcc.exe\nMCC did not start\n"
                             "starting MCC with the bots: C:\\mcc.exe\nbotcore.dll loaded into MCC (pid 7)\n"
                             "Bots are ready: open Multiplayer > Custom Multiplayer\n")
        lp = launcher.linux_play()
        if not (lp["started"] and lp["ready"]):
            fails.append(f"3: {lp}")
        open(log, "a").write("starting MCC with the bots: C:\\mcc.exe\nMCC did not start\n")
        lp = launcher.linux_play()
        if lp["ready"] or lp["last"] != "MCC did not start":
            fails.append(f"4: {lp}")
    launcher.ROOT, paths.wine = real_root, real_wine
    done = threading.Event()
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.5)"])
    appwindow.when_closed(p, done.set)
    if not done.wait(10):
        fails.append("when_closed: stop never ran after the window process ended")
    appwindow.when_closed(None, lambda: fails.append("when_closed: stop ran with no window"))
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("launcher linux OK")


if __name__ == "__main__":
    main()
