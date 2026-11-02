"""The mod conflict scan (tools/conflicts.py) on a made-up MCC folder:

1. a proxy DLL and an ASI plugin in the launcher or game folder are reported; MCC's own DLLs, other files and other
   folders are not
2. a clean launch moves them aside and restore puts every one back, without overwriting a file that came back since

usage: python -I test_conflicts.py      -> "conflicts OK"
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import conflicts as C  # noqa: E402


def touch(*p):
    os.makedirs(os.path.dirname(os.path.join(*p)), exist_ok=True)
    open(os.path.join(*p), "w").close()


def main():
    fails = []
    mcc = tempfile.mkdtemp()
    game = os.path.join(mcc, "MCC", "Binaries", "Win64")
    for f in ("steam_api64.dll", "bink2w64.dll", "dxgi.dll", "ReShade.ini", "MCC-Win64-Shipping.exe"):
        touch(game, f)
    for f in ("d3dcompiler_47.dll", "SC_DLL.dll", "dinput8.dll", "mod.asi", "mcclauncher.exe"):
        touch(mcc, f)
    touch(mcc, "halo1", "dxgi.dll")                      # (another folder: not loaded from there)
    found = sorted(os.path.basename(p) for p, _ in C.scan(mcc))
    if found != ["dinput8.dll", "dxgi.dll", "mod.asi"]:
        fails.append(f"1. found {found}")
    moved = C.turn_off(C.scan(mcc))
    if len(moved) != 3 or C.scan(mcc) or not os.path.exists(os.path.join(game, "dxgi.dll" + C.OFF)):
        fails.append(f"2. not moved aside: {moved}, still {C.scan(mcc)}")
    touch(mcc, "dinput8.dll")                            # a newer copy came back since: kept, the moved one stays aside
    n = C.restore(mcc)
    if n != 2 or not os.path.exists(os.path.join(game, "dxgi.dll")) or not os.path.exists(os.path.join(mcc, "mod.asi")):
        fails.append(f"2. restore put back {n} (want 2: dxgi.dll and mod.asi)")
    if not os.path.exists(os.path.join(mcc, "dinput8.dll" + C.OFF)):
        fails.append("2. restore overwrote a file that came back")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("conflicts OK (3 clashing files found, moved aside, put back; MCC's own left alone)")


if __name__ == "__main__":
    main()
