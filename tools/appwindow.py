"""Opens one of the project's pages (the launcher, the Observer, the LiDAR view, the nav painter) as its own app
window: Microsoft Edge's app mode (no tabs, no address bar, its own title and taskbar button), which every Windows 10
and 11 PC has. The window keeps its own Edge profile under %LOCALAPPDATA%\\ProjectProvingGrounds\\window, so it never
touches the user's own browser profile. Without Edge the page opens in the default browser.

usage: python -I appwindow.py <url> [width height]
"""
import os
import subprocess
import sys
import webbrowser


def edge():
    """msedge.exe's path (its App Paths registry entry, else the usual install folders), or None."""
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as k:
                    p = winreg.QueryValueEx(k, None)[0]
                    if p and os.path.exists(p):
                        return p
            except OSError:
                continue
    except ImportError:
        pass
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        p = os.path.join(base or "", "Microsoft", "Edge", "Application", "msedge.exe")
        if base and os.path.exists(p):
            return p
    return None


def command(url, size=(1400, 900), exe=None, profile=None):
    """The command line that opens url as an app window, or None without Edge."""
    exe = exe or edge()
    if not exe:
        return None
    profile = profile or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ProjectProvingGrounds",
                                      "window")
    return [exe, f"--app={url}", f"--window-size={size[0]},{size[1]}", f"--user-data-dir={profile}",
            "--no-first-run", "--no-default-browser-check", "--disable-features=Translate"]


def open_window(url, size=(1400, 900)):
    """Opens url as an app window (the default browser without Edge). Returns at once."""
    cmd = command(url, size)
    if cmd:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    open_window(a[0], (int(a[1]), int(a[2])) if len(a) >= 3 else (1400, 900))
