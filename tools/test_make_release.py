"""The release builder's rules and privacy scan (tools/make_release.py):

1. where each kind of file goes: the source and hand-made map knowledge to the release; height maps, top-down pictures,
   glass masks and Forge shapes to the map pack; logs, LiDAR scans, learned files, Forge layouts, raw geometry,
   decompiled code, binaries, the development log and the GPL map tools left out; our Ghidra scripts kept
2. the scan finds personal terms (made-up ones here: the real ones live in .private_terms, never committed), an e-mail
   address, a user folder and this PC's drive paths, and passes clean text, generic Windows folders and
   environment-variable paths

usage: python -I test_make_release.py      -> "make_release OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_release as R  # noqa: E402


def main():
    fails = []
    want = {
        "brain/bot.py": "release", "tools/live_bots.py": "release", "tools/test_scaling.py": "release",
        "native/botcore.cpp": "release", "native/third_party/imgui/imgui.cpp": "release", "README.md": "release",
        "maps/reach_30_settlement/callouts.json": "release", "maps/reach_30_settlement/objects.json": "release",
        "maps/_inputs/reach.json": "release", "maps/_human/reference.json": "release",
        "docs/research/02-halo-ai-engine-and-map-data.md": "release", "ghidra/scripts/FindRefs.java": "release",
        "maps/reach_30_settlement/heightmap.npz": "pack", "maps/reach_30_settlement/topdown.png": "pack",
        "maps/reach_30_settlement/glass.json": "pack", "maps/_shapes/reach_tags_45_aftship.json": "pack",
        "maps/reach_30_settlement/lidar.json": None, "maps/reach_30_settlement/nav_learned.json": None,
        "maps/reach_35_island/variants/v3977bae2/lidar.json": None, "maps/bloodgulch/bsp.obj": None,
        "maps/bloodgulch/scenario.xml": None, "logs/drive_h2a_pass.jsonl": None, "native/bin/botcore_s153.dll": None,
        "ghidra/halo1_main.c": None, "tools/bsp2obj/Program.cs": None, "docs/HANDOFF.md": None,
        "docs/oct31/audit.md": None, "Play Halo with Bots.bat": None, "tools/__pycache__/bot.cpython-314.pyc": None,
        "tools/backup.py": None, "tools/view_art/maps/h3_construct.jpg": None, "tools/view_art/games/h3.png": None,
        "tools/view_art/names.json": "release", "LICENSE.md": "release", "NOTICE.md": "release",
        "CONTRIBUTING.md": "release", "SECURITY.md": "release", "CODE_OF_CONDUCT.md": "release",
        "requirements.txt": "release", "installer/ProjectProvingGrounds.iss": "release",
    }
    got = {p: R.where(p) for p in want}
    bad = {p: (got[p], w) for p, w in want.items() if got[p] != w}
    if bad:
        fails.append(f"1. misfiled (got, want): {bad}")
    terms = ["SomeGamerTag", "0x0009DEADBEEF0001"]
    dirty = ("gamertag somegamertag", "id 0x0009deadbeef0001", "mail someone@" + "gmail.com",
             "const uint64_t id = 0x0009" + "ABCDEF012345ull;",
             "path C:" + chr(92) + "Users" + chr(92) + "Jo" + chr(92) + "notes",
             "drive A:" + chr(92) + "Steam" + chr(92) + "steamapps")
    for text in dirty:
        found, _ = R.scan_text(text, terms)
        if not found:
            fails.append(f"2. not caught: {text!r}")
    clean = ("C:" + chr(92) + "Users" + chr(92) + "Public" + chr(92) + "x", "%USERPROFILE%/AppData/LocalLow/MCC",
             "C:" + chr(92) + "Program Files (x86)" + chr(92) + "Steam", "a skilled player's baseline",
             "os.path.expanduser('~')", "made-up id 0x0009000012345678ull")
    for text in clean:
        found, _ = R.scan_text(text, terms)
        if found:
            fails.append(f"2. false alarm on {text!r}: {found}")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"make_release OK ({len(want)} paths filed, {len(dirty)} leaks caught, {len(clean)} clean)")


if __name__ == "__main__":
    main()
