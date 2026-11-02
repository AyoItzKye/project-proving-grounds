"""Find the code that uses a string in a PE file (read-only, the file on disk): the string's RVA (ASCII or UTF-16), then
every RIP-relative LEA / MOV in executable sections that points at it, with the start of the function around each
(scanning back to the previous int3 / padding run). For decompiling just those functions (ghidra/decompile_dll.bat).

usage: python -I pe_xref.py <pe file> <string> [<string> ...]
       python -I pe_xref.py <pe file> --calls <hex address> [...]   (direct E8 calls to those functions)
"""
import re
import struct
import sys


def sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<Q", data, pe + 24 + 24)[0]
    out = []
    for k in range(n):
        s = pe + 24 + opt + 40 * k
        name = data[s:s + 8].rstrip(b"\0").decode()
        vsize, va, rsize, raw = struct.unpack_from("<IIII", data, s + 8)
        chars = struct.unpack_from("<I", data, s + 36)[0]
        out.append((name, va, vsize, raw, rsize, chars))
    return base, out


def rva_of(off, secs):
    for name, va, vsize, raw, rsize, chars in secs:
        if raw <= off < raw + rsize:
            return va + off - raw
    return None


def func_start(data, off):
    """Back from a file offset to just after the previous run of CC / 90 padding (MSVC's function gaps; a guess:
    pdata_func gives exact bounds)."""
    k = off
    while k > 2 and not (data[k - 1] in (0xCC, 0x90) and data[k - 2] in (0xCC, 0x90)):
        k -= 1
    return k


def pdata_func(data, secs, rva):
    """(begin, end) RVAs of the function containing rva, from .pdata's RUNTIME_FUNCTION table (x64), or None."""
    for name, va, vsize, raw, rsize, chars in secs:
        if name == ".pdata":
            best = None
            for k in range(0, rsize - 11, 12):
                b, e, u = struct.unpack_from("<III", data, raw + k)
                if b <= rva < e and (best is None or b > best[0]):
                    best = (b, e)
            return best
    return None


def main():
    path, words = sys.argv[1], sys.argv[2:]
    data = open(path, "rb").read()
    base, secs = sections(data)
    print("image base", hex(base), "sections", [(s[0], hex(s[1])) for s in secs])
    if words and words[0] == "--calls":
        want = {int(a, 16) - base for a in words[1:]}
        for name, va, vsize, raw, rsize, chars in secs:
            if chars & 0x20000000:
                code = data[raw:raw + rsize]
                for m in re.finditer(rb"\xe8", code):
                    i = m.start()
                    if i + 5 <= len(code) and va + i + 5 + struct.unpack_from("<i", code, i + 1)[0] in want:
                        fs = func_start(data, raw + i)
                        print(f"  call at {base + va + i:#x}, function ~{base + rva_of(fs, secs):#x}")
        return
    targets = {}
    for w in words:
        for enc, pat in (("ascii", w.encode() + b"\0"), ("utf16", w.encode("utf-16-le") + b"\0\0")):
            for m in re.finditer(re.escape(pat), data):
                r = rva_of(m.start(), secs)
                if r is not None:
                    targets[r] = f"{w} ({enc})"
    print("strings:", {hex(r): t for r, t in targets.items()})
    for name, va, vsize, raw, rsize, chars in secs:
        if not chars & 0x20000000:          # executable sections only
            continue
        code = data[raw:raw + rsize]
        for m in re.finditer(rb"[\x48\x4c][\x8d\x8b][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", code):
            i = m.start()
            disp = struct.unpack_from("<i", code, i + 3)[0]
            target = va + i + 7 + disp
            if target in targets:
                fs = func_start(data, raw + i)
                print(f"  {targets[target]}: code at {base + va + i:#x} (rva {va + i:#x}), function ~{base + rva_of(fs, secs):#x}")


if __name__ == "__main__":
    main()
