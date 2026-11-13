"""tools/settings.py, the launcher's Settings card: defaults with no file, a broken file or a wrong type; a saved switch
read back; unknown names, wrong types and a body that is not an object refused (the file untouched); the file is JSON
botcore's reader finds ("ce_ragdolls": false).

usage: python -I test_settings.py      -> "settings OK"
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings  # noqa: E402

d = tempfile.mkdtemp()
p = os.path.join(d, "user", "settings.json")
assert settings.load(p) == {"ce_ragdolls": True}, "no file: the defaults"
os.makedirs(os.path.dirname(p))
open(p, "w").write("{not json")
assert settings.load(p) == {"ce_ragdolls": True}, "a broken file: the defaults"
open(p, "w").write('{"ce_ragdolls": "no"}')
assert settings.load(p) == {"ce_ragdolls": True}, "a wrong type in the file: the default"
assert settings.save({"ce_ragdolls": False}, p) == {"ce_ragdolls": False}
assert settings.load(p) == {"ce_ragdolls": False}, "saved off, read back off"
assert '"ce_ragdolls": false' in open(p).read(), "what botcore's reader looks for"
for bad in ({"ce_ragdolls": 0}, {"nonsense": True}, ["ce_ragdolls"]):
    try:
        settings.save(bad, p)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted {bad!r}")
assert json.load(open(p)) == {"ce_ragdolls": False}, "a refused change leaves the file alone"
assert settings.save({"ce_ragdolls": True}, p) == {"ce_ragdolls": True}
print("settings OK")
