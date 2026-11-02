"""Decode the H2 player action: print player 0's raw 0x60-byte action (copied each tick by
botcore's H2 hook) idle and while a key is held, showing the fields that change.

usage: python -I h2_action_probe.py <key> [key ...]     (mcc_nav.py key names: w a s d space e ...)
"""
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botctl  # noqa: E402
import mcc_nav  # noqa: E402
from input_replay import key as send_key  # noqa: E402


def grab(m):
    return bytes(m[botctl.OFF_DBG:botctl.OFF_DBG + 0x60])


def show(tag, b):
    print(tag, " ".join(f"{struct.unpack_from('<I', b, k)[0]:08x}" for k in range(0, 0x60, 4)))


def main():
    m = botctl.shm()
    mcc_nav.focus(mcc_nav.mcc_window())
    idle = grab(m)
    for name in sys.argv[1:]:
        scan, ext = mcc_nav.KEYS[name]
        send_key({"scan": scan, "extended": ext, "down": True})
    time.sleep(0.4)
    held = grab(m)
    for name in sys.argv[1:]:
        scan, ext = mcc_nav.KEYS[name]
        send_key({"scan": scan, "extended": ext, "down": False})
    show("idle", idle)
    show("held", held)
    for k in range(0, 0x60, 4):
        a, b = struct.unpack_from("<I", idle, k)[0], struct.unpack_from("<I", held, k)[0]
        if a != b:
            fa, fb = struct.unpack_from("<f", idle, k)[0], struct.unpack_from("<f", held, k)[0]
            print(f"  +0x{k:02x}: {a:08x} -> {b:08x}   ({fa:.3f} -> {fb:.3f})")


if __name__ == "__main__":
    main()
