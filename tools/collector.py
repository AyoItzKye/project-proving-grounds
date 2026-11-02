"""Data collector (the BOTS panel's "Data collector"; the Observer then shows, tools/player_stats.py). tools/live_bots.py
keeps one per match when botcore.ini has collector=1 (tools/play.py passes --collect on) and it writes
logs/collect_<map>_<date>-<time>.jsonl:

  {"t", "collect": "start", "map", "game", "keys": {"<vk>": name}}                     once
  {"t", "p": [[id, team, alive, x, y, z, yaw, pitch, shield, health, riding, flag, bot, (people only:) crosshair,
              ride], ...]}                                   everyone, every tick (brain/tracefmt.py crosshair, seat_of)
  {"t", "id", "wpn", "inv", "ammo", "mag", "eq", "ab", "uz"}    a person's guns, rounds, equipment, zoom: on change
  {"t", "key": name, "vk", "down": 1 | 0}                     a bound key or a controller button going down or up
                                                              (read 200 times a second; a controller's: "pad A" ...)

Keys: only keys bound in MCC's own settings (GameUserSettings.ini), and only while MCC is the window in front:
nothing typed anywhere else is read. Controller buttons (XInput, any pad) the same: only while MCC is in front.
Mouse look is read from the game (yaw, pitch), not the mouse.
"""
import ctypes
import json
import os
import re
import threading
import time

SETTINGS = os.path.join(os.environ.get("LOCALAPPDATA", ""), "..", "LocalLow", "MCC", "Saved", "Config",
                        "WindowsNoEditor", "GameUserSettings.ini")
# MCC's AbstractButton numbers in CustomKeyboardMouseMappingV2, named where every game's set binds the same key and
# that key is the player's (melee Q, grenade F, use E) or MCC's default; the rest keep their key's name
ACTION = {0: "jump", 2: "action", 3: "reload", 5: "melee", 7: "grenade", 8: "fire", 9: "crouch", 10: "zoom",
          16: "forward", 17: "back", 18: "left", 19: "right", 20: "scores"}
VK_NAME = {1: "LMB", 2: "RMB", 4: "MMB", 5: "Mouse4", 6: "Mouse5", 8: "Backspace", 9: "Tab", 13: "Enter", 16: "Shift",
           17: "Ctrl", 18: "Alt", 20: "CapsLock", 27: "Esc", 32: "Space", 37: "Left", 38: "Up", 39: "Right",
           40: "Down", 46: "Delete", 160: "LShift", 161: "RShift", 162: "LCtrl", 163: "RCtrl", 164: "LAlt",
           165: "RAlt", 186: ";", 187: "=", 188: ",", 189: "-", 190: ".", 191: "/", 192: "~"}


# a controller's buttons (XInput wButtons bits; the triggers as bits 16-17 past XINPUT_GAMEPAD_TRIGGER_THRESHOLD), as
# key events with vk PAD_VK + bit
PAD_VK = 0x10000
PAD = {0: "Up", 1: "Down", 2: "Left", 3: "Right", 4: "Start", 5: "Back", 6: "LS", 7: "RS", 8: "LB", 9: "RB",
       12: "A", 13: "B", 14: "X", 15: "Y", 16: "LT", 17: "RT"}
TRIGGER = 30


class _Pad(ctypes.Structure):
    _fields_ = [("packet", ctypes.c_uint32), ("buttons", ctypes.c_uint16), ("lt", ctypes.c_uint8), ("rt", ctypes.c_uint8),
                ("lx", ctypes.c_int16), ("ly", ctypes.c_int16), ("rx", ctypes.c_int16), ("ry", ctypes.c_int16)]


def key_name(vk):
    if vk >= PAD_VK:
        return "pad " + PAD.get(vk - PAD_VK, str(vk - PAD_VK))
    return VK_NAME.get(vk) or (chr(vk) if 48 <= vk <= 90 else f"vk{vk}")


def pads():
    """() -> the buttons held on every connected controller, PAD bits OR-ed; None without XInput. Pads not plugged in
    are looked for every 2 s (asking an empty slot every pass is slow)."""
    dll = None
    for name in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            dll = getattr(ctypes.windll, name)
            break
        except (OSError, AttributeError):
            continue
    if dll is None:
        return None
    st, live, seen = _Pad(), [], [-9.0]

    def held():
        if time.monotonic() - seen[0] > 2.0:
            seen[0], live[:] = time.monotonic(), [k for k in range(4) if dll.XInputGetState(k, ctypes.byref(st)) == 0]
        mask = 0
        for k in live:
            if dll.XInputGetState(k, ctypes.byref(st)) == 0:
                mask |= st.buttons | (st.lt > TRIGGER) << 16 | (st.rt > TRIGGER) << 17
        return mask
    return held


def read_binds(text):
    """{vk: name} for every key bound in any game's set: its action where ACTION names one, else the key."""
    out = {}
    for ab, vks in re.findall(r"AbstractButton=(\d+),((?:VirtualKeyCodes\[\d\]=\d+,?)+)", text):
        act = ACTION.get(int(ab))
        for vk in (int(v) for v in re.findall(r"=(\d+)", vks)):
            if vk and (vk not in out or (act and out[vk] == key_name(vk))):
                out[vk] = act or key_name(vk)
    return out


def binds(path=SETTINGS):
    try:
        found = read_binds(open(path, encoding="utf-8", errors="replace").read())
    except OSError:
        found = {}
    # no settings file (or no binds in it): MCC's defaults as the player's file had them on
    return found or {32: "jump", 69: "action", 82: "reload", 81: "melee", 70: "grenade", 1: "fire", 162: "crouch",
                     2: "zoom", 87: "forward", 83: "back", 65: "left", 68: "right", 160: "LShift", 49: "1", 50: "2"}


def crouch_held(pid, state=None, front=None, keymap=None):
    """-> True while the person holds a key bound to crouch with MCC (process pid) the window in front: the game reads
    no crouch for players, and the bots shot at a crouched man's standing head height. MCC's crouch is held.
    ponytail: keyboard only; a controller's crouch needs its binding read."""
    vks = [vk for vk, name in (keymap or binds()).items() if name == "crouch"] or [162]
    if state is None:
        user32 = ctypes.windll.user32
        state = lambda vk: bool(user32.GetAsyncKeyState(vk) & 0x8000)   # noqa: E731
    front = front or (lambda: in_front(pid))
    return lambda: front() and any(state(vk) for vk in vks)


def in_front(pid):
    """Whether process pid owns the window in front."""
    user32 = ctypes.windll.user32
    p = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(p))
    return p.value == pid


class Keys(threading.Thread):
    """Polls the bound keys while MCC (process pid) is the window in front; edges into events [(t, vk, down)].
    Out of focus every key reads up, so a key held when you alt-tab ends there. A controller's buttons the same
    (pad: () -> PAD bits held, collector.pads)."""
    def __init__(s, vks, pid, clock, period=0.005, state=None, front=None, pad=None):
        super().__init__(daemon=True)
        s.vks, s.pid, s.clock, s.period = sorted(vks), pid, clock, period
        s.events, s.lock, s.done = [], threading.Lock(), False
        user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
        s.state = state or (lambda vk: bool(user32.GetAsyncKeyState(vk) & 0x8000))
        s.front = front or s._front
        s.pad = pad if pad is not None else (pads() if state is None else None)

    def _front(s):
        return in_front(s.pid)

    def poll(s, down):
        """One pass: the edges since the last (tests call it directly)."""
        front = s.front()
        mask = s.pad() if s.pad and front else 0
        for vk, d in [(vk, front and s.state(vk)) for vk in s.vks] + [(PAD_VK + b, bool(mask >> b & 1)) for b in PAD]:
            if d != down.get(vk, False):
                down[vk] = d
                with s.lock:
                    s.events.append((round(s.clock(), 4), vk, int(d)))

    def run(s):
        down = {}
        while not s.done:
            s.poll(down)
            time.sleep(s.period)

    def take(s):
        with s.lock:
            out, s.events = s.events, []
        return out


class Collector:
    def __init__(s, path, map_name, game, pid, clock, keymap=None, keys=None):
        s.path, s.clock = path, clock
        s.keymap = keymap if keymap is not None else binds()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        s.out = open(path, "w", encoding="utf-8")
        s.last = {}                                  # person -> the last guns / equipment line written
        s.out.write(json.dumps(dict(t=round(clock(), 3), collect="start", map=map_name, game=game,
                                    keys={str(k): v for k, v in sorted(s.keymap.items())})) + "\n")
        s.keys = keys if keys is not None else Keys(s.keymap, pid, clock)
        if keys is None:
            s.keys.start()

    def tick(s, now, players, zoom=None, aims=None):
        """players: brain.core.PlayerState list (the tick's snapshot); zoom(id) -> the unit's zoom byte or None;
        aims: person id -> (crosshair, ride), appended to that person's row (tools/live_bots.py)."""
        rows = [[p.id, p.team, int(p.alive), round(p.pos.x, 2), round(p.pos.y, 2), round(p.pos.z, 2),
                 round(p.yaw, 3), round(p.pitch, 3), round(p.shield, 2), round(p.health, 2), int(p.vehicle != -1),
                 int(p.has_flag), int(p.is_bot)] + list((aims or {}).get(p.id, ())) for p in players]
        lines = [dict(t=round(now, 3), p=rows)]
        for p in players:
            if p.is_bot:
                continue
            g = dict(wpn=p.weapon, inv=list(p.weapons), ammo=list(p.ammo), mag=list(p.mag), eq=p.equipment,
                     ab=int(p.ability_on), uz=zoom(p.id) if zoom else None)
            if s.last.get(p.id) != g:
                s.last[p.id] = g
                lines.append(dict(t=round(now, 3), id=p.id, **g))
        for t, vk, down in s.keys.take():
            lines.append(dict(t=t, key=s.keymap.get(vk, key_name(vk)), vk=vk, down=down))
        s.out.write("".join(json.dumps(x) + "\n" for x in lines))

    def close(s):
        s.keys.done = True
        for t, vk, down in s.keys.take():
            s.out.write(json.dumps(dict(t=t, key=s.keymap.get(vk, key_name(vk)), vk=vk, down=down)) + "\n")
        s.out.close()
