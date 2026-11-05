"""Offline check of the Linux / Steam Deck scripts (installer/linux) with bash, on a fake home: a Steam library on an
"SD card" listed in libraryfolders.vdf, MCC with its compatdata (config_info naming a fake Proton that only prints how
it was called) and a fake Steam Linux Runtime. Checks that install.sh finds them, copies the mod, runs the setup in the
mod's own prefix (not MCC's), writes the menu entry; that ppg-run.sh (the Steam launch option) swaps MCC's program for
the mod's Python running launch.py in the same Proton command, and leaves the anti-cheat on command alone; and that
uninstall.sh keeps the player's data and leaves the stand-in. Needs bash (Git for Windows, or Linux); skipped without.

usage: python -I test_linux_install.py
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
TMP = os.path.join(ROOT, "logs", "tmp", "test_linux_install")
LINUX = os.path.join(ROOT, "installer", "linux")


def bash():
    for p in (r"C:\Program Files\Git\bin\bash.exe", shutil.which("bash")):
        if p and os.path.exists(p) and "system32" not in p.lower():      # (not WSL's launcher)
            return p
    return None


def unix(p):
    """A Windows path as Git's bash writes it (/a/...); a Linux path as it is."""
    p = os.path.abspath(p)
    return "/" + p[0].lower() + p[2:].replace("\\", "/") if os.name == "nt" else p


def write(path, text, lf=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n" if lf else None) as f:
        f.write(text)


def run(sh, args, env, check=True):
    r = subprocess.run([sh, *args], env=env, capture_output=True, text=True, errors="replace", timeout=120)
    if check and r.returncode:
        raise SystemExit(f"{args[0]} failed ({r.returncode}):\n{r.stdout}\n{r.stderr}")
    return r


def main():
    sh = bash()
    if not sh:
        print("skipped: no bash on this PC")
        return
    shutil.rmtree(TMP, ignore_errors=True)
    home = os.path.join(TMP, "home deck")                 # (a space: every path must be quoted)
    steam = os.path.join(home, ".local", "share", "Steam")
    card = os.path.join(TMP, "run", "media", "mmcblk0p1")
    write(os.path.join(steam, "steamapps", "libraryfolders.vdf"),
          f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"path"\t\t"{unix(steam)}"\n\t}}\n'
          f'\t"1"\n\t{{\n\t\t"path"\t\t"{unix(card)}"\n\t}}\n}}\n')
    mcc = os.path.join(card, "steamapps", "common", "Halo The Master Chief Collection")
    write(os.path.join(mcc, "MCC", "Binaries", "Win64", "MCC-Win64-Shipping.exe"), "")
    write(os.path.join(card, "steamapps", "appmanifest_976730.acf"),
          '"AppState"\n{\n\t"appid"\t\t"976730"\n\t"installdir"\t\t"Halo The Master Chief Collection"\n}\n')
    proton = os.path.join(steam, "steamapps", "common", "Proton 9.0 (Beta)")
    write(os.path.join(proton, "proton"), '#!/bin/bash\nprintf "PROTON "; printf "%s|" "$@"; echo\n'
          'echo "DATA=$STEAM_COMPAT_DATA_PATH"; echo "CLIENT=$STEAM_COMPAT_CLIENT_INSTALL_PATH"\n'
          'echo "COMMON=$HB_STEAM_COMMON"; echo "MCCENV=$HB_MCC"; echo "LINUX=$PPG_LINUX"\n')
    write(os.path.join(proton, "toolmanifest.vdf"), '"manifest"\n{\n\t"require_tool_appid" "1628350"\n}\n')
    compat = os.path.join(card, "steamapps", "compatdata", "976730")
    write(os.path.join(compat, "config_info"), f"3\n{unix(proton)}/files/share/fonts/\n{unix(proton)}/files/lib/\n")
    slr = os.path.join(steam, "steamapps", "common", "SteamLinuxRuntime_sniper", "_v2-entry-point")
    write(slr, '#!/bin/bash\necho "SLR $1"; shift; [ "$1" = "--" ] && shift; exec "$@"\n')
    for p in (os.path.join(proton, "proton"), slr):
        os.chmod(p, 0o755)

    payload = os.path.join(TMP, "ProjectProvingGrounds-Linux-0.0.0", "payload")
    for rel in ("tools/launcher.py", "tools/launch.py", "tools/setup.py", "python/python.exe", "brain/paths.py"):
        write(os.path.join(payload, *rel.split("/")), "")
    for f in os.listdir(LINUX):                        # (the scripts with LF endings, as the release tar has them)
        data = open(os.path.join(LINUX, f), "rb").read()
        os.makedirs(os.path.join(payload, "installer", "linux"), exist_ok=True)
        open(os.path.join(payload, "installer", "linux", f), "wb").write(
            data.replace(b"\r\n", b"\n") if f.endswith(".sh") else data)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("XDG_", "PPG_", "HB_"))}
    env["HOME"] = unix(home)

    inst = os.path.join(payload, "installer", "linux", "install.sh")
    out = run(sh, [unix(inst), "--payload", unix(payload)], env).stdout
    app = os.path.join(home, ".local", "share", "project-proving-grounds", "app")
    assert f"MCC:    {unix(mcc)}" in out and f"Proton: {unix(proton)} (in SteamLinuxRuntime_sniper)" in out, out
    assert os.path.exists(os.path.join(app, "tools", "launcher.py")), out
    assert "SLR --verb=waitforexitandrun" in out and f"PROTON waitforexitandrun|{unix(app)}/python/python.exe|-u|-I|" \
           "Z:" + unix(app).replace("/", "\\") + "\\tools\\setup.py|" in out, out
    assert f"DATA={unix(home)}/.local/share/project-proving-grounds/prefix" in out, out      # the mod's prefix
    assert "COMMON=Z:" + unix(card).replace("/", "\\") + "\\steamapps\\common" in out and "LINUX=1" in out, out
    assert f'"{unix(app)}/installer/linux/ppg-run.sh" %command%' in out, out
    entry = open(os.path.join(home, ".local", "share", "applications", "project-proving-grounds.desktop")).read()
    assert f'Exec="{unix(app)}/installer/linux/ppg-launcher.sh"' in entry, entry

    # the Steam launch option: Steam's own command for the anti-cheat off choice, through the wrapper
    run_sh = os.path.join(app, "installer", "linux", "ppg-run.sh")
    exe = os.path.join(mcc, "MCC", "Binaries", "Win64", "MCC-Win64-Shipping.exe")
    run(sh, [unix(run_sh), unix(slr), "--verb=waitforexitandrun", "--", unix(os.path.join(proton, "proton")),
             "waitforexitandrun", unix(exe), "-novid"], env)
    log = open(os.path.join(app, "logs", "linux_play.txt")).read()
    win = lambda p: "Z:" + unix(p).replace("/", "\\")                 # noqa: E731
    assert f"PROTON waitforexitandrun|{unix(app)}/python/python.exe|-u|-I|{win(app)}\\tools\\launch.py|--exe|" \
           f"{win(exe)}|--|-novid|" in log, log
    assert f"MCCENV={win(mcc)}" in log and "LINUX=1" in log, log
    # the anti-cheat on choice runs exactly as Steam asked
    r = run(sh, [unix(run_sh), unix(os.path.join(proton, "proton")), "waitforexitandrun",
                 unix(os.path.join(mcc, "mcclauncher.exe"))], env)
    assert f"PROTON waitforexitandrun|{unix(mcc)}/mcclauncher.exe|" in r.stdout, r.stdout

    # uninstall, keeping the player's data
    os.makedirs(os.path.join(app, "maps", "bloodgulch"), exist_ok=True)
    run(sh, [unix(os.path.join(app, "installer", "linux", "uninstall.sh")), "--yes"], env)
    assert os.path.isdir(os.path.join(app, "maps", "bloodgulch")) and not os.path.exists(os.path.join(app, "tools"))
    assert open(os.path.join(app, "installer", "linux", "ppg-run.sh")).read() == '#!/bin/bash\nexec "$@"\n'
    assert not os.path.exists(os.path.join(home, ".local", "share", "applications", "project-proving-grounds.desktop"))
    shutil.rmtree(TMP, ignore_errors=True)
    print("linux install OK")


if __name__ == "__main__":
    main()
