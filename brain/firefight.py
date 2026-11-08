"""Reach (and ODST) Firefight, the mode add-on: what each NPC is and how much it matters, the Spartans' heat, the sides'
roles and the decision tables of docs/bot-brain/11-reach-firefight-versus.md (Versus, Generator Defense) and
docs/bot-brain/12-firefight-enemy-handbook.md (the enemy roster). Pure functions; tools/live_bots.py fills snap.ff,
brain/bot.py (threat, retreat) and brain/director.py (roles) use them. tools/test_firefight.py checks the tables.

An NPC's rank is its character tag's name (brain/live.py ai_rank: grunt_major, jackal_sniper, elite_ultra, ...), a
player's side the unit's side byte: 1 Spartans, 7 Elites (they swap at each turn of Versus and Generator Defense)."""
import math

SPARTAN, ELITE = 1, 7
FT = 0.1                      # world units per foot (1 u = 10 ft)
# the guide's bands, in u: Melee, Short, Medium, Long (brain/bot.py threat's own steps: 0.8, 4, 12, 30)
BANDS = (0.8, 4.0, 12.0)


def band(d):
    return 0 if d < BANDS[0] else 1 if d < BANDS[1] else 2 if d < BANDS[2] else 3


# rank -> (lethality at Melee, Short, Medium, Long; value: priority A 0.9, B 0.6, C 0.35, D 0.1). Handbook section 3
# (Reach) and 2 (ODST). Matched by the most specific key in the rank's name; the first match wins.
RANKS = (
    ("engineer", (0.3, 0.3, 0.3, 0.3), 1.0),          # overshields everything near it: first in any wave (ladder 1)
    ("hunter", (1.0, 0.9, 0.7, 0.5), 0.85),           # A as a pair at Medium or closer
    ("chieftain", (1.0, 0.9, 0.9, 0.8), 0.9),         # boss: hammer or a heavy weapon
    ("general", (1.0, 0.8, 0.7, 0.5), 0.9),           # Elite General: a walking boss
    ("grunt_heavy", (0.4, 0.6, 0.9, 0.8), 0.9),       # fuel rod or plasma launcher: the huddle killer
    ("grunt_specops", (0.4, 0.6, 0.9, 0.8), 0.9),
    ("jackal_sniper", (0.3, 0.5, 0.7, 0.9), 0.8),     # needle rifle or focus rifle on high ground
    ("heretic_heavy", (0.6, 0.8, 0.9, 1.0), 0.9),     # rockets or a laser
    ("heretic_sniper", (0.4, 0.5, 0.8, 1.0), 0.85),
    ("elite_specops", (1.0, 1.0, 0.5, 0.3), 0.7),     # camo and swords
    ("elite_jetpack", (0.7, 0.7, 0.7, 0.5), 0.65),    # Ranger: over the hold
    ("elite_ultra", (1.0, 0.8, 0.7, 0.5), 0.6),
    ("elite_officer", (0.9, 0.7, 0.6, 0.4), 0.6),     # (the Major's tag on the Firefight maps)
    ("elite_major", (0.9, 0.7, 0.6, 0.4), 0.6),
    ("elite", (0.8, 0.6, 0.5, 0.3), 0.35),            # Minor
    ("heretic", (0.6, 0.6, 0.6, 0.5), 0.5),
    ("skirmisher_champion", (0.5, 0.7, 0.6, 0.5), 0.6),
    ("skirmisher_commando", (0.5, 0.7, 0.7, 0.6), 0.6),
    ("skirmisher", (0.5, 0.7, 0.6, 0.4), 0.35),
    ("brute_major", (1.0, 0.8, 0.4, 0.2), 0.5),       # hammer when leading Brutes
    ("brute_captain", (0.9, 0.7, 0.5, 0.3), 0.6),     # (ODST)
    ("brute", (0.8, 0.6, 0.4, 0.2), 0.35),
    ("drone", (0.3, 0.5, 0.4, 0.2), 0.3),
    ("bugger", (0.3, 0.5, 0.4, 0.2), 0.3),
    ("jackal", (0.4, 0.4, 0.2, 0.1), 0.35),           # shield Jackals: C, B at the door
    ("grunt_ultra", (0.3, 0.4, 0.2, 0.1), 0.35),
    ("grunt", (0.3, 0.4, 0.2, 0.1), 0.1),             # Minor, Major: D
    ("marine", (0.3, 0.4, 0.3, 0.2), 0.2),            # (human AI: an Elite's enemy)
)
UNKNOWN = ((0.5, 0.5, 0.4, 0.3), 0.4)
PLAYER_ELITE = ((0.9, 0.85, 0.8, 0.5), 0.8)          # a needle rifle at Medium 0.8 (guide 11 section 3.1)
PLAYER_SPARTAN = ((0.9, 0.85, 0.8, 0.6), 0.8)
BIG = ("hunter", "chieftain", "general", "heretic_heavy")   # what warrants rockets, and the heat's big term
POWER = ("rockets", "spartan_laser", "sniper", "fuelrod", "plasma_launcher", "grenade_launcher")   # (section 3.2)


def entry(rank):
    """(lethality per band, value) of an NPC by its rank's name."""
    r = (rank or "").lower()
    for key, lethal, value in RANKS:
        if key in r:
            return lethal, value
    return UNKNOWN


def threat_mult(rank, d, player_side=None, versus=False, lives=None, last_three=False):
    """The Firefight factor on brain/bot.py threat for an enemy: lethality at its band times its value (guide 11
    section 3.1, the product; exposure stays the core scorer's), 1.0 for an even enemy (lethality 0.5, value 0.5).
    A player Elite in Versus is worth a life: at 2 lives or fewer it outranks everything but a Hunter at Melee band.
    The last three of a wave end it (value 0.8)."""
    b = band(d)
    if rank and "hunter" in rank.lower() and b == 0:
        return HUNTER_MELEE                       # the one thing over a player Elite when the lives are low
    if player_side == ELITE:
        lethal, value = PLAYER_ELITE
        if versus and lives is not None and 0 <= lives <= 2:
            return ELITE_LOW_LIVES
        if versus:
            value = 1.0
    elif player_side == SPARTAN:
        lethal, value = PLAYER_SPARTAN
    else:
        lethal, value = entry(rank)
    if last_three:
        value = max(value, 0.8)
    return max(0.25, min(2.5, (0.3 + lethal[b]) * (0.3 + value) / 0.64))


HUNTER_MELEE, ELITE_LOW_LIVES = 2.8, 2.6     # (the formula tops out at 2.5: a Chieftain or General at Melee band)
LOCK_GAP = 10.0               # s between two locks started by the team (guide 11 9.4: never all locked at once)
LOCK_TIME = 30.0              # s a lock holds (about 30 s, guide 11 1.3)


def heat(squads_alive=0, big=False, elite_majority=False, player_elites=0, lives=None, unshielded=False,
         generator_hit=False, power_weapon=False, held=False):
    """Guide 11 section 2.4: 0 (cool) to 1 (hot) for the Spartans; the Elites read it inverted."""
    h = (0.15 * squads_alive + 0.25 * big + 0.15 * elite_majority + 0.10 * player_elites
         + 0.15 * (lives is not None and 0 <= lives <= 2) + 0.10 * unshielded + 0.10 * generator_hit
         - 0.10 * power_weapon - 0.10 * held)
    return max(0.0, min(1.0, h))


def squads(npcs, r=4.0):
    """NPC squads: groups of enemies within r of each other (a squad walks as one). npcs: [(x, y)]."""
    groups = []
    for x, y in npcs:
        for g in groups:
            if any(math.hypot(x - a, y - b) < r for a, b in g):
                g.append((x, y))
                break
        else:
            groups.append([(x, y)])
    return groups


def heat_zone(h, tier=4):
    """cool / warm / hot by the tier-scaled thresholds: Tier 2 huddles at 0.5 and never roams, Tier 6 huddles at 0.75
    and roams at 0.5; the default 0.35 / 0.65. tier: 1 Easy .. 6 (brain/profiles.py's four tiers map to 2, 3, 5, 6)."""
    roam, huddle = {1: (0.0, 0.5), 2: (0.0, 0.5), 3: (0.35, 0.65), 4: (0.35, 0.65), 5: (0.45, 0.7),
                    6: (0.5, 0.75)}.get(tier, (0.35, 0.65))
    return "hot" if h >= huddle else "cool" if h < roam else "warm"


def survive(side, lives=None):
    """The Survive threshold (shield fraction below which the bot breaks off, guide 11 section 2.5): Spartans 0.35 at
    4 lives, 0.5 at 2, 0.65 at 1 (the life pool is the team's health bar); Elites 0.5 (an Elite death is a Spartan
    life and a large score)."""
    if side == ELITE:
        return 0.5
    if lives is None or lives < 0 or lives >= 4:
        return 0.35
    return {3: 0.42, 2: 0.5, 1: 0.65, 0: 0.65}[lives]


def retreat_bias(side):
    """Retreat utility bias: Spartans 1.2, Elites 1.4 (guide 11 section 2.5)."""
    return 1.4 if side == ELITE else 1.2


def spartan_pressure(alone, shields_down, lives, power_facing):
    """Guide 11 section 2.2, the Elites' pick among Spartans: 0.5, +0.3 alone (no teammate within 30 ft), +0.2 shields
    down, +0.2 when the pool is at 1 (a kill ends the turn), -0.3 holding a power weapon facing us at Medium or longer."""
    return 0.5 + 0.3 * alone + 0.2 * shields_down + 0.2 * (lives == 1) - 0.3 * power_facing


def elite_pressure(versus, isolated, lives, near_generator=False):
    """The Spartans' pressure on a player Elite: Versus 0.6 (+0.2 isolated from NPCs, +0.2 at 2 lives or fewer: a kill
    gives one back); Generator Defense 0.4, 0.9 within 15 ft of a generator."""
    if not versus:
        return 0.9 if near_generator else 0.4
    return 0.6 + 0.2 * isolated + 0.2 * (lives is not None and 0 <= lives <= 2)


def generator_defend(health, enemy_near, hit, locked, expires_first=False):
    """Spartans' generator pressure: 0.3 idle, 0.7 an enemy within 30 ft, 1.0 hit or under half, 0.1 locked, 1.0 for
    the lock that expires first with enemies near."""
    if locked:
        return 1.0 if expires_first and enemy_near else 0.1
    if hit or health < 0.5:
        return 1.0
    return 0.7 if enemy_near else 0.3


def generator_destroy(health, locked, defenders):
    """Elites' generator pressure: 0.2 locked, 0.6 unlocked and defended, 1.0 undefended or under 30 percent."""
    if health < 0.3:
        return 1.0
    if locked:
        return 0.2
    return 0.6 if defenders else 1.0


def lock_now(hit, squad_near_alone, elite_near_moving, elite_near_still, tier, wave_left, overlaps_cooldown,
             enemy_near, sudden_death):
    """Guide 11 section 9.3, lock the generator? (only guards lock; at most one lock started per 10 s team-wide)."""
    if sudden_death:
        return False                              # cannot
    if hit:
        return True
    if wave_left is not None and wave_left <= 3:
        return False
    if elite_near_still and tier >= 5:
        return False                              # baiting the lock: shoot instead
    if squad_near_alone or elite_near_moving:
        return True
    if overlaps_cooldown and not enemy_near:
        return False
    return False


def leave_huddle(zone, wave_left, elite_seen_10s, drop_ft=None, gen_attacked=False, gen_low=False, compromised=False):
    """Guide 11 section 9.3, leave the huddle? -> who goes: None, "roamer_support", "nearest", "roamer", "rotator",
    "rotator_support", "all"."""
    if compromised:
        return "all"
    if wave_left is not None and wave_left <= 3 and not elite_seen_10s:
        return "roamer_support"
    if drop_ft is not None and drop_ft <= 10:
        return "nearest"
    if zone == "hot":
        return "rotator_support" if gen_low else None
    if drop_ft is not None:
        return "roamer"
    if gen_attacked:
        return "rotator"
    return None


def elite_commit(isolated_down_pair, lives, power_facing, own_health, last_minute_low, boss_at_door):
    """Guide 11 section 9.3, commit to a Spartan? -> "no", "yes", "all", "back" (from the back entrance)."""
    if own_health < 0.5:
        return "no"                               # regenerate
    if last_minute_low:
        return "no"                               # stall: the clock wins the turn
    if lives == 1:
        return "all"
    if power_facing:
        return "no"
    if boss_at_door:
        return "back"
    return "yes" if isolated_down_pair else "no"


def spartan_roles(n, generators=0, zone="cool"):
    """Guide 11 section 2.3 and 4.1: anchor always; generator guards in Generator Defense (one per generator the team
    can cover, two at one generator), the rest rotators; else roamer and support. Hot: no roamer."""
    if n <= 0:
        return []
    if generators:
        guards = min(n, 2 if generators == 1 else generators)
        roles = ["generator_guard"] * guards
        if generators == 2 and n >= 4:
            roles = ["generator_guard", "generator_guard", "rotator", "anchor"]
        elif len(roles) < n:
            roles += ["rotator"] + ["anchor"] * (n - guards - 1)
        return roles[:n]
    order = ["anchor", "support" if zone == "hot" else "roamer", "support", "anchor"]
    return order[:n] if n <= 4 else order + ["support"] * (n - 4)


def elite_roles(n, versus=True, generators=0, unlocked=0, late_low=False):
    """Guide 11 section 2.3 and 6.1: hunter, breaker (Generator Defense: one whenever a generator is unlocked; with four
    Elites one distractor, two breakers, one shadow), shadow (moves with the biggest NPC squad), stalker (Versus: baits
    and runs the clock, late in a turn with the Spartans low)."""
    if n <= 0:
        return []
    if generators:
        base = ["breaker", "shadow", "breaker", "distractor"] if unlocked else ["hunter", "shadow", "hunter", "breaker"]
        return (base + ["hunter"] * n)[:n]
    if late_low:
        return (["stalker", "stalker", "shadow", "stalker"] + ["stalker"] * n)[:n]
    return (["hunter", "shadow", "hunter", "stalker" if versus else "hunter"] + ["hunter"] * n)[:n]
