"""Where things are installed on this PC: Steam's libraries, The Master Chief Collection, Halo's official mod kits, the
Visual Studio C++ build tools and the map tools. Nothing is assumed about drive letters: Steam's own registry key and
its library list (steamapps/libraryfolders.vdf) are read, and an environment variable overrides each answer:

    HB_STEAM_COMMON   a steamapps/common folder to look in first
    HB_MCC            The Master Chief Collection's folder
    HB_KIT_<NAME>     a mod kit's folder, e.g. HB_KIT_H3EK
    HB_VCVARS         vcvars64.bat of a Visual Studio C++ install
    HB_MAP_TOOLS      the folder with bsp2obj.exe and model2obj.exe (the separate map tools project)

    python -I brain/paths.py      prints what it finds
"""
import functools
import glob
import os
import re

MCC_NAME = "Halo The Master Chief Collection"
# Halo's official mod kits (free on Steam), by their install folder names
KITS = ("HCEEK", "H2EK", "H2AMPEK", "H3EK", "H3ODSTEK", "HREK", "H4EK")


def _steam_root():
    """Steam's own folder: its registry key, else the default install folder."""
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key, name in ((r"Software\Valve\Steam", "SteamPath"), (r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath")):
                try:
                    with winreg.OpenKey(hive, key) as k:
                        path = winreg.QueryValueEx(k, name)[0]
                        if path and os.path.isdir(path):
                            return os.path.normpath(path)
                except OSError:
                    continue
    except ImportError:
        pass
    default = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam")
    return default if os.path.isdir(default) else None


def library_paths(vdf_text):
    """The library folders listed in libraryfolders.vdf's text ("path" entries, backslashes doubled)."""
    return [os.path.normpath(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"]+)"', vdf_text)]


@functools.lru_cache(maxsize=None)
def steam_commons():
    """Every steamapps/common folder on this PC, the override first."""
    out = []
    if os.environ.get("HB_STEAM_COMMON"):
        out.append(os.environ["HB_STEAM_COMMON"])
    root = _steam_root()
    if root:
        libs = [root]
        try:
            libs += library_paths(open(os.path.join(root, "steamapps", "libraryfolders.vdf"), encoding="utf-8",
                                       errors="replace").read())
        except OSError:
            pass
        out += [os.path.join(lib, "steamapps", "common") for lib in libs]
    seen, uniq = set(), []
    for p in out:
        key = os.path.normcase(os.path.normpath(p))
        if key not in seen and os.path.isdir(p):
            seen.add(key)
            uniq.append(os.path.normpath(p))
    return tuple(uniq)


def installed_in(common, name):
    """Whether Steam's own record of an app (steamapps/appmanifest_<id>.acf beside this common folder) puts the app
    with this install folder name here."""
    rx = re.compile(r'"installdir"\s+"%s"' % re.escape(name), re.I)
    for acf in glob.glob(os.path.join(os.path.dirname(common), "appmanifest_*.acf")):
        try:
            if rx.search(open(acf, encoding="utf-8", errors="replace").read()):
                return True
        except OSError:
            continue
    return False


def app(name, env=None):
    """An installed Steam app's folder by its install folder name (the env override first), or None. A folder of that
    name can be left behind in another library (a game moved or uninstalled): the library Steam says has it comes
    first."""
    if env and os.environ.get(env):
        return os.environ[env]
    found = [os.path.join(c, name) for c in steam_commons() if os.path.isdir(os.path.join(c, name))]
    return next((p for p in found if installed_in(os.path.dirname(p), name)), found[0] if found else None)


def mcc():
    """The Master Chief Collection's folder, or None when it is not found."""
    return app(MCC_NAME, "HB_MCC")


def kit(name):
    """A Halo mod kit's folder (KITS), or None when it is not installed."""
    return app(name, "HB_KIT_" + name)


def steam_common():
    """The steamapps/common folder MCC is in (else the first one found), or None."""
    m = mcc()
    if m:
        return os.path.dirname(m)
    commons = steam_commons()
    return commons[0] if commons else None


# MCC's games: their map folders (Steam installs each game on its own, so some may be missing), and their names
GAME_MAPS = {"ce": r"halo1\maps", "h2": r"halo2\h2_maps_win64_dx11", "h2a": r"groundhog\maps", "h3": r"halo3\maps",
             "odst": r"halo3odst\maps", "reach": r"haloreach\maps", "h4": r"halo4\maps"}
GAME_NAMES = {"ce": "Halo: CE", "h2": "Halo 2", "h2a": "Halo 2 Anniversary", "h3": "Halo 3", "odst": "Halo 3: ODST",
              "reach": "Halo: Reach", "h4": "Halo 4"}


def games(mcc_dir=None):
    """The MCC games installed (their maps are there), in GAME_MAPS order."""
    mcc_dir = mcc_dir or mcc()
    return [g for g, d in GAME_MAPS.items()
            if mcc_dir and glob.glob(os.path.join(mcc_dir, *d.split("\\"), "*.map"))]


def map_tool(name):
    """bsp2obj.exe / model2obj.exe of the separate map tools project (GPL-3.0, run as their own programs), or None:
    the HB_MAP_TOOLS folder, else tools/map_tools (where the installer puts them), else a proving-grounds-map-tools
    checkout beside this project (its bin folder, as its build.bat writes it)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for d in (os.environ.get("HB_MAP_TOOLS"), os.path.join(root, "tools", "map_tools"),
              os.path.join(os.path.dirname(root), "proving-grounds-map-tools", "bin")):
        if d and os.path.exists(os.path.join(d, name + ".exe")):
            return os.path.join(d, name + ".exe")
    return None


def need(path, what):
    """path, or a clear stop when it was not found (for the tools that cannot run without it)."""
    if not path:
        raise SystemExit(f"{what} was not found: install it through Steam, or set its environment variable "
                         f"(python -I brain/paths.py lists them)")
    return path


@functools.lru_cache(maxsize=None)
def vcvars():
    """vcvars64.bat of the newest Visual Studio with the C++ tools (vswhere), or None."""
    if os.environ.get("HB_VCVARS"):
        return os.environ["HB_VCVARS"]
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere = os.path.join(pf86, "Microsoft Visual Studio", "Installer", "vswhere.exe")
    if os.path.exists(vswhere):
        import subprocess
        try:
            out = subprocess.run([vswhere, "-latest", "-products", "*", "-requires",
                                  "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                                 capture_output=True, text=True, timeout=20).stdout.strip()
            bat = os.path.join(out, "VC", "Auxiliary", "Build", "vcvars64.bat") if out else None
            if bat and os.path.exists(bat):
                return bat
        except (OSError, subprocess.SubprocessError):
            pass
    for bat in sorted(glob.glob(os.path.join(pf86, "Microsoft Visual Studio", "*", "*", "VC", "Auxiliary", "Build",
                                             "vcvars64.bat")), reverse=True):
        return bat
    return None


if __name__ == "__main__":
    assert library_paths('"0"\n{\n\t"path"\t\t"D:\\\\Games\\\\Steam"\n}') == [os.path.normpath("D:\\Games\\Steam")]
    import tempfile                                  # a folder left behind in one library, the install in another
    with tempfile.TemporaryDirectory() as tmp:
        old, new = (os.path.join(tmp, lib, "steamapps", "common") for lib in ("old", "new"))
        for c in (old, new):
            os.makedirs(os.path.join(c, MCC_NAME))
        open(os.path.join(new, "..", "appmanifest_976730.acf"), "w").write(f'"AppState"\n{{\n\t"installdir"\t\t"{MCC_NAME}"\n}}')
        assert installed_in(new, MCC_NAME) and not installed_in(old, MCC_NAME)
        os.makedirs(os.path.join(new, MCC_NAME, "halo3", "maps"))
        open(os.path.join(new, MCC_NAME, "halo3", "maps", "construct.map"), "w").close()
        assert games(os.path.join(new, MCC_NAME)) == ["h3"] and games(os.path.join(old, MCC_NAME)) == []
    print("steam libraries:", ", ".join(steam_commons()) or "none found")
    print("MCC:", mcc() or "not found (set HB_MCC)", "| games:", ", ".join(games()) or "none")
    for k in KITS:
        print(f"{k}:", kit(k) or "not installed")
    print("vcvars64.bat:", vcvars() or "not found (set HB_VCVARS)")
    for t in ("bsp2obj", "model2obj"):
        print(f"{t}:", map_tool(t) or "not found (the installer puts it in tools/map_tools; or set HB_MAP_TOOLS)")
