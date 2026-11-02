"""Find the method tables (vtables) that hold a given function address in a DLL file and print
every entry, so a class found by one tiny method (a get_name returning a string) leads to the rest.

usage: python -I vtable_of.py <dll path> <hex address | =string> [entries before] [entries after]
       (=name: the address of that NUL-ended string, e.g. a HaloScript function's name, so its
       definition entry and the code pointers beside it show)
"""
import struct
import sys


def sections(b):
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec, opt = struct.unpack_from("<H", b, pe + 6)[0], struct.unpack_from("<H", b, pe + 20)[0]
    base = struct.unpack_from("<Q", b, pe + 24 + 24)[0]
    out = []
    for i in range(nsec):
        o = pe + 24 + opt + i * 40
        vs, va, rs, ra = struct.unpack_from("<IIII", b, o + 8)
        out.append((b[o:o + 8].rstrip(b"\0").decode(), base + va, max(vs, rs), ra))
    return base, out


def main():
    path = sys.argv[1]
    before = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    after = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    b = open(path, "rb").read()
    base, secs = sections(b)
    if sys.argv[2].startswith("="):
        o = b.find(b"\0" + sys.argv[2][1:].encode() + b"\0") + 1
        addr = next(va + o - ra for n, va, size, ra in secs if ra <= o < ra + size)
        print(f"string {sys.argv[2][1:]!r} at {addr:#x}")
    else:
        addr = int(sys.argv[2], 16)

    def where(v):
        return next((n for n, va, size, _ in secs if va <= v < va + size), None)

    def file_off(v):
        return next((ra + v - va for n, va, size, ra in secs if va <= v < va + size), None)

    def to_va(o):
        return next((va + o - ra for n, va, size, ra in secs if ra <= o < ra + size), None)

    want = struct.pack("<Q", addr)
    i = b.find(want)
    while i >= 0:
        va = to_va(i)
        print(f"table entry at {va:#x} ({where(va)})")
        for k in range(-before, after):
            v = struct.unpack_from("<Q", b, i + 8 * k)[0]
            s = where(v)
            mark = "  <-" if k == 0 else ""
            print(f"  [{k:+3}] {va + 8 * k:#x}: {v:#x} {s or ''}{mark}")
        i = b.find(want, i + 1)
    if file_off(addr) is None:
        print("address not in the file")


if __name__ == "__main__":
    main()
