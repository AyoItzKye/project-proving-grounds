"""Start MCC (anti-cheat off) and load botcore, so the Bots tab shows in the Halo CE custom game
lobby. Run from "Play Halo with Bots.bat" in the project folder.

usage: python -I launch.py
"""
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MCC = "MCC-Win64-Shipping.exe"


def running(name):
    sys.path.insert(0, HERE)
    import conflicts
    return conflicts.process_running(name)


def main():
    sys.path.insert(0, ROOT)
    from brain import looks
    looks.profiles()             # this install's 15 bots, drawn on the first run and kept (brain/looks.py)
    if not running(MCC):
        print("starting MCC from Steam (choose the anti-cheat OFF option if Steam asks)")
        os.startfile("steam://rungameid/976730")
    for _ in range(180):
        if running(MCC):
            break
        time.sleep(1)
    else:
        sys.exit("MCC did not start")
    if any(running(n) for n in ("EasyAntiCheat.exe", "EasyAntiCheat_EOS.exe")):
        sys.exit("MCC is running with anti-cheat ON. Quit it and start it with anti-cheat off.")
    time.sleep(15)                                   # let MCC open its window and renderer
    dll = max(glob.glob(os.path.join(ROOT, "native", "bin", "botcore*.dll")), key=os.path.getmtime)
    sys.path.insert(0, HERE)
    import botctl
    exe = botctl.injector()                          # (put back if Windows Defender deleted it)
    if exe is None:
        sys.exit(1)
    r = subprocess.run([exe, os.path.abspath(dll)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    print("Bots are ready: open Multiplayer > Custom Multiplayer > Halo: CE, Halo 2, Halo 2 Anniversary, Halo 3, Halo: Reach or Halo 4; the BOTS tile is next to"
          " START (or press B).")


if __name__ == "__main__":
    main()
