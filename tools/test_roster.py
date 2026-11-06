"""Offline checks for the BOTS panel's list (the player: a bots panel with multiple teams, bots easy to move
around): botcore.ini's bot lines parse (tools/botctl.py roster), and tools/play.py adds exactly those
bots: Halo: CE plays the third and later teams as red / blue, free for all gives every bot its own team, a
lobby never goes past 16 players, a person's name is not taken twice. The C++ side (the panel, its roster
operations) has its own self-test: native/bin/panel_preview.exe --selftest.

usage: python -I test_roster.py      -> "roster OK"
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
from play import roster_plan  # noqa: E402

INI = """enabled=1
red=7
blue=8
difficulty=3
lidar=0
lidar_players=16
roster=1
teams=3
bot=0,top,rusher,NobleJackal
bot=1,strong,any,Monitorx
bot=2,novice,sniper,Ghost, the 3rd
bot=9,bogus,nothing,Odd
bot=1,average,camper,
"""


def main():
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "botcore.ini")
        open(p, "w").write(INI)
        r = botctl.roster(p)
        no_ff = botctl.roster(p, firefight=True)               # (s170 and before: no Firefight list)
        open(p, "w").write(INI + "ffroster=1\nffbot=0,novice,sniper,FireOne\nffbot=0,top,any,FireTwo\n")
        ff, mp = botctl.roster(p, firefight=True), botctl.roster(p)
        open(p, "w").write(INI + "ffroster=1\n")                # Firefight's list emptied: no bots, not the 16's
        ff_empty = botctl.roster(p, firefight=True)
        open(p, "w").write("enabled=1\nred=4\nblue=4\n")      # a build from before the list: no list at all
        old = botctl.roster(p)
    if old is not None:
        fails.append("an ini without the list read as an (empty) list")
    # Firefight's own list (native botcore.cpp ffbot= lines): its bots only, the 16-player list untouched by it
    if no_ff is not None or ff_empty != [] or [b["name"] for b in ff or []] != ["FireOne", "FireTwo"] or mp != r:
        fails.append(f"Firefight list: none {no_ff}, empty {ff_empty}, read {ff}, the 16's {mp == r}")
    want = [dict(name="NobleJackal", team=0, tier="top", style="rusher"),
            dict(name="Monitorx", team=1, tier="strong", style="any"),
            dict(name="Ghost, the 3rd", team=2, tier="novice", style="sniper"),   # a name may hold a comma
            dict(name="Odd", team=7, tier="top", style="any")]                       # bad values: safe defaults
    if r != want:
        fails.append(f"parsed {r}")
    people = [dict(index=0, team=0, name="Player")]
    plan = roster_plan(r, people, True, "ce")
    if [t for t, _ in plan] != [0, 1, 0, 1]:
        fails.append(f"Halo: CE teams {plan} (want the third and later teams as red / blue)")
    plan = roster_plan(r, people, True, "reach")
    if [t for t, _ in plan] != [0, 1, 2, 7]:
        fails.append(f"Reach teams {plan}")
    plan = roster_plan(r, people, False, "h3")
    if len({t for t, _ in plan} | {0}) != 5:
        fails.append(f"free for all teams {plan} (want every bot its own team, none the player's)")
    crowd = [dict(index=i, team=i % 2, name=f"P{i}") for i in range(14)]
    if len(roster_plan(r, crowd, True, "reach")) != 2:
        fails.append("went past 16 players")
    plan = roster_plan([dict(name="Player", team=1, tier="top", style="any")], people, True, "reach")
    if plan[0][1].lower() == "player":
        fails.append("took a person's name")
    # Firefight holds 4 players in all (ODST crashed with 7, 15 and 16-25): botctl.player_cap, and every path of
    # play.py's bot adding (the panel's list, team games, free for all, LiDAR) goes through it
    if (botctl.player_cap("odst"), botctl.player_cap("reach", firefight=True), botctl.player_cap("h3")) != (4, 4, 16):
        fails.append("player cap: ODST / Firefight 4, other games 16")
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "play.py"), encoding="utf-8").read()
    if ("room = botctl.player_cap(o.game, firefight)" not in src or src.count("room > 0") < 2
            or "[:max(0, room)]" not in src):
        fails.append("play.py adds bots on a path the player cap does not cover")
    # Firefight takes the panel's list too (s169: it used made-up teammates, the panel's 3 never joined): its own
    # list, all on your team, and live_bots reads the same list for each bot's difficulty
    if ('team = players[0]["team"] if ff else team' not in src or "botctl.roster(o.roster, firefight=True)" not in src
            or '["--ff-list"]' not in src):
        fails.append("play.py: Firefight does not take the panel's Firefight list onto the player's team")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("roster OK")


if __name__ == "__main__":
    main()
