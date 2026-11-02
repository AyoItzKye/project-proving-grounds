"""Replays recorded input (keys by scan code, mouse clicks at a screen position) with the original timing; mouse is what
tools/mcc_click.py clicks with. (The recorder, input_logger.py, was removed: click navigation replaced it.) Refuses to
run while Easy Anti-Cheat is running.

usage: python -I input_replay.py <logs/menu_path_.../events.jsonl> [--speed 1.0] [--until N]
       (--until stops after event N, to replay only the start of a path)
"""
import argparse
import ctypes as C
import ctypes.wintypes as W
import json
import os
import subprocess
import time

user32 = C.WinDLL("user32", use_last_error=True)
INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE = 0x1, 0x2, 0x8
MOUSE_FLAGS = {"left_down": 0x2, "left_up": 0x4, "right_down": 0x8, "right_up": 0x10,
               "middle_down": 0x20, "middle_up": 0x40}


class KI(C.Structure):
    _fields_ = [("wVk", W.WORD), ("wScan", W.WORD), ("dwFlags", W.DWORD), ("time", W.DWORD), ("extra", C.c_size_t)]


class MI(C.Structure):
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("data", W.DWORD), ("dwFlags", W.DWORD), ("time", W.DWORD), ("extra", C.c_size_t)]


class U(C.Union):
    _fields_ = [("ki", KI), ("mi", MI), ("pad", C.c_byte * 32)]


class INPUT(C.Structure):
    _fields_ = [("type", W.DWORD), ("u", U)]


def send(inp):
    if user32.SendInput(1, C.byref(inp), C.sizeof(INPUT)) != 1:
        raise OSError(C.get_last_error())


def key(ev):
    flags = KEYEVENTF_SCANCODE | (0 if ev["down"] else KEYEVENTF_KEYUP) | (KEYEVENTF_EXTENDEDKEY if ev["extended"] else 0)
    send(INPUT(INPUT_KEYBOARD, U(ki=KI(0, ev["scan"], flags, 0, 0))))


def mouse(ev):
    if ev["action"] == "wheel":
        send(INPUT(INPUT_MOUSE, U(mi=MI(0, 0, C.c_uint32(ev["wheel"]).value, 0x800, 0, 0))))
        return
    user32.SetCursorPos(ev["x"], ev["y"])
    send(INPUT(INPUT_MOUSE, U(mi=MI(0, 0, 0, MOUSE_FLAGS[ev["action"]], 0, 0))))


def _thumb(img):
    import numpy as np
    return np.asarray(img.convert("L").resize((120, 50)), dtype=np.float32)


def wait_for_screen(shot_path, prev_shot=None, timeout=45.0, threshold=16.0):
    """Wait until the screen looks like the recorded screenshot, is closer to it than to the
    previous step's screenshot (so a splash screen is not mistaken for the title screen), and
    has stopped changing. Loading times vary; this keeps each key on the right menu.
    Returns the final difference (mean absolute grey level, 0..255)."""
    import numpy as np
    from PIL import Image, ImageGrab
    want = _thumb(Image.open(shot_path))
    before = _thumb(Image.open(prev_shot)) if prev_shot else None
    distinct = before is not None and float(np.abs(before - want).mean()) > 5.0
    t_end, prev, diff = time.time() + timeout, None, 999.0
    while time.time() < t_end:
        now = _thumb(ImageGrab.grab(all_screens=False))
        diff = float(np.abs(now - want).mean())
        moved_on = not distinct or diff < float(np.abs(now - before).mean()) - 1.0
        still = prev is not None and float(np.abs(now - prev).mean()) < 3.0
        if diff < threshold and moved_on and still:
            return diff
        prev = now
        time.sleep(0.25)
    return diff


def anticheat_running():
    out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    return "easyanticheat" in out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--until", type=int, default=None)
    ap.add_argument("--from-time", type=float, default=0.0, help="skip events recorded before this time (s)")
    ap.add_argument("--sync", action="store_true", help="wait for each recorded screen before pressing")
    a = ap.parse_args()
    if anticheat_running():
        raise SystemExit("Easy Anti-Cheat is running: not sending any input.")
    evs = [json.loads(l) for l in open(a.events)]
    evs = [e for e in evs if e["type"] in ("key", "mouse") and not e.get("injected") and e["t"] >= a.from_time]
    if a.until is not None:
        evs = evs[:a.until]
    base = os.path.dirname(os.path.abspath(a.events))
    t0, start = time.perf_counter(), evs[0]["t"] if evs else 0
    last_shot = None
    for n, e in enumerate(evs, 1):
        if a.sync and e.get("shot"):
            d = wait_for_screen(os.path.join(base, e["shot"]), last_shot)
            last_shot = os.path.join(base, e["shot"])
            print(f"step {n}: {e.get('action') or e.get('vk')} on {e['shot']} (screen diff {d:.1f})", flush=True)
            time.sleep(0.3)
            t0, start = time.perf_counter(), e["t"]   # re-anchor timing at each matched screen
        wait = (e["t"] - start) / a.speed - (time.perf_counter() - t0)
        if wait > 0:
            time.sleep(wait)
        key(e) if e["type"] == "key" else mouse(e)
    print(f"replayed {len(evs)} events")


if __name__ == "__main__":
    main()
