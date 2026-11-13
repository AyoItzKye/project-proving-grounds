"""The launcher's Settings card: the player's options in user/settings.json (kept by updates and Repair, like
user/update.json). botcore reads the file too (native/ce_ragdoll.cpp: "ce_ragdolls", checked every 2 s), so an option
changes a running game. A missing file or key is the default.

DEFAULTS: ce_ragdolls (bool, True): Halo: CE multiplayer bodies as ragdolls (Halo 2's always are: no option)."""
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PATH = os.path.join(ROOT, "user", "settings.json")
DEFAULTS = {"ce_ragdolls": True}


def load(path=PATH):
    try:
        got = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        got = {}
    return {k: type(v)(got[k]) if isinstance(got.get(k), type(v)) else v for k, v in DEFAULTS.items()}


def save(changes, path=PATH):
    """Known keys of the right type from changes into the file; unknown keys and wrong types refused (ValueError).
    Returns every setting."""
    if not isinstance(changes, dict):
        raise ValueError("settings: a JSON object of name: value")
    bad = [k for k, v in changes.items() if k not in DEFAULTS or not isinstance(v, type(DEFAULTS[k]))]
    if bad:
        raise ValueError(f"not a setting: {', '.join(bad)}")
    st = load(path)
    st.update(changes)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, path)
    return st
