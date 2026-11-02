// watch.dll: temporary instrumentation. Hardware write breakpoint (DR0) on an address read from
// watch.txt next to the DLL ("<hex address> [milliseconds] [length 1/2/4/8]"), on every thread,
// for that long (default 4000 ms, 4 bytes); a vectored exception handler records each distinct
// call stack (8 frames, unwound from the faulting context) that wrote it. Result in watch.log as
// module+offset. Copy the DLL to a new name for each run: loading the same file twice is a no-op.
#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#include <stdio.h>
#include <stdint.h>

static uintptr_t g_addr;
static int g_ms = 4000, g_len = 4;
static volatile LONG g_n;
static uintptr_t g_rip[64][8];
static volatile LONG g_cnt[64];
static SRWLOCK g_lock = SRWLOCK_INIT;

static void backtrace(const CONTEXT* c0, uintptr_t* out) {
    CONTEXT c = *c0;
    for (int k = 0; k < 8; k++) {
        out[k] = (uintptr_t)c.Rip;
        DWORD64 base = 0;
        PRUNTIME_FUNCTION f = RtlLookupFunctionEntry(c.Rip, &base, nullptr);
        if (!f) { if (!c.Rsp) break; c.Rip = *(DWORD64*)c.Rsp; c.Rsp += 8; continue; }   // leaf
        void* hd = nullptr; DWORD64 fr = 0;
        RtlVirtualUnwind(UNW_FLAG_NHANDLER, base, c.Rip, f, &c, &hd, &fr, nullptr);
        if (!c.Rip) break;
    }
}

static LONG CALLBACK veh(EXCEPTION_POINTERS* e) {
    if (e->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP) return EXCEPTION_CONTINUE_SEARCH;
    if (!(e->ContextRecord->Dr6 & 1)) return EXCEPTION_CONTINUE_SEARCH;
    uintptr_t st[8] = {};
    backtrace(e->ContextRecord, st);
    AcquireSRWLockExclusive(&g_lock);
    LONG k = 0;
    for (; k < g_n; k++) if (!memcmp(g_rip[k], st, sizeof st)) break;
    if (k == g_n && g_n < 64) { memcpy(g_rip[k], st, sizeof st); g_cnt[k] = 0; g_n++; }
    if (k < 64) g_cnt[k]++;
    ReleaseSRWLockExclusive(&g_lock);
    e->ContextRecord->Dr6 = 0;
    return EXCEPTION_CONTINUE_EXECUTION;
}

static DWORD g_armed[4096];
static int g_narmed;

static bool armed(DWORD tid) {
    for (int i = 0; i < g_narmed; i++) if (g_armed[i] == tid) return true;
    return false;
}

// on: arm every thread not armed yet (call repeatedly: threads created later, e.g. a new game
// thread per match, get the breakpoint too); off: disarm all
static void set_all(bool on) {
    DWORD me = GetCurrentThreadId(), pid = GetCurrentProcessId();
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 te{ sizeof te };
    for (BOOL ok = Thread32First(snap, &te); ok; ok = Thread32Next(snap, &te)) {
        if (te.th32OwnerProcessID != pid || te.th32ThreadID == me) continue;
        if (on && armed(te.th32ThreadID)) continue;
        HANDLE t = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_SUSPEND_RESUME, FALSE, te.th32ThreadID);
        if (!t) continue;
        if (SuspendThread(t) != (DWORD)-1) {
            CONTEXT c{}; c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
            if (GetThreadContext(t, &c)) {
                DWORD64 len = g_len == 1 ? 0 : g_len == 2 ? 1 : g_len == 8 ? 2 : 3;
                if (on) { c.Dr0 = g_addr; c.Dr7 = (c.Dr7 & ~0xF0003ull) | 1 | (1ull << 16) | (len << 18); }   // L0, write
                else { c.Dr0 = 0; c.Dr7 &= ~0xF0003ull; }
                if (SetThreadContext(t, &c) && on && g_narmed < 4096) g_armed[g_narmed++] = te.th32ThreadID;
            }
            ResumeThread(t);
        }
        CloseHandle(t);
    }
    CloseHandle(snap);
}

static DWORD WINAPI main_thread(LPVOID self) {
    wchar_t path[MAX_PATH];
    GetModuleFileNameW((HMODULE)self, path, MAX_PATH);
    wchar_t* slash = wcsrchr(path, L'\\') + 1;
    wcscpy_s(slash, 64, L"watch.txt");
    FILE* f = _wfopen(path, L"r");
    if (f) { fscanf_s(f, "%llx %d %d", (unsigned long long*)&g_addr, &g_ms, &g_len); fclose(f); }
    wcscpy_s(slash, 64, L"watch.log");
    FILE* log = _wfopen(path, L"w");
    if (!g_addr || !log) return 0;
    PVOID h = AddVectoredExceptionHandler(1, veh);
    for (DWORD t0 = GetTickCount(); GetTickCount() - t0 < (DWORD)g_ms; Sleep(2)) set_all(true);
    set_all(false);
    Sleep(200);
    RemoveVectoredExceptionHandler(h);
    fprintf(log, "watched %llx\n", (unsigned long long)g_addr);
    for (LONG k = 0; k < g_n && k < 64; k++) {
        fprintf(log, "x%ld:", g_cnt[k]);
        for (int d = 0; d < 8 && g_rip[k][d]; d++) {
            HMODULE mod = nullptr; char name[MAX_PATH] = "?";
            GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               (LPCWSTR)g_rip[k][d], &mod);
            if (mod) GetModuleBaseNameA(GetCurrentProcess(), mod, name, MAX_PATH);
            fprintf(log, " %s+%llx", name, (unsigned long long)(g_rip[k][d] - (uintptr_t)mod));
        }
        fputc(10, log);
    }
    fclose(log);
    return 0;
}

BOOL APIENTRY DllMain(HMODULE mod, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(mod);
        CloseHandle(CreateThread(nullptr, 0, main_thread, mod, 0, nullptr));
    }
    return TRUE;
}
