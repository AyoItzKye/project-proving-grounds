// filemon.dll: temporary instrumentation. Logs files MCC opens (CreateFileW), to find which
// UI screen files load when the Halo CE custom game lobby opens. Log: filemon.log next to the DLL.
#include <windows.h>
#include <stdio.h>
#include <share.h>
#include "third_party/minhook/include/MinHook.h"

typedef HANDLE(WINAPI* cf_fn)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static cf_fn o_cf;
static FILE* g_log;
static int g_n;

static HANDLE WINAPI h_cf(LPCWSTR name, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    if (g_log && name && g_n < 20000 && !wcsstr(name, L"filemon.log")) {
        SYSTEMTIME st; GetLocalTime(&st);
        fwprintf(g_log, L"%02d:%02d:%02d.%03d %s\n", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, name);
        fflush(g_log); g_n++;
    }
    return o_cf(name, a, s, sa, c, f, t);
}

static DWORD WINAPI main_thread(LPVOID self) {
    wchar_t path[MAX_PATH];
    GetModuleFileNameW((HMODULE)self, path, MAX_PATH);
    wcscpy_s(wcsrchr(path, L'\\') + 1, 64, L"filemon.log");
    g_log = _wfsopen(path, L"w", _SH_DENYNO);
    MH_Initialize();
    void* target = GetProcAddress(GetModuleHandleW(L"kernelbase.dll"), "CreateFileW");
    bool ok = MH_CreateHook(target, (void*)&h_cf, (void**)&o_cf) == MH_OK && MH_EnableHook(target) == MH_OK;
    fwprintf(g_log, L"filemon %s\n", ok ? L"on" : L"FAILED");
    fflush(g_log);
    return 0;
}

BOOL APIENTRY DllMain(HMODULE mod, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(mod);
        CloseHandle(CreateThread(nullptr, 0, main_thread, mod, 0, nullptr));
    }
    return TRUE;
}
