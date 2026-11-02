"""Live QC of Halo: Reach game types with bots (supervisor: "play Territories, Assault, Stockpile, Headhunter, Infection
and CTF live on each map they appear on; report what the bots did"). From the Reach custom game lobby (MCC on any
monitor, test override with the bots in logs/test_override.json): pick the map and the game type by keys, start, let
the brain play MINUTES, end the match from the pause menu, back to the lobby; then read the match's trace and write one
line of what happened to logs/live_qc.md (and the trace name).

Keys since: on MCC's newer menus (main menu text at x 273, not 92) every click spot had moved, and with MCC on monitor
2 a click only pressed whatever was focused (END GAME clicked opened LEAVE). The lobby by keys, each step seen on a
screenshot: the top row is map, game type, options, START; Down from the map tile opens the map carousel; picking a
map opens the game type carousel by itself (Reach's 13: 1 Slayer, 2 CTF, 3 Oddball, 4 King, 5 Juggernaut, 6 Infection;
seen picked: 3 Oddball, 4 King, 10 HEADHUNTER, so 7-13 are not in the order once listed here, 7 Race, 8 Territories, 9
Assault, 10 Stockpile, 11 Headhunter: Stockpile is likely 9; check on screen); picking one opens its variants on the
first after the category's own tile; picking one opens the options on ACCEPT OPTIONS; accepting focuses START (Enter:
the countdown). Pause menu: LEAVE, END GAME...; its dialog YES is left of NO. Esc on the carnage report is Back.

usage: python -I live_qc.py <map#> <category#> <variant#> [--minutes 5] [--label text]
       map# / category# / variant#: positions in the lobby's choosers (1 = first); the started match's map and variant
       name are read from the game and written next to them, so a wrong pick shows.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
def key(*names):
    """Keys to MCC (focused first), 0.4 s apart (mcc_nav.py key)."""
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "key", *names], capture_output=True)


def pick_keys(m, c, v):
    """Map m, category c, variant v by keys (the module notes), then ACCEPT OPTIONS: START focused after."""
    key("up", "up", *["left"] * 4)                       # the top row's map tile (out of any open chooser)
    # (a pause after the run to the first entry: right after it, picks that scrolled the carousel landed one past:
    # category 8 started Assault, 9 Stockpile; 2-4 were right)
    key("down", *["left"] * 30)                         # (Halo 3 has 27 maps, Reach 20)
    time.sleep(1.5)
    key(*["right"] * (m - 1), "enter")
    time.sleep(2.5)
    # the game type tile's carousel: it opens by itself only when the map changed (the same map twice: the
    # category keys went nowhere and the last game type was played again, Infection three times)
    key("up", "up", *["left"] * 4, "right", "down")
    time.sleep(1.5)
    key(*["left"] * 14)
    time.sleep(1.5)
    key(*["right"] * (c - 1), "enter")
    time.sleep(2.5)
    key(*["right"] * (v - 1), "enter")                  # (it opens on the first variant)
    time.sleep(2.5)
    key("enter")                                        # ACCEPT OPTIONS: START is focused
    time.sleep(2.0)


def in_game():
    try:
        from brain import live as L
        live = {"reach": L.LiveReach, "h3": L.LiveH3, "h2": L.LiveH2, "ce": L.Live, "h4": L.LiveH4F,
                "h2a": lambda: L.LiveH4F("groundhog.dll")}[GAME[0]]()
        return live if live.players() else None
    except Exception:
        return None


def in_menus():
    """MCC's own menu byte (exe+0x4000B8C+0x11: 0 menus, 1 in a game). The match is over only when this says menus: an
    empty player list also happens between rounds (live, Territories: read as the end, the next clicks left the
    lobby and started ODST Firefight)."""
    try:
        from memread import Game
        g = Game("MCC-Win64-Shipping.exe")
        return g.read(g.base + 0x4000B8C + 0x11, 1)[0] == 0
    except BaseException:
        return False


def in_reach_lobby(timeout=8.0):
    """The game's custom game lobby is on screen (its title, tools/menu_titles/<game>_lobby.png): no picking clicks
    anywhere else."""
    import goto_lobby
    return goto_lobby.on_screen(GAME[0] + "_lobby", timeout=timeout, fatal=False)


GAME = ["reach"]         # --game reach | h3 (Halo 3's lobby has the same choosers); ce, h2, h2a, h4 with --here


def end_match():
    for attempt in range(3):     # an Esc while the host is dead (respawn scoreboard) opens no pause menu
        if in_menus():           # the match ended by itself meanwhile: END GAME / YES would land on the lobby's
            time.sleep(10)       # game type tile and a category (Invasion became Headhunter)
            break
        key("esc")
        time.sleep(1.5)
        if in_menus():
            time.sleep(10)
            break
        key("left", "left", "left", "left", "right", "enter")   # END GAME (the row's second: LEAVE is first)
        time.sleep(2.0)
        if in_menus():
            time.sleep(10)
            break
        key("left", "enter")             # YES (left of the focused NO)
        time.sleep(1.5)
        t0 = time.time()         # the post-game report can take a while: no second Esc on it (it leaves the lobby)
        while time.time() - t0 < 35 and not in_menus():
            time.sleep(2)
        if in_menus():
            time.sleep(10)
            break
        time.sleep(4)            # still playing: wait out the respawn, try again
    for _ in range(4):           # the END GAME dialog left open (Halo 3: YES clicked while it was still
        if in_menus():           # opening did nothing, three times): YES once it has settled
            break
        key("left", "enter")
        time.sleep(8)
    key("esc")                   # Back: to the lobby (from the post-game report)
    time.sleep(6)


def summarize(trace):
    """What the bots did, from the trace's world lines (live_bots.py) and bot lines."""
    modes, best, last = {}, {}, None
    carriers, owners, flags_taken, phases, core_carriers = set(), {}, 0, set(), set()
    prev_flag = {}
    seats, ferries = {}, set()                   # bot -> seats it sat in; bots sent to pick up a carrier
    for line in open(trace, encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if "seat" in r:
            seats.setdefault(r["id"], set()).add(r["seat"])
        if (r.get("order") or [None])[0] == "ferry":
            ferries.add(r["id"])
        if "world" not in r:
            continue
        last = r
        modes[r.get("mode")] = modes.get(r.get("mode"), 0) + 1   # (the line after the match ended reads slayer)
        for t, v in (r.get("score") or {}).items():               # (and 0-0: the best each team reached)
            best[t] = max(best.get(t, 0), v)
        for it in r.get("items") or []:
            if it[3] is not None:
                carriers.add(it[3])
        for k, z in enumerate(r.get("zones") or []):
            if z[4] != -1 and owners.get(k) != z[4]:
                owners[k] = z[4]
                owners.setdefault("changes", 0)
                owners["changes"] += 1
        for t, f in (r.get("flags") or {}).items():
            if f[0] == "carried" and prev_flag.get(t) != "carried":
                flags_taken += 1
            prev_flag[t] = f[0]
        inv = r.get("invasion")
        if inv:
            phases.add(inv[0])
            if inv[5] is not None:
                core_carriers.add(inv[5])
    if last is None:
        return "no world lines in the trace"
    out = [f"mode {max(modes, key=modes.get)}", f"score {best}", f"brain ran {last.get('t', 0):.0f} s"]
    if carriers:
        out.append(f"{len(carriers)} players carried the objective")
    if owners:
        out.append(f"territory captures {owners.get('changes', 0)}")
    if flags_taken:
        out.append(f"flag pickups {flags_taken}")
    if phases:
        out.append(f"Invasion phases {sorted(phases)}, core carriers {len(core_carriers)}")
    if seats:
        n = lambda k: sum(k in v for v in seats.values())
        out.append(f"bots in vehicles {len(seats)} (drove {n('driver')}, gunner {n('gunner')}, passenger {n('passenger')})")
    if ferries:
        out.append(f"ferry orders {len(ferries)}")
    return "; ".join(out)


def main():
    a = sys.argv[1:]
    if "--game" in a:
        GAME[0] = a[a.index("--game") + 1]
    if "--here" in a:            # the lobby as it is: no picks, just play it
        if not in_reach_lobby():
            print("not in the custom game lobby: no clicks")
            sys.exit(2)
        play(float(a[a.index("--minutes") + 1]) if "--minutes" in a else 5.0,
             a[a.index("--label") + 1] if "--label" in a else "")
        return
    m, c, v = (int(x) for x in a[:3])
    minutes = float(a[a.index("--minutes") + 1]) if "--minutes" in a else 5.0
    label = a[a.index("--label") + 1] if "--label" in a else ""
    if not in_reach_lobby():     # the choosers' clicks anywhere else go astray (they started ODST Firefight)
        print("not in the Reach custom game lobby: no clicks")
        sys.exit(2)
    pick_keys(m, c, v)           # (never Esc in the options panel: it leaves the lobby)
    play(minutes, label, focused=True)


def play(minutes, label, focused=False):
    """START the lobby's setup, play `minutes`, end the match, write what the bots did. focused: START already is."""
    if not focused:
        key("up", "up", *["left"] * 4, *["right"] * 3)   # the top row's START tile (4th: map, game type, options)
    live = None
    for attempt in range(3):     # Enter starts the countdown (once in a while it needs a second press)
        key("enter")
        t0 = time.time()
        while time.time() - t0 < 75 and live is None:
            time.sleep(5)
            live = in_game()
        if live is not None:
            break
    if live is None:
        print("no match started")
        sys.exit(1)
    try:
        name, variant = live.map_name(), live.variant_name()
    except Exception:
        name, variant = "?", "?"
    start, gone = time.time(), 0
    while time.time() - start < minutes * 60 and gone < 2:   # a match that ends by itself: the post-game report
        time.sleep(10)
        gone = gone + 1 if in_menus() else 0
    # (any game's: CE's map folders have no game prefix, trace_beavercreek_...; one match runs at a time)
    traces = sorted(glob.glob(os.path.join(ROOT, "logs", "trace_*.jsonl")), key=os.path.getmtime)
    trace = traces[-1] if traces and os.path.getmtime(traces[-1]) > start - 60 else None
    if gone >= 2:                # (the pause menu's clicks there landed in the lobby's choosers, live)
        time.sleep(10)
        key("esc")               # Back: to the lobby
        time.sleep(6)
    else:
        end_match()
    what = summarize(trace) if trace else "no trace"
    if trace and ("Invasion" in what or "vehicles" in what):    # evidence kept (play.py keeps only the newest 5)
        os.makedirs(os.path.join(ROOT, "logs", "qc_keep"), exist_ok=True)
        shutil.copy(trace, os.path.join(ROOT, "logs", "qc_keep"))
    try:                         # the brain's own log of this match: failed ticks, Forge World's pieces
        log = open(os.path.join(ROOT, "logs", "brain.txt"), encoding="utf-8", errors="replace").read()
        # (the game closing mid-read fails a tick or two with these two: not the brain's fault)
        fails = sum("tick failed" in l and "game thread" not in l and "not 'NoneType'" not in l
                    for l in log.splitlines())
        what += f"; brain errors {fails}" + "".join(f"; {l.strip()}" for l in log.splitlines() if "Forge pieces" in l)
    except OSError:
        pass
    line = (f"| {time.strftime('%H:%M')} | {label} | {name} | {variant} | {minutes:.0f} min | {what} | "
            f"{os.path.basename(trace) if trace else '-'} |")
    print(line)
    with open(os.path.join(ROOT, "logs", "live_qc.md"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if not in_reach_lobby(timeout=20):   # not back in the lobby: stop here, no more clicks (live_qc_batch stops on 2)
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "shot"], capture_output=True)
        print("not back in the Reach lobby after the match (logs/nav_now.jpg): stopped")
        sys.exit(2)


if __name__ == "__main__":
    main()
