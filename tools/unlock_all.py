"""All armor in MCC's customization menus, for Anti-Cheat Disabled play only.

MCC lists every cosmetic in Data/UI/unlockdb.xml with a state (eUnlockState_Unlocked / LockedVisible /
LockedHidden). This sets the LockedVisible items of eUnlockCategory_Customization (armor of every game) to
Unlocked. Hidden items (unreleased, event-only) are left alone. Nothing online is touched: the file is local, and
progression with EAC off is not saved to the account. The original is copied once to unlockdb.xml.orig next to it
(and to backups/ in this repo); --restore puts it back. Restore it (or verify the game files in Steam) before
playing with Easy Anti-Cheat on: a changed game file there can be flagged. An MCC update replaces the file: run
this again after one.

usage: python -I unlock_all.py [--restore] [--check] [--file <unlockdb.xml>]
"""
import os
import re
import shutil
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

GAME = paths.mcc()
HERE = os.path.dirname(os.path.abspath(__file__))
BACKUPS = os.path.join(HERE, "..", "backups")
ROW = re.compile(r'<Unlock [^>]*category="eUnlockCategory_Customization"[^>]*/>')


def unlock(text):
    """(new text, items changed): the customization rows' LockedVisible state set to Unlocked."""
    n = 0

    def one(m):
        nonlocal n
        row = m.group(0)
        if 'state="eUnlockState_LockedVisible"' not in row:
            return row
        n += 1
        return row.replace('state="eUnlockState_LockedVisible"', 'state="eUnlockState_Unlocked"')
    return ROW.sub(one, text), n


def counts(text):
    rows = ROW.findall(text)
    return {s: sum(f'state="eUnlockState_{s}"' in r for r in rows) for s in ("Unlocked", "LockedVisible", "LockedHidden")}


def selftest():
    sample = ('<Unlock id="a" type="t" category="eUnlockCategory_Customization" state="eUnlockState_LockedVisible"/>\n'
              '<Unlock id="b" type="t" category="eUnlockCategory_Customization" state="eUnlockState_LockedHidden"/>\n'
              '<Unlock id="c" type="t" category="eUnlockCategory_Nameplate" state="eUnlockState_LockedVisible"/>\n')
    out, n = unlock(sample)
    assert n == 1 and counts(out) == {"Unlocked": 1, "LockedVisible": 0, "LockedHidden": 1}, (n, counts(out))
    assert 'id="c" type="t" category="eUnlockCategory_Nameplate" state="eUnlockState_LockedVisible"' in out
    assert unlock(out) == (out, 0)                              # a second run changes nothing


def main():
    selftest()
    args = sys.argv[1:]
    path = args[args.index("--file") + 1] if "--file" in args else os.path.join(GAME, "Data", "UI", "unlockdb.xml")
    orig = path + ".orig"
    if "--restore" in args:
        if not os.path.exists(orig):
            sys.exit(f"no backup at {orig}")
        shutil.copy2(orig, path)
        print("restored", path, counts(open(path, encoding="utf-8").read()))
        return
    text = open(path, encoding="utf-8", newline="").read()      # the file's own CRLF line ends, kept
    if "--check" in args:
        print(path, counts(text))
        return
    if not os.path.exists(orig):
        shutil.copy2(path, orig)
        os.makedirs(BACKUPS, exist_ok=True)
        shutil.copy2(path, os.path.join(BACKUPS, "unlockdb.xml.orig"))
    new, n = unlock(text)
    if n:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print(f"unlocked {n} armor items in {path}: {counts(new)} (backup {orig})")


if __name__ == "__main__":
    main()
