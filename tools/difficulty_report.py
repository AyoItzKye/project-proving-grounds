"""Compare bot behaviour across difficulty tiers in the offline Blood Gulch sim (CTF). Checks the
player's rules: easiest bots never jump and run straight at the objective; hardest bots jump
shot, strafe and juke, take side and sneaky routes, and go for power weapons on time.

usage: python tools/difficulty_report.py [seconds]   (from the project folder)
       python tools/difficulty_report.py --ladder [seconds]   every tier in one lobby: K/D by tier
       python tools/difficulty_report.py --human [seconds]    a good-human stand-in's K/D against each tier
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.sim import Sim  # noqa: E402

TIERS = ["novice", "average", "strong", "top"]
PERS = ["rusher", "camper", "flanker", "objector", "spammer", "grudger", "sniper"]


def run(tier, seconds, seed):
    sim = Sim("ctf", per_team=4, seed=seed, tiers=[tier])
    routes = collections.Counter()
    orig = {t: d.pick_route for t, d in sim.directors.items()}
    for t, d in sim.directors.items():
        def wrapped(now, b, used, _f=orig[t], _m=sim.m):
            via = _f(now, b, used)
            sneaky = any(list(via) == r for r in _m["sneak"].get(b.team, []))
            routes["straight" if not via else ("sneaky" if sneaky else "lane")] += 1
            return via
        d.pick_route = wrapped
    sim.run(seconds)
    st = sim.stats.values()
    minutes = seconds / 60
    fights = sum(v["fight_ticks"] for v in st)
    return {
        "jumps/min/bot": round(sum(v["jumps"] for v in st) / minutes / len(st), 2),
        "strafe in fights": f"{sum(v['strafe_ticks'] for v in st) / max(fights, 1):.0%}",
        "routes": dict(routes),
        "pickups": collections.Counter(n for _, _, n in sim.pickups),
        "accuracy": f"{sum(v['hits'] for v in st) / max(1, sum(v['shots'] for v in st)):.0%}",
        "kills": sum(v["kills"] for v in st),
        "flag takes": sum(1 for e in sim.flag_events if e[1] == "taken"),
        "caps": sum(sim.score.values()),
    }


def now_seen(bot, pid):
    b = bot.per.beliefs.get(pid)
    return b is not None and b.seen


def ladder_run(job):
    """One mixed-tier match (two of each tier a team): kills and deaths by tier, and who killed whom."""
    map_name, mode, seed, seconds = job
    # one personality for the whole lobby (by seed): in seat order the tiers drew different ones (the
    # campers and the sniper were all Normal), so the ladder measured personalities, not difficulty
    sim = Sim(mode, per_team=8, seed=seed, tiers=TIERS, map_name=map_name, personalities=[PERS[seed % len(PERS)]])
    pairs = collections.Counter()
    orig = sim.kill

    def kill(e, src):
        tier = sim.stats[e.id]["tier"]
        pairs[(sim.stats[src.id]["tier"], tier)] += 1
        v = sim.bots[e.id]                    # how it died: never saw its killer / saw him, fought another
        saw = src.id in v.per.recognized or now_seen(v, src.id)
        pairs[("blind", tier)] += not saw
        pairs[("other", tier)] += saw and v.goal != ("fight", src.id)
        mates = sum(1 for p in sim.players if p.team == src.team and p.alive and p.id != src.id
                    and sim.bots[p.id].goal == ("fight", e.id))
        pairs[("2v1", sim.stats[src.id]["tier"])] += mates > 0
        orig(e, src)
    sim.kill = kill
    sim.run(seconds)
    by = collections.defaultdict(lambda: [0, 0])
    for v in sim.stats.values():
        by[v["tier"]][0] += v["kills"]
        by[v["tier"]][1] += v["deaths"]
    return dict(by), pairs


def ladder(seconds, seeds=tuple(range(7)), maps=(("reach_50_panopticon", "slayer"), ("h3_construct", "slayer"))):
    """The difficulty ladder: every tier in one lobby, K/D by tier and head to head. A ladder that works is
    steep: top over strong over average over novice."""
    from multiprocessing import Pool
    jobs = [(m, mode, s, seconds) for m, mode in maps for s in seeds]
    with Pool(min(len(jobs), 6)) as pool:
        res = pool.map(ladder_run, jobs)
    by, pairs = collections.defaultdict(lambda: [0, 0]), collections.Counter()
    for b, p in res:
        for t, (k, d) in b.items():
            by[t][0] += k
            by[t][1] += d
        pairs.update(p)
    print(f"ladder: {len(jobs)} matches x {seconds:.0f} s ({', '.join(m for m, _ in maps)}; seeds {list(seeds)})")
    for t in TIERS:
        k, d = by[t]
        print(f"  {t:8s} kills {k:4}  deaths {d:4}  K/D {k / max(d, 1):.2f}")
    print("  head to head (row's kills on column / column's kills on row):")
    for a in TIERS:
        print(f"  {a:8s} " + "  ".join(f"{b[:3]} {pairs[(a, b)]:3}/{pairs[(b, a)]:<3}" for b in TIERS if b != a))
    print("  deaths never having seen the killer / seen but fighting someone else; kills with a mate on him:")
    for t in TIERS:
        k, d = by[t]
        print(f"  {t:8s} blind {100 * pairs[('blind', t)] / max(d, 1):3.0f}%   other {100 * pairs[('other', t)] / max(d, 1):3.0f}%"
              f"   2v1 kills {100 * pairs[('2v1', t)] / max(k, 1):3.0f}%")
    return {t: by[t][0] / max(by[t][1], 1) for t in TIERS}


# a stand-in for a good human: the bot brain with human hands. A bot re-reads a strafe every 0.1 s and
# leads it well; a person about every quarter second, leading worse (modelled, not measured on the
# player)
HUMAN = dict(track=0.25, reaction=0.26, lead=0.6, aim_err=0.012)
# his decisions: a Regular's, held fixed, so what a tier change does shows only in the bots he plays against
# (with the top brain every Legendary change made the stand-in better too and moved all four numbers)
STAND_IN = "average"


def human_run(job):
    """One match: a human stand-in on each team (the player's lobby: one person, bots of one tier; two a
    team changed the answer), every bot of one tier. His kills and deaths against bots (each other's
    kills on the two stand-ins left out)."""
    import dataclasses
    import random
    from brain.bot import Bot
    from brain.profiles import make_profile
    tier, map_name, mode, seed, seconds = job
    sim = Sim(mode, per_team=8, seed=seed, tiers=[tier], map_name=map_name, personalities=[PERS[seed % len(PERS)]])
    humans = []
    for team in (0, 1):
        pid = next(p.id for p in sim.players if p.team == team)
        prof = dataclasses.replace(make_profile(STAND_IN, "rusher", random.Random(seed * 7 + team)), **HUMAN)
        sim.bots[pid] = sim.directors[team].bots[pid] = Bot(pid, team, prof, sim.m, random.Random(seed * 100 + pid))
        humans.append(pid)
    res = collections.Counter()
    orig = sim.kill

    def kill(e, src):
        res["k"] += src.id in humans and e.id not in humans
        res["d"] += e.id in humans and src.id not in humans
        orig(e, src)
    sim.kill = kill
    sim.run(seconds)
    for pid in humans:
        res["shots"] += sim.stats[pid]["shots"]
        res["hits"] += sim.stats[pid]["hits"]
    return tier, res


def human(seconds, seeds=tuple(range(7)), tiers=TIERS, maps=(("reach_50_panopticon", "slayer"), ("h3_construct", "slayer"))):
    """How hard each difficulty is for a good human (modelled): the stand-in's K/D against a lobby of
    that tier. the player's targets: Easy he dominates, Heroic manageable but challenging, Legendary
    hard."""
    from multiprocessing import Pool
    jobs = [(t, m, mode, s, seconds) for t in tiers for m, mode in maps for s in seeds]
    tot = collections.defaultdict(collections.Counter)
    with Pool(6) as pool:
        for tier, res in pool.imap_unordered(human_run, jobs):
            tot[tier].update(res)
    print(f"human stand-in: {len(jobs)} matches x {seconds:.0f} s ({', '.join(m for m, _ in maps)}; 2 stand-ins a match)")
    for t in tiers:
        k, d = tot[t]["k"], tot[t]["d"]
        n = len(seeds) * len(maps) * 2
        print(f"  vs {t:8s} K/D {k / max(d, 1):4.2f}   kills {k / n / (seconds / 60):4.1f}/min   deaths {d / n / (seconds / 60):4.1f}/min   his hits {100 * tot[t]["hits"] / max(tot[t]["shots"], 1):3.0f}%")
    return {t: tot[t]["k"] / max(tot[t]["d"], 1) for t in tiers}


def main():
    if "--human" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--human"]   # [seconds] [tier,tier..] [seeds]
        human(float(args[0]) if args else 150, tuple(range(int(args[2]))) if len(args) > 2 else tuple(range(7)),
              args[1].split(",") if len(args) > 1 else TIERS)
        return
    if "--ladder" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--ladder"]
        ladder(float(args[0]) if args else 150)
        return
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 240
    out = {t: run(t, seconds, seed=21) for t in TIERS}
    for t, r in out.items():
        print(f"{t:8s} {r}")
    # the player's rules as checks
    assert out["novice"]["jumps/min/bot"] == 0, "novices must never jump"
    assert set(out["novice"]["routes"]) <= {"straight"}, "novices must run straight at the objective"
    assert out["top"]["jumps/min/bot"] > out["average"]["jumps/min/bot"] > 0, "jumping must rise with skill"
    assert out["top"]["routes"].get("sneaky", 0) > 0, "top bots should take sneaky routes"
    assert sum(out["top"]["pickups"].values()) > sum(out["novice"]["pickups"].values()), "top bots should get more power items"
    print("difficulty checks OK")


if __name__ == "__main__":
    main()
