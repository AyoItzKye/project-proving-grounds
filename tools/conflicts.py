"""Other mods that can clash with Project Proving Grounds, found in the MCC folder, and a clean launch without them.

What can clash: a DLL another mod drops beside MCC's program so Windows loads it into the game (a "proxy" DLL named
like a system one: dxgi.dll, d3d11.dll, dinput8.dll, version.dll ... ReShade, Special K, ASI loaders, other injectors
and overlays), and ASI plugin files. They hook the same game and the same drawing as this mod. MCC's own DLLs are
known and never reported. Steam Workshop mods are only counted: MCC loads them only when started with mods, and they
change maps and game files, not the game's code.

A clean launch moves the clashing files aside (renamed <file>.ppg-off) for one session; restore() puts them back,
and the launcher does so when MCC has closed (and at its next start, if the PC was turned off in between).

usage: python -I conflicts.py              the report
       python -I conflicts.py --off         move them aside (before starting MCC)
       python -I conflicts.py --restore     put them back
       python -I conflicts.py --restore-after-mcc   put them back once MCC has started and closed again
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import paths  # noqa: E402  (where MCC is)

OFF = ".ppg-off"
# names Windows would load from the program's folder in place of a system DLL: the usual proxy loaders
PROXY = {"dxgi.dll", "d3d11.dll", "d3d12.dll", "d3d9.dll", "d3d10.dll", "dinput8.dll", "version.dll", "winmm.dll",
         "xinput1_3.dll", "xinput1_4.dll", "xinput9_1_0.dll", "dsound.dll", "opengl32.dll", "winhttp.dll", "wininet.dll",
         "msimg32.dll", "dbghelp.dll", "uxtheme.dll", "bink2w64_.dll"}
# the folders Windows loads them from: the launcher's and the game's
FOLDERS = ("", os.path.join("MCC", "Binaries", "Win64"))


def scan(mcc=None):
    """[(path, why)] of the files that can clash, in MCC's launcher and game folders."""
    mcc = mcc or paths.mcc()
    if not mcc:
        return []
    out = []
    for sub in FOLDERS:
        d = os.path.join(mcc, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            low = f.lower()
            if low in PROXY:
                out.append((os.path.join(d, f), "a DLL other mods put beside the game so it loads into it"))
            elif low.endswith(".asi"):
                out.append((os.path.join(d, f), "an ASI plugin (loaded into the game by an ASI loader)"))
    return out


def workshop_count():
    """How many Steam Workshop items for MCC are subscribed (MCC loads them only when started with mods)."""
    for common in paths.steam_commons():
        d = os.path.join(os.path.dirname(common), "workshop", "content", "976730")
        if os.path.isdir(d):
            return len(os.listdir(d))
    return 0


def turn_off(found=None):
    """Moves every clashing file aside for one session; returns the files moved."""
    moved = []
    for p, _ in (found if found is not None else scan()):
        os.replace(p, p + OFF)
        moved.append(p)
    return moved


def restore(mcc=None):
    """Puts back every file a clean launch moved aside; returns how many."""
    mcc = mcc or paths.mcc()
    n = 0
    for sub in FOLDERS if mcc else ():
        for p in glob.glob(os.path.join(mcc, sub, "*" + OFF)):
            orig = p[:-len(OFF)]
            if not os.path.exists(orig):
                os.replace(p, orig)
                n += 1
    return n


def report():
    found = scan()
    lines = [f"{len(found)} file(s) in the MCC folder can clash with the bots"]
    lines += [f"  {os.path.relpath(p, paths.mcc())}: {why}" for p, why in found]
    w = workshop_count()
    if w:
        lines.append(f"{w} Steam Workshop item(s) subscribed for MCC (only loaded when MCC starts with mods)")
    return "\n".join(lines)


def mcc_running():
    import subprocess
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq MCC-Win64-Shipping.exe"], capture_output=True,
                         text=True).stdout
    return "mcc-win64-shipping.exe" in out.lower()


def restore_after_mcc(start_wait=180):
    """Waits for MCC to start (up to start_wait s) and then to close, then puts the moved files back."""
    import time
    for _ in range(start_wait):
        if mcc_running():
            break
        time.sleep(1)
    while mcc_running():
        time.sleep(5)
    return restore()


if __name__ == "__main__":
    if "--off" in sys.argv:
        print(f"moved aside: {len(turn_off())}")
    elif "--restore-after-mcc" in sys.argv:
        print(f"put back: {restore_after_mcc()}")
    elif "--restore" in sys.argv:
        print(f"put back: {restore()}")
    else:
        print(report())
