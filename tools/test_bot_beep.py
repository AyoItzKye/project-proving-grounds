"""GitHub #22: a bot's respawn countdown must not beep for the person (Reach, ODST, Halo 3).

native/spawnhook.cpp mutes the game's 2D interface sound while a bot's respawn handler runs. Checks: every hook in its
table names a DLL, and its 8 head bytes are the bytes at that RVA in the MCC 1.3528 DLLs (backups/mcc-2025.08.16);
the Reach and ODST interface-sound and respawn-handler hooks exist; the detours drop the sound only under the bot flag.
usage: python -I tools/test_bot_beep.py   (exit 1 on a failure)
"""
import os, re, sys
import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DLLS = {"haloreach.dll": "backups/mcc-2025.08.16/haloreach/haloreach.dll",
        "halo3odst.dll": "backups/mcc-2025.08.16/halo3odst/halo3odst.dll",
        "halo3.dll": "backups/mcc-2025.08.16/halo3/halo3.dll"}

src = open(os.path.join(ROOT, "native", "spawnhook.cpp"), encoding="utf-8").read()
heads = {m[0]: bytes(int(b, 16) for b in m[1].split(","))
         for m in re.findall(r"static const uint8_t (\w+_HEAD)\[8\] = \{([^}]*)\};", src)}
rows = re.findall(r'\{ L"([\w.]+)", "([\w ]+)", (0x[0-9A-Fa-f]+), (\w+_HEAD),', src)
fails = []
want = {("haloreach.dll", "interface sound"), ("haloreach.dll", "respawn handler"),
        ("halo3odst.dll", "interface sound"), ("halo3odst.dll", "respawn handler"),
        ("halo3.dll", "interface sound"), ("halo3.dll", "respawn handler")}
missing = want - {(d, n) for d, n, _, _ in rows}
if missing:
    fails.append(f"hooks missing: {sorted(missing)}")
pes = {}
for dll, name, rva, head in rows:
    path = os.path.join(ROOT, DLLS[dll])
    if not os.path.exists(path):
        print(f"skip head check (no {DLLS[dll]})")
        continue
    if dll not in pes:
        pes[dll] = (pefile.PE(path, fast_load=True), open(path, "rb").read())
    pe, data = pes[dll]
    off = pe.get_offset_from_rva(int(rva, 16))
    if data[off:off + 8] != heads[head]:
        fails.append(f"{dll}+{rva} {name}: head {data[off:off + 8].hex(' ')} != {head}")
for det in ("h_hr_ui_sound", "h_od_ui_sound", "h_h3_ui_sound"):
    if not re.search(det + r"\([^)]*\) \{\s*if \(!t_bot_tick\)", src):
        fails.append(f"{det} does not play only outside a bot's respawn handler")
for det in ("h_hr_respawn_tick", "h_od_respawn_tick", "h_h3_respawn_tick"):
    at = src.find(det + "(uint32_t player) {")
    body = src[at:src.find("\n}\n", at)] if at >= 0 else ""
    if "t_bot_tick = is_bot(player);" not in body or "t_bot_tick = false;" not in body:
        fails.append(f"{det} does not set and clear the bot flag around the game's handler")
# GitHub #21: Halo CE's HUD message (pickups) for a bot is dropped (native/botcore.cpp hud_message_hook): the hook's RVA
# is the function Ghidra names FUN_180ada904 (its prologue in 1.3528's halo1.dll) and the detour drops bot players only
core = open(os.path.join(ROOT, "native", "botcore.cpp"), encoding="utf-8").read()
m = re.search(r"RVA_HUD_MESSAGE = (0x[0-9A-Fa-f]+);", core)
h1 = os.path.join(ROOT, "backups/mcc-2025.08.16/halo1/halo1.dll")
if not m:
    fails.append("botcore.cpp has no RVA_HUD_MESSAGE (#21)")
elif os.path.exists(h1):
    pe = pefile.PE(h1, fast_load=True)
    data = open(h1, "rb").read()
    off = pe.get_offset_from_rva(int(m[1], 16))
    want = bytes.fromhex("40 53 55 56 57 41 56 41 57 48 81 EC 88 00 00")   # push rbx (REX) .. r15; sub rsp, 0x88
    if data[off:off + len(want)] != want:
        fails.append(f"halo1.dll+{m[1]} HUD message: head {data[off:off + 15].hex(' ')} (want {want.hex(' ')})")
body = core[core.find("hud_message_hook(uint32_t player"):]
body = body[:body.find("\n}\n")]
if "bot_player_index[i] == index" not in body or "return;" not in body or "g_hud_message_orig(" not in body:
    fails.append("hud_message_hook does not drop bot players' messages only (#21)")
for f in fails:
    print("FAIL", f)
print("bot respawn beep muted:", "FAIL" if fails else "OK")
sys.exit(1 if fails else 0)
