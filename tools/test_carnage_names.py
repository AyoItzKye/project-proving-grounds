"""tools/carnage_names.py: a bot row MCC left blank (made-up Xbox id) gets its name, clan tag, botcore's service tag
and its team; the player's row, unknown ids and bot rows MCC named already (botcore's hooks) stay as they are.

usage: python -I test_carnage_names.py      -> "carnage names OK"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carnage_names import bot_tag, fix  # noqa: E402

ROW = ('<Player mXboxUserId="{id}" isGuest="false" mGameMode="6" mGamertagText="{gt}" ClantagText="{ct}" '
       'EmblemTexture0="49" ServiceId="{sid}" mTeamId="0" Score="1">')


def main():
    xml = "\n".join([ROW.format(id="0xB07B07B000000006", gt="", ct="UNSC", sid="117"),
                     ROW.format(id="0x0009000012345678", gt="PlayerOne", ct="", sid="X42"),
                     ROW.format(id="0xB07B07B000000009", gt="", ct="UNSC", sid="117")])
    out = fix(xml, {6: ("Falcon65", 1)}).splitlines()
    fails = []
    if 'mGamertagText="Falcon65" ClantagText=""' not in out[0] or 'ServiceId="F65" mTeamId="1"' not in out[0]:
        fails.append(f"bot row: {out[0]}")
    if out[1] != xml.splitlines()[1] or out[2] != xml.splitlines()[2]:
        fails.append("the player's row or an unknown id changed")
    named = ROW.format(id="0xB07B07B000000007", gt="SilentGrunt", ct="KOTH", sid="SGI")
    if fix(named, {7: ("SilentGrunt", 0)}, lambda n: "") != named:
        fails.append("a row MCC named (botcore's hooks) was rewritten")
    if 'ClantagText="KOTH"' not in fix(xml.splitlines()[0], {6: ("Falcon65", 1)}, lambda n: "KOTH"):
        fails.append("a blank bot row did not get the bot's clan tag")
    if [bot_tag(n) for n in ("Hawk983", "Teabag", "xXRocketXx", "Salty117")] != ["H983", "TEA", "XRX", "S117"]:
        fails.append("bot_tag differs from botcore's hr_bot_tag")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("carnage names OK")


if __name__ == "__main__":
    main()
