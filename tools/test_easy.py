"""Easy bots. No detours for guns (only one it all but walks over); a man it saw stays in mind a few seconds."""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot, EYES_KEEP  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def main():
    m = get_map("h3_construct")
    easy = Bot(3, 0, make_profile("novice", "rusher", random.Random(3)), m, random.Random(3))
    easy.game = "h3"
    me = PlayerState(3, 0, "bot", Vec(10.0, -3.0, 3.2), alive=True, weapon="assault_rifle",
                     weapons=["assault_rifle"], ammo=[200], mag=[32])
    snap = Snapshot(5.0, [me])
    snap.ground_weapons = [("battle_rifle", Vec(14.0, -3.0, 3.2))]
    assert easy.upgrade_point(me, snap) is None, "Easy went out of its way (4 u) for a battle rifle"
    snap.ground_weapons = [("battle_rifle", Vec(11.2, -3.0, 3.2))]
    assert easy.upgrade_point(me, snap) is not None, "Easy walked over a battle rifle and left it"

    # the man it saw duck behind cover 2 s ago: still watched (it was 0.5 s for Easy)
    easy.now = 10.0
    easy.per.beliefs[7] = Belief(Vec(14.0, 0.0, 3.2), Vec(), 10.0 - 2.0, False, "eyes")
    easy.look_point(me, Vec(0.0, -3.0, 3.2))
    assert easy.att[0] == "watch", f"Easy forgot the man around the corner after 2 s ({easy.att})"
    easy.now = 10.0 + EYES_KEEP
    easy.look_point(me, Vec(0.0, -3.0, 3.2))
    assert easy.att[0] != "watch", "Easy stared at an old sighting forever"

    # (the player: yes to Easy toward 70%): shot from behind 1 s ago, it is still turning to the shots, at a spin
    # (its 0.5 s ran out before its turn ended: 22-33% of first hits on Easy went unanswered live, the player 6%)
    easy.per.beliefs.clear()
    easy.now = 20.0
    easy.per.beliefs[8] = Belief(Vec(10.0, -12.0, 3.2), Vec(), 19.0, False, "hit")
    easy.aim.whip = 0.0
    easy.look_point(me, Vec(0.0, -3.0, 3.2))
    assert easy.att[0] == "watch" and "hit" in easy.att[1] and easy.aim.whip >= 0.35, \
        f"Easy shot from behind 1 s ago: {easy.att}, spin {easy.aim.whip} (want turned to the shots, 0.35 at least)"

    # and it throws grenades into a fight that goes on (never before: the pressure grenade was tactics > 0.15 only)
    nades = 0
    foe = PlayerState(9, 1, "f", Vec(20.0, -3.0, 3.2), alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
    easy.engaged_since, easy.goal, easy.notes = None, ("fight", 9), []
    for k in range(180):                                   # the fight opened at 25 s (its opener off), then 5 s of it
        t = 25.0 if k == 0 else 30.0 + k / 30
        easy.per.beliefs[9] = Belief(foe.pos, Vec(), t, True, "eyes")
        easy.per.last_seen[9] = t
        easy.per.recognized.add(9)
        act = Action()
        easy.fight(t, 1 / 30, me, Snapshot(t, [me, foe]), 9, act, lambda p, q, **kw: q)
        easy.nade_open = False
        nades += bool(act.grenade) and k > 0
    assert nades >= 1, "Easy, 5 s into a fight 10 u off: no grenade thrown (want some, like a person)"
    print(f"easy OK (shot from behind: turned at spin {easy.aim.whip:.2f}; {nades} grenades in a 5 s fight)")


if __name__ == "__main__":
    main()
