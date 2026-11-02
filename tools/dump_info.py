"""Crash summary from a Windows minidump (MCC's UE4Minidump.dmp): exception code and address as
module+offset, plus module+offset guesses for return addresses found on the crashing thread's stack.

usage: python -I dump_info.py <file.dmp> [stack words=400]
"""
import struct
import sys


def main():
    data = open(sys.argv[1], "rb").read()
    words = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    n, rva = struct.unpack_from("<II", data, 8)
    streams = {}
    for i in range(n):
        typ, size, at = struct.unpack_from("<III", data, rva + i * 12)
        streams[typ] = (at, size)
    mods = []
    at, _ = streams[4]                                   # ModuleListStream
    for i in range(struct.unpack_from("<I", data, at)[0]):
        base, size, _, _, name_rva = struct.unpack_from("<QIIII", data, at + 4 + i * 108)
        ln = struct.unpack_from("<I", data, name_rva)[0]
        mods.append((base, size, data[name_rva + 4:name_rva + 4 + ln].decode("utf-16-le").rsplit("\\", 1)[-1]))

    def where(a):
        for base, size, name in mods:
            if base <= a < base + size:
                return "%s+0x%X" % (name, a - base)
        return None

    at, _ = streams[6]                                   # ExceptionStream
    tid = struct.unpack_from("<I", data, at)[0]
    code, _, _, addr = struct.unpack_from("<IIQQ", data, at + 8)
    nparams = struct.unpack_from("<I", data, at + 8 + 24)[0]
    params = struct.unpack_from("<%dQ" % nparams, data, at + 8 + 32) if nparams else ()
    ctx_size, ctx_rva = struct.unpack_from("<II", data, at + 8 + 152)
    print("exception 0x%08X at %s (0x%X) params %s" % (code, where(addr), addr, [where(p) or hex(p) for p in params]))
    near = sorted(mods, key=lambda m: abs(m[0] - params[-1]))[:3] if params else []
    print("modules nearest the address:", ["%s 0x%X-0x%X" % (n, b, b + s) for b, s, n in near])
    rip, rsp = struct.unpack_from("<Q", data, ctx_rva + 0xF8)[0], struct.unpack_from("<Q", data, ctx_rva + 0x98)[0]
    print("thread %d rip %s rsp 0x%X" % (tid, where(rip), rsp))
    regs = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi"]
    print(" ".join("%s=%X" % (r, struct.unpack_from("<Q", data, ctx_rva + 0x78 + 8 * i)[0]) for i, r in enumerate(regs)))
    # the stack memory of the crashing thread from MemoryListStream
    at, _ = streams[5]
    for i in range(struct.unpack_from("<I", data, at)[0]):
        start, size, mrva = struct.unpack_from("<QII", data, at + 4 + i * 16)
        if start <= rsp < start + size:
            off = mrva + (rsp - start)
            count = min(words, (start + size - rsp) // 8)
            for k, w in enumerate(struct.unpack_from("<%dQ" % count, data, off)):
                w2 = where(w)
                if w2 and not w2.startswith("ntdll") and "kernel" not in w2.lower():
                    print("  [rsp+0x%X] %s" % (k * 8, w2))
            break


if __name__ == "__main__":
    main()
