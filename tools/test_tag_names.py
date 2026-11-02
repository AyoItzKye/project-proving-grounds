"""The tag name reader (tools/reach_tag_names.py) on the installed game:

1. every saved name list (maps/_shapes/<game>_tags_<map>.json) matches a fresh read of its .map file, entry by entry
2. every .map file of Reach, Halo 3, Halo 4 and Halo 2 Anniversary has a readable table with globals\\globals in it

usage: python -I test_tag_names.py      -> "tag names OK"  (SKIP without MCC installed)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reach_tag_names as T  # noqa: E402


def main():
    if not os.path.isdir(os.path.join(T.MCC, "haloreach", "maps")):
        print(f"SKIP test_tag_names.py: needs MCC's map files ({T.MCC})")
        return
    fails = []
    same, bad = T.check() if os.path.isdir(T.OUT) else (0, [])
    if bad:
        fails.append(f"1. saved lists differ: {bad}")
    files = 0
    for game, folder in T.GAME_DIR.items():
        d = os.path.join(T.MCC, folder, "maps")
        for fn in sorted(os.listdir(d)) if os.path.isdir(d) else ():
            if not fn.endswith(".map") or fn in ("shared.map", "campaign.map"):
                continue
            files += 1
            try:
                names = T.names_of(os.path.join(d, fn))
            except SystemExit as e:
                fails.append(f"2. {game} {fn}: {e}")
                continue
            if "globals\\globals" not in names:
                fails.append(f"2. {game} {fn}: no globals\\globals among {len(names)} names")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"tag names OK ({same} saved lists match, {files} map files read)")


if __name__ == "__main__":
    main()
