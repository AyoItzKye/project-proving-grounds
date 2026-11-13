"""tools/loading_tag.py, the "Loading mod ..." tag Play shows until botcore's overlay is up: the tag opens a real window
(topmost, no border) with its text, is not "ready" until the overlay's event exists (native/overlay.cpp creates
LOCAL\\PPG_overlay_ready at its first frame), and closes (its window gone) when it does or at its timeout. Windows only
(a Wine run is the same calls); skipped elsewhere.

usage: python -I test_loading_tag.py      -> "loading tag OK"
"""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if os.name != "nt":
    print("loading tag SKIP (Windows only)")
    sys.exit(0)

import loading_tag  # noqa: E402

u, k = ctypes.windll.user32, ctypes.windll.kernel32
tag = loading_tag.LoadingTag()
assert not tag.ready(), "no overlay event yet: not ready"
tag.start()
for _ in range(40):
    if tag.hwnd:
        break
    time.sleep(0.1)
assert tag.hwnd and u.IsWindow(tag.hwnd), "the tag's window exists"
assert u.IsWindowVisible(tag.hwnd), "and is on screen"
ex = u.GetWindowLongW(tag.hwnd, -20)
assert ex & 0x8 and ex & 0x20 and ex & 0x08000000, "topmost, click-through, never takes focus"
b = ctypes.create_unicode_buffer(64)
u.GetWindowTextW(tag.hwnd, b, 64)
assert b.value == "Project Proving Grounds"
assert not tag.wait_ready(0.7), "no overlay: the wait times out"
assert not u.IsWindow(tag.hwnd), "and the window is closed"

tag2 = loading_tag.LoadingTag()
tag2.start()
ev = k.CreateEventW(None, True, True, loading_tag.READY_EVENT)                  # (what the overlay does)
assert tag2.ready(), "the overlay's event: ready"
t0 = time.time()
assert tag2.wait_ready(5), "ready: wait returns True"
assert time.time() - t0 < 2, "at once"
k.CloseHandle(ev)
print("loading tag OK")
