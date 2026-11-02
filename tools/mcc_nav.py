"""Look at MCC and press menu keys, one step at a time, so menus can be navigated by sight.

usage: python -I mcc_nav.py shot                 save the MCC screen to logs/nav_now.jpg
       python -I mcc_nav.py key down down enter  focus MCC, press keys (0.4 s apart), then shot
       python -I mcc_nav.py move 2 put MCC's window on monitor 2 (test runs)
Keys: up down left right enter esc space tab backspace.
Refuses to send keys while Easy Anti-Cheat is running.
Screenshots are of MCC's window wherever it is (main monitor or not), scaled to fit 1600x900.
"""
import ctypes as C
import ctypes.wintypes as W
import os
import subprocess
import sys
import time

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from input_replay import key as send_key  # noqa: E402

user32 = C.WinDLL("user32", use_last_error=True)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "nav_now.jpg")
# scan codes (set 1); arrows are extended keys
KEYS = {"up": (0x48, True), "down": (0x50, True), "left": (0x4B, True), "right": (0x4D, True),
        "enter": (0x1C, False), "esc": (0x01, False), "space": (0x39, False), "tab": (0x0F, False),
        "backspace": (0x0E, False), "b": (0x30, False), "w": (0x11, False), "a": (0x1E, False),
        "s": (0x1F, False), "d": (0x20, False), "e": (0x12, False), "ctrl": (0x1D, False), "c": (0x2E, False),
        # for tools/decode_buttons.py (scan codes, set 1)
        "q": (0x10, False), "r": (0x13, False), "f": (0x21, False), "g": (0x22, False), "v": (0x2F, False),
        "x": (0x2D, False), "z": (0x2C, False), "t": (0x14, False), "shift": (0x2A, False), "alt": (0x38, False),
        "1": (0x02, False), "2": (0x03, False), "3": (0x04, False), "4": (0x05, False)}


def mcc_window():
    found = []

    @C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def cb(h, _):
        buf = C.create_unicode_buffer(256)
        user32.GetWindowTextW(h, buf, 256)
        if buf.value.startswith("Halo: The Master Chief Collection") and user32.IsWindowVisible(h):
            found.append(h)
        return True
    user32.EnumWindows(cb, 0)
    return found[0] if found else None


def focus(h):
    user32.keybd_event(0x12, 0, 0, 0)          # a tap of Alt lets SetForegroundWindow work
    user32.keybd_event(0x12, 0, 2, 0)
    user32.ShowWindow(h, 9)
    user32.SetForegroundWindow(h)
    time.sleep(0.4)
    return user32.GetForegroundWindow() == h


def mcc_rect():
    """MCC's window on the virtual desktop (left, top, right, bottom), or the main monitor if it has none."""
    h = mcc_window()
    r = W.RECT()
    if h and user32.GetWindowRect(h, C.byref(r)) and r.right > r.left:
        return r.left, r.top, r.right, r.bottom
    return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def grab():
    """MCC's own window content (PrintWindow, full render: a window on top of it is not in the picture; a another
    window over MCC on its monitor hid the menus from goto_lobby), else the screen where it is."""
    h = mcc_window()
    for _ in range(6 if h else 0):                    # (now and then a frame comes back black: try again)
        try:
            from PIL import Image
            r = W.RECT()
            user32.GetClientRect(h, C.byref(r))
            w, ht = r.right - r.left, r.bottom - r.top
            gdi = C.WinDLL("gdi32")
            gdi.CreateCompatibleBitmap.restype = W.HBITMAP
            hdc = user32.GetDC(h)
            mem = gdi.CreateCompatibleDC(hdc)
            bmp = gdi.CreateCompatibleBitmap(hdc, w, ht)
            gdi.SelectObject(mem, bmp)
            ok = user32.PrintWindow(h, mem, 3)       # PW_CLIENTONLY | PW_RENDERFULLCONTENT
            buf = C.create_string_buffer(w * ht * 4)
            hdr = (C.c_uint32 * 10)(40, w, -ht & 0xFFFFFFFF, 1 | (32 << 16), 0, 0, 0, 0, 0, 0)
            gdi.GetDIBits(mem, bmp, 0, ht, buf, C.byref(hdr), 0)
            gdi.DeleteObject(bmp)
            gdi.DeleteDC(mem)
            user32.ReleaseDC(h, hdc)
            img = Image.frombuffer("RGBA", (w, ht), buf, "raw", "BGRA", 0, 1).convert("RGB")
            if ok and img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                return img
        except Exception:
            break
        time.sleep(0.15)
    return ImageGrab.grab(bbox=mcc_rect(), all_screens=True)


def monitors():
    """[(left, top, right, bottom)] of every monitor, the main one first."""
    out = []

    @C.WINFUNCTYPE(W.BOOL, W.HMONITOR, W.HDC, C.POINTER(W.RECT), W.LPARAM)
    def cb(m, _dc, r, _):
        out.append((r.contents.left, r.contents.top, r.contents.right, r.contents.bottom))
        return True
    user32.EnumDisplayMonitors(None, None, cb, 0)
    return sorted(out, key=lambda r: (r[0] != 0 or r[1] != 0, r[0]))


def move(n):
    """MCC's window onto monitor n (1 = main), covering it; MCC is borderless full screen."""
    h, mons = mcc_window(), monitors()
    if not h or not 1 <= n <= len(mons):
        sys.exit(f"MCC window {'not found' if not h else 'found'}; monitors: {mons}")
    l, t, r, b = mons[n - 1]
    user32.SetWindowPos(h, None, l, t, r - l, b - t, 0x0004 | 0x0010)    # SWP_NOZORDER | SWP_NOACTIVATE
    time.sleep(1.0)
    print("MCC window", mcc_rect(), "monitor", n, mons[n - 1])


def shot():
    img = grab()
    img.thumbnail((1600, 900))
    img.save(OUT, quality=80)
    print(OUT)


def main():
    if not sys.argv[1:]:
        sys.exit(__doc__)
    if sys.argv[1] == "move":
        move(int(sys.argv[2]))
        return
    if sys.argv[1] == "turn":                      # turn the host player's view: relative mouse counts (look tests)
        from input_replay import INPUT, INPUT_MOUSE, MI, U, send
        h = mcc_window()
        if not h or not focus(h):
            sys.exit("MCC window not found or not focused")
        dx = int(sys.argv[2])
        for _ in range(20):
            send(INPUT(INPUT_MOUSE, U(mi=MI(dx // 20, 0, 0, 0x0001, 0, 0))))   # MOUSEEVENTF_MOVE
            time.sleep(0.02)
        time.sleep(0.5)
        shot()
        return
    if sys.argv[1] == "hold":                      # hold one key, screenshot while held (scoreboard)
        h = mcc_window()
        if not h or not focus(h):
            sys.exit("MCC window not found or not focused")
        scan, ext = KEYS[sys.argv[2].lower()]
        send_key({"scan": scan, "extended": ext, "down": True})
        time.sleep(1.2)
        shot()
        send_key({"scan": scan, "extended": ext, "down": False})
        return
    if sys.argv[1] == "key":
        if "easyanticheat" in subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower():
            sys.exit("Easy Anti-Cheat is running: not sending keys.")
        h = mcc_window()
        if not h:
            sys.exit("MCC window not found")
        if not focus(h):
            print("warning: MCC did not take focus")
        for name in sys.argv[2:]:
            scan, ext = KEYS[name.lower()]
            send_key({"scan": scan, "extended": ext, "down": True})
            time.sleep(0.08)
            send_key({"scan": scan, "extended": ext, "down": False})
            time.sleep(0.4)
        time.sleep(0.8)
    shot()


if __name__ == "__main__":
    main()
