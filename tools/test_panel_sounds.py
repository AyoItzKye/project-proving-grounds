"""The BOTS panel's sounds: one place picks them from ImGui's own state each frame, and the offline panel
(native/bin/panel_preview.exe) prints them instead of playing them ("sound <kind> <volume>"). In the bot editor at
1920x1080:

1. it opens: one "open", nothing else
2. the Backpack box clicked, then an item in its list: two "select" (a click counts on letting go)
3. Tab x3: two "move" (the first Tab only shows the focus), no "select" (Tab into a text box is a move, not a press)
4. Tab x22 to the Backpack box, Space, Esc: one "select" (the list opens), one "back" (Esc shuts it)
5. a pick whose save fails (--readonly): one "error"
6. the volume at 0: no sound at all; at 25: each sound at 25
7. the sounds themselves (panel_preview --wavs: what overlay.cpp plays): 16-bit mono PCM WAVs at 22.05 kHz; move
   12-16 ms, select 50-58, back 54-62, open 125-135, error 155-165; their peaks under a quarter of full scale and half as
   loud at volume 30 as at 60; the move's tick near 1.9 kHz, the error near 200 Hz (zero crossings)

usage: python -I test_panel_sounds.py      -> "panel sounds OK"
"""
import array
import collections
import os
import stat
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "native", "bin")
EXE = os.path.join(BIN, "panel_preview.exe")
OUT = os.path.join(HERE, "..", "logs", "tmp", "sounds_test.ppm")
PICK = "1386,740;1370,601"                    # the Backpack box; an item in its list
LENGTHS = {"move": (12, 16), "select": (50, 58), "back": (54, 62), "open": (125, 135), "error": (155, 165)}   # ms
PITCH = {"move": (1700, 2100), "error": (170, 260)}                                                        # Hz


def sounds(*args):
    r = subprocess.run([EXE, "--state", "edit2mo", "--size", "1920x1080", "--out", OUT] + list(args), capture_output=True,
                       text=True, timeout=120)
    if r.returncode:
        sys.exit(f"FAIL\npanel_preview {' '.join(args)}: {r.stdout[-300:]}{r.stderr[-300:]}")
    lines = [ln.split() for ln in r.stdout.splitlines() if ln.startswith("sound ")]
    return collections.Counter(ln[1] for ln in lines), {ln[2] for ln in lines}


def main():
    if not os.path.exists(EXE):
        print("panel sounds: skipped (needs native/build_preview.bat)")
        return
    fails = []
    want = lambda label, got, exp: fails.append(f"{label}: {dict(got)} (want {exp})")
    got, _ = sounds()
    if got != {"open": 1}:
        want("it opens", got, "one open, nothing else")
    got, _ = sounds("--click", PICK)
    if got["select"] != 2 or got["move"] or got["back"] or got["error"]:
        want("the box clicked, then an item", got, "two select, no other")
    got, _ = sounds("--keys", "tab*3")
    if got["move"] != 2 or got["select"]:
        want("Tab x3", got, "two move, no select")
    got, _ = sounds("--keys", "tab*22,space,esc")
    if got["select"] != 1 or got["back"] != 1 or got["move"] < 20:
        want("Tab x22, Space, Esc", got, "one select, one back, 20+ move")
    prof = os.path.join(os.environ.get("TEMP", ""), "hb_profiles_preview.ini")
    try:
        got, _ = sounds("--click", PICK, "--readonly")
    finally:
        if os.path.exists(prof):
            os.chmod(prof, stat.S_IWRITE | stat.S_IREAD)
    if got["error"] != 1:
        want("a save that fails", got, "one error")
    got, _ = sounds("--click", PICK, "--sounds", "0")
    if got:
        want("volume 0", got, "no sound")
    got, vols = sounds("--click", PICK, "--sounds", "25")
    if not got or vols != {"25"}:
        fails.append(f"volume 25: sounds at {vols} (want each at 25)")
    peaks = {}
    for vol in (60, 30):
        d = os.path.join(HERE, "..", "logs", "tmp", f"sounds_{vol}")
        os.makedirs(d, exist_ok=True)
        r = subprocess.run([EXE, "--wavs", d, "--sounds", str(vol)], capture_output=True, text=True, timeout=60)
        if r.returncode:
            sys.exit(f"FAIL\n--wavs: {r.stdout}{r.stderr}")
        for name, (lo, hi) in LENGTHS.items():
            with wave.open(os.path.join(d, name + ".wav"), "rb") as w:
                if (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) != (1, 2, 22050, "NONE"):
                    fails.append(f"{name}.wav: {w.getparams()} (want 16-bit mono PCM, 22.05 kHz)")
                    continue
                pcm = array.array("h", w.readframes(w.getnframes()))
            ms = 1000.0 * len(pcm) / 22050
            peak = max(abs(x) for x in pcm)
            peaks[(name, vol)] = peak
            if not lo <= ms <= hi or not 0 < peak < 32767 / 4:
                fails.append(f"{name}.wav at {vol}: {ms:.0f} ms, peak {peak} (want {lo}-{hi} ms, under {32767 // 4})")
            if vol == 60 and name in PITCH:
                crossings = sum(1 for a, b in zip(pcm, pcm[1:]) if (a < 0) != (b < 0))
                hz = crossings / 2 / (len(pcm) / 22050)
                if not PITCH[name][0] <= hz <= PITCH[name][1]:
                    fails.append(f"{name}.wav: about {hz:.0f} Hz (want {PITCH[name][0]}-{PITCH[name][1]})")
    for name in LENGTHS:
        r = peaks.get((name, 30), 0) / max(1, peaks.get((name, 60), 1))
        if not 0.45 <= r <= 0.55:
            fails.append(f"{name}.wav: volume 30 is {r:.2f} of volume 60's peak (want half)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("panel sounds OK (open, select on clicks and keys, moves on Tab, back on Esc, error on a failed save, volume; "
          "the five WAVs well formed, their lengths, loudness and pitch)")


if __name__ == "__main__":
    main()
