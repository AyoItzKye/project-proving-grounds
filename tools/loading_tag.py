"""A small "Loading mod ..." tag on screen from the moment Play starts MCC until botcore's overlay is up (tools/launch.py).

MCC reaches its menus before the mod is loaded (the mod is loaded about 15 s after MCC starts), and a player who is quick
opens Multiplayer first: the BOTS panel does not appear in a lobby entered before the mod. The tag says to wait. It is a
topmost, click-through window with no border (it takes no focus and no clicks) in the top middle of MCC's window, made
with plain Win32 calls (also works in Wine / Proton on the Steam Deck). It closes when botcore's overlay has drawn its
first frame (it creates the event LOCAL\\PPG_overlay_ready then: native/overlay.cpp), or after `timeout` seconds.

    tag = LoadingTag(); tag.start()  ...  tag.wait_ready(timeout=120)   (closes the window)
"""
import ctypes
import ctypes.wintypes as W
import threading
import time

READY_EVENT = "Local\\PPG_overlay_ready"
TEXT = "Project Proving Grounds is loading. Open Multiplayer once this message closes."
WS_POPUP, WS_EX_TOPMOST, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE, WS_EX_LAYERED, WS_EX_TRANSPARENT = (
    0x80000000, 0x8, 0x80, 0x08000000, 0x80000, 0x20)
WM_PAINT, WM_DESTROY, WM_CLOSE = 0x000F, 0x0002, 0x0010
LRESULT = ctypes.c_ssize_t


class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", W.UINT), ("lpfnWndProc", ctypes.c_void_p), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", W.HINSTANCE), ("hIcon", W.HICON), ("hCursor", W.HANDLE),
                ("hbrBackground", W.HBRUSH), ("lpszMenuName", W.LPCWSTR), ("lpszClassName", W.LPCWSTR)]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [("hdc", W.HDC), ("fErase", W.BOOL), ("rcPaint", W.RECT), ("fRestore", W.BOOL), ("fIncUpdate", W.BOOL),
                ("rgbReserved", ctypes.c_byte * 32)]


def _api():
    u, g, k = ctypes.windll.user32, ctypes.windll.gdi32, ctypes.windll.kernel32
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
    u.DefWindowProcW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
    u.DefWindowProcW.restype = LRESULT
    u.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID]
    u.CreateWindowExW.restype = W.HWND
    u.BeginPaint.argtypes = [W.HWND, ctypes.POINTER(PAINTSTRUCT)]
    u.BeginPaint.restype = W.HDC
    u.EndPaint.argtypes = [W.HWND, ctypes.POINTER(PAINTSTRUCT)]
    u.FillRect.argtypes = [W.HDC, ctypes.POINTER(W.RECT), W.HBRUSH]
    u.DrawTextW.argtypes = [W.HDC, W.LPCWSTR, ctypes.c_int, ctypes.POINTER(W.RECT), W.UINT]
    u.GetClientRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
    g.CreateSolidBrush.restype = W.HBRUSH
    g.DeleteObject.argtypes = [W.HANDLE]
    g.SetBkMode.argtypes = [W.HDC, ctypes.c_int]
    g.SetTextColor.argtypes = [W.HDC, W.DWORD]
    u.SetWindowPos.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, W.UINT]
    g.CreateFontW.restype = W.HANDLE
    g.SelectObject.argtypes = [W.HDC, W.HANDLE]
    k.OpenEventW.restype = W.HANDLE
    return u, g, k, WNDPROC


def mcc_rect():
    """(left, top, right, bottom) of MCC's window, else the primary screen."""
    u = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def each(h, _):
        if u.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(256)
            u.GetWindowTextW(h, b, 256)
            if b.value.startswith("Halo: The Master Chief Collection"):
                r = W.RECT()
                u.GetWindowRect(h, ctypes.byref(r))
                if r.right - r.left > 400:
                    found.append((r.left, r.top, r.right, r.bottom))
        return True
    u.EnumWindows(each, 0)
    return found[0] if found else (0, 0, u.GetSystemMetrics(0), u.GetSystemMetrics(1))


class LoadingTag:
    def __init__(self, text=TEXT):
        self.text = text
        self.hwnd = None
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def ready(self):
        """True once botcore's overlay has drawn a frame."""
        h = ctypes.windll.kernel32.OpenEventW(0x100000, False, READY_EVENT)       # SYNCHRONIZE
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
        return bool(h)

    def wait_ready(self, timeout=120):
        """Waits for the overlay (or timeout seconds), then closes the tag. True when the overlay came up."""
        end = time.time() + timeout
        while time.time() < end and not self.ready():
            time.sleep(0.5)
        ok = self.ready()
        self.close()
        return ok

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join(3)

    def _run(self):
        try:
            u, g, k, WNDPROC = _api()
            try:
                u.SetProcessDPIAware()
            except Exception:
                pass
            text = self.text

            def proc(h, msg, wp, lp):
                if msg == WM_PAINT:
                    ps = PAINTSTRUCT()
                    dc = u.BeginPaint(h, ctypes.byref(ps))
                    r = W.RECT()
                    u.GetClientRect(h, ctypes.byref(r))
                    brush = g.CreateSolidBrush(0x00211A12)                       # (BGR) a dark blue-grey
                    u.FillRect(dc, ctypes.byref(r), brush)
                    g.DeleteObject(brush)
                    font = g.CreateFontW(-18, 0, 0, 0, 600, 0, 0, 0, 1, 0, 0, 4, 0, "Segoe UI")
                    old = g.SelectObject(dc, font)
                    g.SetBkMode(dc, 1)
                    g.SetTextColor(dc, 0x00FFFFFF)
                    u.DrawTextW(dc, text, -1, ctypes.byref(r), 0x25)           # DT_CENTER | DT_VCENTER | DT_SINGLELINE
                    g.SelectObject(dc, old)
                    g.DeleteObject(font)
                    u.EndPaint(h, ctypes.byref(ps))
                    return 0
                if msg == WM_DESTROY:
                    u.PostQuitMessage(0)
                    return 0
                return u.DefWindowProcW(h, msg, wp, lp)

            self._proc = WNDPROC(proc)                                           # (kept alive)
            wc = WNDCLASS()
            wc.lpfnWndProc = ctypes.cast(self._proc, ctypes.c_void_p).value
            wc.hInstance = k.GetModuleHandleW(None)
            wc.lpszClassName = "PPGLoadingTag"
            u.RegisterClassW(ctypes.byref(wc))
            left, top, right, bottom = mcc_rect()
            w, h = 760, 44
            x = left + max(0, (right - left - w) // 2)
            y = top + 14
            self.hwnd = u.CreateWindowExW(WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED |
                                          WS_EX_TRANSPARENT, wc.lpszClassName, "Project Proving Grounds", WS_POPUP,
                                          x, y, w, h, None, None, wc.hInstance, None)
            if not self.hwnd:
                return
            u.SetLayeredWindowAttributes(self.hwnd, 0, 235, 2)                    # LWA_ALPHA
            u.ShowWindow(self.hwnd, 4)                                           # SW_SHOWNOACTIVATE
            msg = W.MSG()
            while not self._stop.is_set():
                while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    u.TranslateMessage(ctypes.byref(msg))
                    u.DispatchMessageW(ctypes.byref(msg))
                # MCC's window may come and go while it starts: follow it, stay on top
                nl, nt, nr, nb = mcc_rect()
                u.SetWindowPos(self.hwnd, -1, nl + max(0, (nr - nl - w) // 2), nt + 14, w, h, 0x10 | 0x40)
                time.sleep(0.5)
            u.DestroyWindow(self.hwnd)
        except Exception:
            pass                                                                # (a missing tag must never stop the launch)


if __name__ == "__main__":                                                      # python -I loading_tag.py [seconds]
    import sys
    t = LoadingTag()
    t.start()
    print("tag up; ready:", t.wait_ready(float(sys.argv[1]) if len(sys.argv) > 1 else 5))
