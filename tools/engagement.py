"""Engagement report from a live (or sim) trace: who died how often, the player's kills, stuck and edge
events per bot, how each weapon was used (fire share and range in fights, fire outside the weapon's band),
equipment plans and the time they froze a bot, and every long close encounter with the player (a bot
within 8 units of him for 15 s or more: what it was doing meanwhile)..

usage: python -I engagement.py <trace.jsonl> [person id, default 0]
"""
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain.bot import WEAPON_RANGE  # noqa: E402

BANDS = ((0.8, "melee"), (4.0, "short"), (12.0, "medium"), (30.0, "long"), (1e9, "extreme"))


def band(d):
    return next(n for lim, n in BANDS if d < lim)


def load(path):
    meta, world, bots, thinks = {}, [], collections.defaultdict(list), collections.defaultdict(list)
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if "meta" in d:
            b = d["meta"].get("bot")
            if b:
                meta[b["id"]] = b
        elif "world" in d:
            world.append(d)
        elif "think" in d:
            thinks[d["id"]].append(d)
        elif "id" in d and "cmd" in d:
            bots[d["id"]].append(d)
    return meta, world, bots, thinks


def deaths(world):
    """(t, id, pos) for each alive -> dead change; a change of half the players at once is the end."""
    out, alive = [], {}
    for w in world:
        gone = [r for r in w["world"] if not r[2] and alive.get(r[0])]
        if len(gone) < max(3, len(w["world"]) // 2):
            out += [(w["t"], r[0], alive[r[0]]) for r in gone]
        for r in w["world"]:
            alive[r[0]] = (r[3], r[4], r[5]) if r[2] else None
    return out


def at(rows, t, key="t"):
    """The last row at or before t (rows sorted by t)."""
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid][key] <= t:
            lo = mid + 1
        else:
            hi = mid
    return rows[lo - 1] if lo else None


def main():
    path = sys.argv[1]
    person = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    meta, world, bots, thinks = load(path)
    span = world[-1]["t"] - world[0]["t"] if world else 0.0
    died = deaths(world)
    print(f"== {os.path.basename(path)}: {span:.0f} s, {len(meta)} bots, person #{person}")

    # the player's kills: a bot that died within 2 s of the player facing it (0.15 rad) from 40
    # units
    pos_at = lambda pid, t: next((r for r in (at(world, t) or {"world": []})["world"] if r[0] == pid), None)
    kills = []
    for t, pid, p in died:
        if pid == person or p is None:
            continue
        o = pos_at(person, t - 0.5)
        if o and o[2]:
            dx, dy = p[0] - o[3], p[1] - o[4]
            d = math.hypot(dx, dy)
            off = abs(math.atan2(math.sin(math.atan2(dy, dx) - o[10]), math.cos(math.atan2(dy, dx) - o[10])))
            if d < 40 and off < 0.15 + 0.6 / max(d, 1.0):
                kills.append((t, pid, round(d, 1)))
    od = [x for x in died if x[1] == person]
    print(f"  person: {len(kills)} kills (bots dying in his sights), {len(od)} deaths; "
          f"all deaths {len(died)} ({len(died) / max(span / 60, 0.01):.1f} a minute)")

    # per bot: deaths, stuck and edge events, fights, fire share
    print("  bot  tier    pers      deaths  stuck  edge  fight%  fire%(fight)  top goals")
    stuck_spots = collections.Counter()
    for bid in sorted(bots):
        rows = bots[bid]
        m = meta.get(bid, {})
        prev, stuck, edge = None, 0, 0
        for r in rows:
            for n in r.get("notes", []):
                if n != prev and n.startswith("unstuck"):
                    stuck += 1
                    stuck_spots[(round(r["pos"][0]), round(r["pos"][1]), round(r["pos"][2]))] += 1
                if n != prev and n.startswith("edge"):
                    edge += 1
                prev = n
            if not r.get("notes"):
                prev = None
        fight = [r for r in rows if r["goal"] == "fight"]
        fire = sum(1 for r in fight if r["cmd"][3] & 1)
        goals = collections.Counter(r["goal"] for r in rows).most_common(3)
        print(f"  #{bid:<3} {m.get('tier', '?'):7} {m.get('pers', '?'):9} {sum(1 for x in died if x[1] == bid):6} "
              f"{stuck:6} {edge:5} {100 * len(fight) / max(len(rows), 1):6.0f} {100 * fire / max(len(fight), 1):12.0f}  "
              + ", ".join(f"{g} {100 * n / len(rows):.0f}%" for g, n in goals))
    print("  stuck spots (x, y, z: events):", ", ".join(f"{k}: {v}" for k, v in stuck_spots.most_common(8)))

    # weapons in fights: fire share, range, fire outside the weapon's band
    print("  weapon            fight ticks  fire%  median d  fire out of band  deaths holding it")
    wf = collections.defaultdict(lambda: dict(n=0, fire=0, d=[], out=0))
    for bid, rows in bots.items():
        for r in rows:
            if r["goal"] != "fight" or not str(r.get("arg")).isdigit():
                continue
            tgt = pos_at(int(r["arg"]), r["t"])
            if not tgt:
                continue
            d = math.dist(r["pos"], tgt[3:6])
            w = wf[r.get("wpn") or "?"]
            w["n"] += 1
            w["d"].append(d)
            if r["cmd"][3] & 1:
                w["fire"] += 1
                lo, hi = WEAPON_RANGE.get(r.get("wpn"), (5.0, 25.0))
                w["out"] += d < lo - 1.0 or d > hi
    held = collections.Counter()
    for t, pid, p in died:
        if pid in bots:
            r = at(bots[pid], t - 0.3)
            if r:
                held[r.get("wpn")] += 1
    for name, w in sorted(wf.items(), key=lambda kv: -kv[1]["n"]):
        med = sorted(w["d"])[len(w["d"]) // 2] if w["d"] else 0
        print(f"  {name:18} {w['n']:11} {100 * w['fire'] / max(w['n'], 1):5.0f}  {med:8.1f}  "
              f"{100 * w['out'] / max(w['fire'], 1):15.0f}%  {held[name]:5}")

    # equipment plans and the time they froze the bot (no move, no fire)
    plans = collections.Counter()
    for bid, rows in bots.items():
        prev = None
        for r in rows:
            for n in r.get("notes", []):
                k = n.split(":")[0]
                if n != prev and k in ("armor_lock", "sprint", "jetpack", "hologram", "active_camo", "drop_shield",
                                       "evade", "thruster", "promethean_vision", "hardlight_shield", "regen_field",
                                       "autosentry", "bubble_shield", "power_drain", "regenerator", "trip_mine", "flare"):
                    plans[n] += 1
                prev = n
    if plans:
        print("  equipment plans:", dict(plans.most_common(10)))

    owner_duels(person, kills, od, world, bots, thinks)

    # long close encounters with the player
    print("  close encounters with the person (within 8 units, 15 s or more):")
    for bid, rows in bots.items():
        win, start = [], None
        for r in rows[::3]:
            o = pos_at(person, r["t"])
            near = o and o[2] and math.dist(r["pos"], o[3:6]) < 8.0
            if near:
                start = r["t"] if start is None else start
                win.append(r)
            elif start is not None:
                if win[-1]["t"] - start >= 15.0:
                    report_window(bid, meta, win, person, died)
                win, start = [], None
        if start is not None and win[-1]["t"] - start >= 15.0:
            report_window(bid, meta, win, person, died)


def owner_duels(person, kills, owner_deaths, world, bots, thinks):
    """Each of the player's kills, its last 6 s: did the bot know of him (eyes), fight him, fire at him,
    who was hurt first, did he lose any shield, was either side helped. Then his deaths, and how many
    enemy bots fought him at once (focus fire). What separates a free kill from a lost duel."""
    team_of = {r[0]: r[1] for w in world[:50] for r in w["world"]}
    hp_of = lambda w, pid: next((r[6] + r[7] for r in w["world"] if r[0] == pid and r[2]), None)
    kinds, rows_out = collections.Counter(), []
    for t, pid, d in kills:
        rows = [r for r in bots.get(pid, []) if t - 6.0 <= r["t"] <= t]
        th = [x for x in thinks.get(pid, []) if t - 6.0 <= x["t"] <= t]
        ws = [w for w in world if t - 6.0 <= w["t"] <= t]
        if not rows or not ws:
            continue
        on = [r for r in rows if r["goal"] == "fight" and str(r["arg"]) == str(person)]
        saw = next((x["t"] for x in th if any(b[0] == person and b[4] for b in x.get("beliefs", []))), None)
        fought = on[0]["t"] if on else None
        fired = sum(1 for r in on if r["cmd"][3] & 1)
        hp = [(w["t"], hp_of(w, pid)) for w in ws]
        hurt = next((b[0] for a, b in zip(hp, hp[1:]) if a[1] is not None and b[1] is not None and b[1] < a[1] - 0.01), None)
        ohp = [x for x in (hp_of(w, person) for w in ws) if x is not None]
        dealt = max(0.0, ohp[0] - min(ohp)) if ohp else 0.0      # the player's shield + health lost meanwhile
        last = at(world, t - 1.0)
        me = next((r for r in last["world"] if r[0] == pid), None) if last else None
        near = lambda team: sum(1 for r in last["world"] if r[2] and r[0] not in (pid, person) and r[1] == team
                                and me and math.dist(r[3:6], me[3:6]) < 12) if last else 0
        mates, his = near(team_of.get(pid)), near(team_of.get(person))
        busy = collections.Counter(r["goal"] if r["goal"] != "fight" or str(r["arg"]) == str(person) else "fight other"
                                   for r in rows if r["t"] > t - 3.0).most_common(1)[0][0]
        kind = ("never saw him" if saw is None else "saw him, fought someone else" if not on
                else "fought him, never fired" if not fired else "fired at him, lost")
        kinds[kind] += 1
        first = "him" if hurt is not None and (fought is None or hurt < fought - 0.05) else "bot"
        rows_out.append((t, pid, d, rows[-1].get("wpn"), kind, busy, first, fired, dealt, mates, his,
                         None if saw is None or fought is None else fought - saw))
    if not rows_out:
        return
    print("  the person's kills, last 6 s of each (dealt = his shield + health lost meanwhile, of 2.0):")
    print("     t   bot   d  weapon           what it was doing          last 3 s        hurt 1st  shots  dealt  mates  his  saw->fight")
    for t, pid, d, wpn, kind, busy, first, fired, dealt, mates, his, lag in rows_out:
        print(f"  {t:5.0f}  #{pid:<3} {d:4.0f}  {str(wpn):16} {kind:26} {busy:15} {first:8} {fired:5}  {dealt:5.2f}  "
              f"{mates:5} {his:4}  {'' if lag is None else f'{lag:.2f}'}")
    n = len(rows_out)
    print(f"  summary: {dict(kinds)}; he was hurt first {sum(1 for x in rows_out if x[6] == 'him')}/{n}; "
          f"dealt him nothing {sum(1 for x in rows_out if x[8] < 0.05)}/{n}; alone (no mate in 12 u) "
          f"{sum(1 for x in rows_out if x[9] == 0)}/{n}; his team helped {sum(1 for x in rows_out if x[10] > 0)}/{n}")
    for t, _, _ in owner_deaths:
        ws = [w for w in world if t - 6.0 <= w["t"] <= t]
        on = {bid for bid, rows in bots.items() for r in rows
              if t - 6.0 <= r["t"] <= t and r["goal"] == "fight" and str(r["arg"]) == str(person)}
        print(f"  person died at {t:.0f} s: {len(on)} bots fighting him in the last 6 s {sorted(on)}")
    counts = collections.Counter()
    by_t = collections.defaultdict(set)
    for bid, rows in bots.items():
        if team_of.get(bid) == team_of.get(person):
            continue
        for r in rows:
            if r["goal"] == "fight" and str(r["arg"]) == str(person):
                by_t[round(r["t"] * 2)].add(bid)
    for k, v in by_t.items():
        counts[len(v)] += 1
    tot = sum(counts.values())
    if tot:
        print("  enemy bots fighting him at once (share of half seconds with any):",
              ", ".join(f"{k}: {100 * v / tot:.0f}%" for k, v in sorted(counts.items())))


def report_window(bid, meta, win, person, died):
    t0, t1 = win[0]["t"], win[-1]["t"]
    goals = collections.Counter(r["goal"] for r in win)
    on_owner = sum(1 for r in win if r["goal"] == "fight" and str(r["arg"]) == str(person))
    fire = sum(1 for r in win if r["cmd"][3] & 1)
    moved = sum(math.dist(a["pos"], b["pos"]) for a, b in zip(win, win[1:]))
    notes = collections.Counter(n for r in win for n in r.get("notes", []))
    d_deaths = [x for x in died if x[1] == bid and t0 <= x[0] <= t1]
    m = meta.get(bid, {})
    print(f"    #{bid} ({m.get('tier')} {m.get('pers')}) {t0:.0f}-{t1:.0f} s ({t1 - t0:.0f} s): goals "
          + ", ".join(f"{g} {100 * n / len(win):.0f}%" for g, n in goals.most_common(3))
          + f"; fighting the person {100 * on_owner / len(win):.0f}%, firing {100 * fire / len(win):.0f}%, "
          f"walked {moved:.0f} units, died {len(d_deaths)}x; notes {dict(notes.most_common(4))}")


if __name__ == "__main__":
    main()
