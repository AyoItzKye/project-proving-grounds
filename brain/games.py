"""What each MCC game lets a player do: one profile per game, read by the brain where the games differ (jump heights,
health, shields, radar, sprint, abilities: what a player can and cannot do in that game).

Sources: the games' tag data (H3 / Reach / H4 / H2A / ODST editing kits, exported) and Halopedia's tag-cited infoboxes,
gathered Nov 11 (logs/tmp/games_nov11/agentA, agentB). Values marked "?" are not verified and are not used.

health:   "packs"  health never comes back by itself; health packs restore it (CE, ODST)
          "thirds" it comes back to the next third over time (Reach; its health packs top it up)
          "full"   it comes back whole after a delay (H2, H3, H2A, H4)
shield:   (delay s, full recharge s) after the last hit
radar:    the motion tracker's default range in world units where known (CE: 20 u, its tag; the others' "25 m" is
          not yet tied to world units: None)
radar_still / radar_crouch: standing still / crouch-walking hides a player from it
sprint, abilities, equipment, dual_wield: what a player has
fall:     (hurt from, dead from) world units of drop; None: no fall damage
"""

GAMES = {
    "ce":    dict(health="packs", shield=(6.0, 4.0), radar=20.0, radar_still=True, radar_crouch=True, sprint=False,
                  abilities=False, equipment=False, dual_wield=False, fall=(3.0, 6.0), assassinate=False),
    "h2":    dict(health="full", shield=(4.25, 1.75), radar=None, radar_still=True, radar_crouch=True, sprint=False,
                  abilities=False, equipment=False, dual_wield=True, fall=None, assassinate=False),
    "h2a":   dict(health="full", shield=(5.0, 2.0), radar=None, radar_still=True, radar_crouch=True, sprint=False,
                  abilities=False, equipment=False, dual_wield=True, fall=None, assassinate=False),
    "h3":    dict(health="full", shield=(5.0, 2.0), radar=None, radar_still=True, radar_crouch=True, sprint=False,
                  abilities=False, equipment=True, dual_wield=True, fall=None, assassinate=False),
    "odst":  dict(health="packs", shield=(5.0, 3.0), radar=None, radar_still=True, radar_crouch=True, sprint=False,
                  abilities=False, equipment=False, dual_wield=False, fall=(6.0, 10.0), assassinate=False),
    "reach": dict(health="thirds", shield=(6.0, 3.0), radar=None, radar_still=True, radar_crouch=True, sprint=True,
                  abilities=True, equipment=False, dual_wield=False, fall=None, assassinate=True),
    "h4":    dict(health="full", shield=(7.0, 3.0), radar=None, radar_still=True, radar_crouch=True, sprint=True,
                  abilities=True, equipment=False, dual_wield=False, fall=None, assassinate=True),
}


def profile(game):
    """The game's profile (Halo 3's for one not known)."""
    return GAMES.get(game, GAMES["h3"])


def needs_health_packs(game):
    """Health that does not come back whole by itself: a hurt bot goes for a health pack (CE, ODST; Reach's thirds)."""
    return profile(game)["health"] in ("packs", "thirds")


def plain_jump(game, seconds=False):
    """How high a plain jump lifts the feet in this game (world units), or with seconds=True how long it takes to
    get there: its jump speed and gravity measured in real matches (tools/jumpphys.py PHYS: Halo 3 1.11 u in 0.74 s,
    Reach 0.67 u in 0.57 s, CE 0.65 u in 0.64 s)."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
    from jumpphys import PHYS
    _, v0, g, _ = PHYS.get(game, PHYS["h3"])
    return v0 / g if seconds else v0 * v0 / (2 * g)


def radar_range(game):
    """The motion tracker's range in world units where the game's tag gives it (CE: 20), else None."""
    return profile(game)["radar"]
