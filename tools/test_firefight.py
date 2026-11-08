"""brain/firefight.py against the guides' tables (docs/bot-brain/11-reach-firefight-versus.md section 9.5,
12-firefight-enemy-handbook.md section 3.1): the threat order, the heat formula and zones, the decision tables, roles."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import firefight as F  # noqa: E402


def main():
    fails = []

    def check(ok, what):
        if not ok:
            fails.append(what)

    t = lambda rank, d, **k: F.threat_mult(rank, d, **k)
    # the Reach ladder: a fuel rod Grunt at Medium over an Ultra Elite at Medium over a Minor Grunt; Engineers first
    check(t("grunt_heavy", 8) > t("elite_ultra", 8) > t("grunt", 8), "ladder: heavy Grunt > Ultra > Minor Grunt")
    check(t("engineer", 15) > t("elite_ultra", 15), "an Engineer outranks an Ultra")
    check(t("jackal_sniper", 20) > t("jackal", 20), "Jackal snipers over shield Jackals")
    check(t("hunter", 0.5) > t("hunter", 20), "a Hunter at Melee band over one at Long")
    # Versus: a player Elite at 2 lives or fewer outranks everything but a Hunter at Melee band
    pe = t(None, 6, player_side=F.ELITE, versus=True, lives=2)
    check(pe > t("grunt_heavy", 6) and pe > t("chieftain", 6) and t("hunter", 0.5) >= pe * 0.9,
          f"a player Elite at 2 lives ({pe:.2f}) over the wave, not over a Hunter at Melee band")
    check(t(None, 6, player_side=F.ELITE, versus=True, lives=4) < pe, "the Elite's value rises as the lives fall")
    check(t("grunt", 8, last_three=True) > t("grunt", 8), "the last three of a wave are worth more")
    check(F.entry("elite_officer") == F.entry("elite_major") and F.entry("grunt_major") == F.entry("grunt"),
          "rank names: the Firefight maps' tags")
    # heat (section 2.4): Hunters and low lives push it hot, a held strongpoint and a power weapon cool it
    check(F.heat_zone(F.heat(squads_alive=1)) == "cool", "one squad: cool")
    check(F.heat_zone(F.heat(squads_alive=3)) == "warm", "three squads: warm")
    check(F.heat_zone(F.heat(squads_alive=3, big=True, lives=2)) == "hot", "Hunters at 2 lives: hot")
    check(F.heat(squads_alive=3, power_weapon=True, held=True) < F.heat(squads_alive=3), "rockets and a hold cool it")
    check(F.heat(squads_alive=12) == 1.0 and F.heat() == 0.0, "heat clamps to 0..1")
    check(F.heat_zone(0.55, tier=2) == "hot" and F.heat_zone(0.55, tier=6) == "warm", "tier-scaled huddle thresholds")
    check(F.heat_zone(0.1, tier=2) == "warm", "Tier 2 never roams")
    check(len(F.squads([(0, 0), (1, 0), (2, 1), (30, 30), (31, 30)])) == 2, "squads: two groups")
    # survive and retreat (section 2.5)
    check((F.survive(F.SPARTAN, 4), F.survive(F.SPARTAN, 2), F.survive(F.SPARTAN, 1), F.survive(F.ELITE)) ==
          (0.35, 0.5, 0.65, 0.5), "survive thresholds")
    check(F.retreat_bias(F.ELITE) == 1.4 and F.retreat_bias(F.SPARTAN) == 1.2, "retreat biases")
    # pressures (section 2.2)
    check(abs(F.spartan_pressure(True, True, 1, False) - 1.2) < 1e-9 and
          abs(F.spartan_pressure(False, False, 4, True) - 0.2) < 1e-9, "spartan pressure")
    check(F.elite_pressure(True, True, 2) == 1.0 and F.elite_pressure(False, False, 4, near_generator=True) == 0.9,
          "player Elite pressure")
    check(F.generator_defend(1.0, False, False, False) == 0.3 and F.generator_defend(0.4, False, False, False) == 1.0
          and F.generator_defend(1.0, True, False, True) == 0.1 and F.generator_defend(1.0, True, False, True, True) == 1.0,
          "generator defend pressure")
    check(F.generator_destroy(1.0, True, 2) == 0.2 and F.generator_destroy(1.0, False, 0) == 1.0
          and F.generator_destroy(0.2, True, 3) == 1.0, "generator destroy pressure")
    # lock the generator? (section 9.3)
    lk = dict(hit=False, squad_near_alone=False, elite_near_moving=False, elite_near_still=False, tier=4, wave_left=None,
              overlaps_cooldown=False, enemy_near=False, sudden_death=False)
    check(F.lock_now(**{**lk, "hit": True}), "lock: taking damage")
    check(F.lock_now(**{**lk, "squad_near_alone": True}), "lock: a squad within 30 ft, the guard alone")
    check(F.lock_now(**{**lk, "elite_near_moving": True}), "lock: a player Elite within 20 ft, moving")
    check(not F.lock_now(**{**lk, "elite_near_still": True, "tier": 5}), "no lock: a still Elite baits a Tier 5 guard")
    check(not F.lock_now(**{**lk, "squad_near_alone": True, "wave_left": 3}), "no lock: the wave is down to 3")
    check(not F.lock_now(**{**lk, "overlaps_cooldown": True}), "no lock: the cooldown would overlap, nobody near")
    check(not F.lock_now(**{**lk, "hit": True, "sudden_death": True}), "Sudden Death: cannot lock")
    # leave the huddle? (section 9.3)
    check(F.leave_huddle("hot", 3, False) == "roamer_support", "wave down to 3, no Elite seen: roamer and support")
    check(F.leave_huddle("hot", 6, True, drop_ft=8) == "nearest", "a drop within 10 ft: the nearest")
    check(F.leave_huddle("warm", 6, True, drop_ft=40) == "roamer", "a far drop, warm: the roamer")
    check(F.leave_huddle("warm", 6, True, gen_attacked=True) == "rotator", "a generator under attack, warm: rotator")
    check(F.leave_huddle("hot", 6, True, gen_low=True) == "rotator_support", "under 30 percent, hot: rotator and support")
    check(F.leave_huddle("hot", 6, True, compromised=True) == "all", "compromised: all")
    check(F.leave_huddle("hot", 6, True, drop_ft=40) is None, "anything else while hot: nobody")
    # commit to a Spartan? (section 9.3)
    ec = dict(isolated_down_pair=False, lives=4, power_facing=False, own_health=1.0, last_minute_low=False,
              boss_at_door=False)
    check(F.elite_commit(**{**ec, "isolated_down_pair": True}) == "yes", "commit: isolated, shields down, a pair")
    check(F.elite_commit(**{**ec, "lives": 1}) == "all", "commit: lives at 1, all")
    check(F.elite_commit(**{**ec, "isolated_down_pair": True, "power_facing": True}) == "no", "no: rockets facing")
    check(F.elite_commit(**{**ec, "lives": 1, "own_health": 0.4}) == "no", "no: under half, regenerate")
    check(F.elite_commit(**{**ec, "lives": 1, "last_minute_low": True}) == "no", "no: the last minute, stall")
    check(F.elite_commit(**{**ec, "boss_at_door": True}) == "back", "Boss wave: from the back entrance")
    # roles (sections 2.3, 4.1, 6.1)
    check(F.spartan_roles(4)[0] == "anchor" and "roamer" in F.spartan_roles(4), "Spartans: an anchor and a roamer")
    check("roamer" not in F.spartan_roles(4, zone="hot"), "hot: no roamer")
    check(F.spartan_roles(4, generators=3) == ["generator_guard"] * 3 + ["rotator"], "3 generators: 3 guards, 1 rotator")
    check(F.spartan_roles(4, generators=2) == ["generator_guard", "generator_guard", "rotator", "anchor"],
          "2 generators: 2 guards, a rotator, an anchor")
    check(F.spartan_roles(4, generators=1)[:2] == ["generator_guard"] * 2, "1 generator: two guards")
    check("breaker" in F.elite_roles(1, generators=2, unlocked=1), "an unlocked generator: a breaker")
    check(sorted(F.elite_roles(4, generators=3, unlocked=1)) == ["breaker", "breaker", "distractor", "shadow"],
          "four Elites on generators: a distractor, two breakers, a shadow")
    check(F.elite_roles(4, late_low=True).count("stalker") >= 3, "late and low: the stalkers run the clock")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("firefight OK")


if __name__ == "__main__":
    main()
