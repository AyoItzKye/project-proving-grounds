"""Offline check of how the mod finds MCC (brain/paths.py) and the launcher's MCC folder choice (GitHub issue #1): Steam
libraries in both libraryfolders.vdf formats, several MCC copies, the folder the player picks (or a folder near it),
HB_MCC over the choice, back to automatic, and how Play starts a copy Steam does not (tools/launch.py). Fake folder
layouts in logs/tmp/test_mcc_folder; the real Steam and the player's choice are not touched.

usage: python -I test_mcc_folder.py
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from brain import paths  # noqa: E402

TMP = os.path.join(ROOT, "logs", "tmp", "test_mcc_folder")


def mcc_copy(folder, game="halo3"):
    os.makedirs(os.path.join(folder, "MCC", "Binaries", "Win64"), exist_ok=True)
    open(os.path.join(folder, paths.GAME_EXE), "w").close()
    if game:
        os.makedirs(os.path.join(folder, game, "maps"), exist_ok=True)
        open(os.path.join(folder, game, "maps", "construct.map"), "w").close()
    return folder


def main():
    # the two formats of libraryfolders.vdf: today's ("path" entries, an "apps" list) and the older numbered one
    new = ('"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"C:\\\\Program Files (x86)\\\\Steam"\n\t\t"apps"\n\t\t{\n'
           '\t\t\t"976730"\t\t"145822487705"\n\t\t}\n\t}\n\t"1"\n\t{\n\t\t"PATH"\t\t"E:\\\\Games \\"SSD\\""\n\t}\n}')
    assert paths.library_paths(new) == [os.path.normpath("C:\\Program Files (x86)\\Steam"),
                                        os.path.normpath('E:\\Games "SSD"')], paths.library_paths(new)
    old = '"LibraryFolders"\n{\n\t"TimeNextStatsReport"\t\t"1700000000"\n\t"1"\t\t"D:\\\\SteamLibrary"\n}'
    assert paths.library_paths(old) == [os.path.normpath("D:\\SteamLibrary")], paths.library_paths(old)

    shutil.rmtree(TMP, ignore_errors=True)
    steam, lib_b = os.path.join(TMP, "Steam"), os.path.join(TMP, "LibB")
    os.makedirs(os.path.join(steam, "steamapps", "common"))
    with open(os.path.join(steam, "steamapps", "libraryfolders.vdf"), "w") as f:
        f.write('"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n\t"1"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}'
                % (steam.replace("\\", "\\\\"), lib_b.replace("\\", "\\\\")))
    left = mcc_copy(os.path.join(steam, "steamapps", "common", paths.MCC_NAME))       # a copy Steam does not list
    real = mcc_copy(os.path.join(lib_b, "steamapps", "common", paths.MCC_NAME), "halo1")
    with open(os.path.join(lib_b, "steamapps", "appmanifest_976730.acf"), "w") as f:
        f.write(f'"AppState"\n{{\n\t"appid"\t\t"976730"\n\t"InstallDir"\t\t"{paths.MCC_NAME}"\n}}')
    mine = mcc_copy(os.path.join(TMP, "MCC builds", "before update"), "haloreach")     # the player's own copy
    empty = os.path.join(TMP, "not mcc")
    os.makedirs(empty)

    paths._steam_roots = lambda: [steam]
    paths.steam_commons.cache_clear()
    paths.CHOICE = os.path.join(TMP, "user", "mcc_folder.txt")
    os.environ.pop("HB_MCC", None)
    os.environ.pop("HB_STEAM_COMMON", None)

    norm = os.path.normcase
    assert [norm(p) for p in paths.installs()] == [norm(real), norm(left)], paths.installs()
    assert norm(paths.mcc()) == norm(real) and paths.is_steam_copy(real) and not paths.is_steam_copy(left)
    assert paths.chosen() is None

    # the player picks a folder: MCC's own, a folder inside it, or the library above it
    ok, said = paths.choose(os.path.join(mine, "MCC", "Binaries", "Win64"))
    assert ok and norm(said) == norm(mine), said
    assert norm(paths.mcc()) == norm(mine) and not paths.is_steam_copy(mine) and paths.games() == ["reach"]
    assert norm(paths.find_root(os.path.join(lib_b, "steamapps", "common"))) == norm(real)
    assert norm(paths.find_root(lib_b)) == norm(real)
    ok, said = paths.choose(empty)
    assert not ok and "not an MCC folder" in said and norm(paths.mcc()) == norm(mine)       # (the old choice stays)
    ok, said = paths.choose(os.path.join(TMP, "nowhere"))
    assert not ok and "does not exist" in said
    no_games = mcc_copy(os.path.join(TMP, "no games"), None)
    assert "none of its games" in paths.choose(no_games)[1]
    os.environ["HB_MCC"] = left                        # the environment variable wins over the choice
    assert paths.mcc() == left
    del os.environ["HB_MCC"]

    # the launcher's endpoint: a pasted path (quotes and all), then automatic again
    import launcher
    assert launcher.choose_mcc({"path": f' "{real}" '}) == (True, real) and norm(paths.chosen()) == norm(real)
    s = launcher.status()
    assert norm(s["mcc"]) == norm(real) and s["mcc_steam"] and not s["mcc_env"] and len(s["mcc_found"]) == 2
    assert launcher.choose_mcc({"path": ""})[0] is False
    assert launcher.choose_mcc({"auto": True}) == (True, "automatic") and paths.chosen() is None
    assert not os.path.exists(paths.CHOICE) and norm(paths.mcc()) == norm(real)
    paths.choose(mine)
    shutil.rmtree(mine)                                # the chosen copy is gone: not found, not another copy
    assert paths.mcc() is None and launcher.status()["mcc"] is None
    import setup
    assert "not there any more" in setup.game_line(paths.mcc())
    paths.choose(None)

    # Play with a copy Steam does not start: its program directly, with steam_appid.txt beside it
    import launch
    mine = mcc_copy(os.path.join(TMP, "MCC builds", "before update"), "haloreach")
    started = []

    class Proc:
        def __init__(self, cmd, cwd=None):
            started.append((cmd, cwd))
    launch.subprocess.Popen, real_popen = Proc, launch.subprocess.Popen
    launch.running, real_running = (lambda name: False), launch.running
    try:
        assert launch.start_copy(mine) is None and not started            # Steam is not running: says so
        launch.running = lambda name: name == "steam.exe"
        assert launch.start_copy(mine) is not None
    finally:
        launch.subprocess.Popen, launch.running = real_popen, real_running
    exe = os.path.join(mine, paths.GAME_EXE)
    assert started == [([exe], os.path.dirname(exe))], started
    for d in (mine, os.path.dirname(exe)):
        assert open(os.path.join(d, "steam_appid.txt")).read() == "976730"
    os.environ.pop("PPG_LINUX", None)
    assert paths.wine() is False                       # (Windows: no Wine ntdll)
    os.environ["PPG_LINUX"] = "1"
    assert paths.wine() is True
    del os.environ["PPG_LINUX"]
    shutil.rmtree(TMP, ignore_errors=True)
    print("mcc folder OK")


if __name__ == "__main__":
    main()
