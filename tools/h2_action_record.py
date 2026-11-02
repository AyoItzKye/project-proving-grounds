"""Record player 0's H2 / H3 action every game tick (botcore copies it to the debug view) while a key is
tapped, and print each tick's words that differ from idle: shows press-only (edge) bits that a
held-key snapshot (h2_action_probe.py) misses.

usage: python -I h2_action_record.py <key> [hold seconds, default 0.15]
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


def main():
    m = botctl.shm()
    game = struct.unpack_from("<I", m, botctl.OFF_GAME)[0]
    n = {3: 0x88, 4: 0xA8, 5: 0x240, 6: 0x100, 7: 0x100}.get(game, 0x60)   # H3 / Reach / ODST / H2 action size
    buf = botctl.OFF_BIG if n > 0x100 else botctl.OFF_DBG     # big actions: the dbg_big copy
    mcc_nav.focus(mcc_nav.mcc_window())
    time.sleep(0.3)
    idle = bytes(m[buf:buf + n])
    scan, ext = mcc_nav.KEYS[sys.argv[1]]
    hold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
    seq0 = struct.unpack_from("<I", m, botctl.OFF_DBG_SEQ)[0]
    rows, last, t0, released = [], seq0, time.time(), False
    send_key({"scan": scan, "extended": ext, "down": True})
    while time.time() - t0 < hold + 0.6:
        if not released and time.time() - t0 > hold:
            send_key({"scan": scan, "extended": ext, "down": False})
            released = True
        seq = struct.unpack_from("<I", m, botctl.OFF_DBG_SEQ)[0]
        if seq != last:
            rows.append((seq, bytes(m[buf:buf + n])))
            last = seq
        time.sleep(0.002)
    if not released:
        send_key({"scan": scan, "extended": ext, "down": False})
    for seq, b in rows:
        diff = [f"+0x{k:02x}:{struct.unpack_from('<I', b, k)[0]:08x}" for k in range(0, n, 4)
                if b[k:k + 4] != idle[k:k + 4]]
        print(seq - seq0, " ".join(diff))


if __name__ == "__main__":
    main()
