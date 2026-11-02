"""Decode the buttons bots cannot press yet, from a skilled player's input: for each button, its key is
sent to MCC (the player's player, in a test match) and botcore's copy of their action is read every
tick; the bits that change from idle are that button (press-only when they show on the first tick only).
Words that change while idle (input history, timers) are left out. Writes maps/_inputs/<game>.json,
which tools/live_bots.py loads into botcore's button table (native/shared.h hb_btn_entry): the only way
a bot's melee, grenade, reload, crouch, equipment or sprint reaches a game that lacks it natively.

usage: python -I decode_buttons.py button=key [button=key ...] [--hold S] [--dry]
       e.g. melee=q grenade=g reload=r crouch=ctrl equipment=f sprint=shift (the player's binds)
       fire2=rmb --hold 1.5   in a Banshee (or any vehicle with a second weapon): its bomb / fuel rod
buttons: melee grenade reload crouch equipment sprint fire2 cycle (botctl.BTN); keys: mcc_nav.KEYS, or lmb rmb mmb.
       cycle=1 the weapon cycle (the player's key 1: Reach's Banshee fuel rod is cycled to)
Needs MCC focused in a match with botcore s60+; the player's player does each thing once (it melees, throws a
grenade ...).
"""
import datetime
import json
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botctl  # noqa: E402
import mcc_nav  # noqa: E402

SIZE = {2: 0x60, 3: 0x88, 4: 0xA8, 5: 0x240, 6: 0x100, 7: 0x100}      # each game's action
GAME = {v: k for k, v in botctl.GAME_ID.items()}


def snap(m, n):
    buf = botctl.OFF_BIG if n > 0x100 else botctl.OFF_DBG
    return bytes(m[buf:buf + n])


def rows_while(m, n, seconds):
    """Every new copy of the player's action for this long."""
    out, last, t0 = [], None, time.time()
    while time.time() - t0 < seconds:
        seq = struct.unpack_from("<I", m, botctl.OFF_DBG_SEQ)[0]
        if seq != last:
            out.append(snap(m, n))
            last = seq
        time.sleep(0.002)
    return out


def words(b):
    return [struct.unpack_from("<Q", b, k)[0] for k in range(0, len(b) - 7, 8)]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hold = float(sys.argv[sys.argv.index("--hold") + 1]) if "--hold" in sys.argv else 0.4
    pairs = [a.split("=", 1) for a in args if "=" in a]
    if not pairs:
        sys.exit(__doc__)
    from input_replay import key as send_key
    m = botctl.shm()
    game = struct.unpack_from("<I", m, botctl.OFF_GAME)[0]
    if game not in SIZE:
        sys.exit(f"botcore reports game {game}: start a match in Halo 2 / 3 / ODST / Reach / H2A / Halo 4 first")
    n, g = SIZE[game], GAME[game]
    mcc_nav.focus(mcc_nav.mcc_window())
    time.sleep(0.5)
    idle_rows = rows_while(m, n, 1.0)
    if len(idle_rows) < 10:
        sys.exit("botcore is not copying the player's action (is the player in a match, s60 loaded?)")
    base = words(idle_rows[0])
    noisy = [0] * len(base)
    for r in idle_rows[1:]:
        for k, w in enumerate(words(r)):
            noisy[k] |= w ^ base[k]
    path = os.path.join(HERE, "..", "maps", "_inputs", f"{g}.json")
    data = json.load(open(path)) if os.path.exists(path) else {}
    for button, keyname in pairs:
        # a mouse button (rmb: a vehicle's second weapon, fire2=rmb in a Banshee) is pressed where the cursor is, never moved
        mouse_btn = {"lmb": "left", "rmb": "right", "mmb": "middle"}.get(keyname)
        if button not in botctl.BTN or (mouse_btn is None and keyname not in mcc_nav.KEYS):
            print(f"{button}={keyname}: unknown button or key")
            continue
        if mouse_btn:
            from input_replay import send, INPUT, U, MI, INPUT_MOUSE, MOUSE_FLAGS
            press = lambda down: send(INPUT(INPUT_MOUSE, U(mi=MI(0, 0, 0, MOUSE_FLAGS[f"{mouse_btn}_{'down' if down else 'up'}"],
                                                                 0, 0))))
        else:
            scan, ext = mcc_nav.KEYS[keyname]
            press = lambda down: send_key({"scan": scan, "extended": ext, "down": down})
        press(True)
        pressed = rows_while(m, n, hold)
        press(False)
        time.sleep(1.2)                                  # let the melee / throw finish before the next key
        found = []
        pw = [words(r) for r in pressed]
        for k in range(len(base)):
            seen = [(w[k] ^ base[k]) & ~noisy[k] for w in pw]
            any_bits = 0
            for x in seen:
                any_bits |= x
            if not any_bits:
                continue
            held = 0
            for x in seen[2:]:
                held |= x
            first = seen[0] | (seen[1] if len(seen) > 1 else 0)
            press_only = any_bits & ~held                # only on the first tick or two
            if held:
                found.append(dict(off=8 * k, mask=held, press=False))
            if press_only & first:
                found.append(dict(off=8 * k, mask=press_only & first, press=True))
        when = datetime.date.today().isoformat()
        for f in found:
            f["how"] = f"decoded live {when}: key {keyname}, {len(pressed)} ticks held, idle noise excluded"
        print(f"{button}={keyname}: " + (", ".join(f"+0x{f['off']:02x} mask 0x{f['mask']:x}{' (press)' if f['press'] else ''}"
                                                  for f in found) or "no change: wrong key, or not bound in this game"))
        if found:
            data[button] = found
    if "--dry" not in sys.argv:
        json.dump(data, open(path, "w"), indent=1)
        print("wrote", os.path.normpath(path))


if __name__ == "__main__":
    main()
