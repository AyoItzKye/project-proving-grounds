"""Find a function of one DLL in a sibling build (e.g. halo3.dll -> halo3odst.dll): takes the
first N instruction bytes at the known RVA, masks rel32 / RIP-relative displacements (they move
between builds), and scans the other DLL's code for the pattern.

usage: python -I find_like.py <known.dll> <rva hex> <other.dll> [bytes=48]
"""
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_64


def sections(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n, opt = struct.unpack_from("<H", data, e + 6)[0], struct.unpack_from("<H", data, e + 20)[0]
    out = []
    for i in range(n):
        o = e + 24 + opt + i * 40
        vsz, va, rsz, raw = struct.unpack_from("<IIII", data, o + 8)
        out.append((data[o:o + 8].rstrip(b"\0").decode(), va, vsz, raw, rsz))
    return out


def rva_to_off(secs, rva):
    for _, va, vsz, raw, rsz in secs:
        if va <= rva < va + max(vsz, rsz):
            return raw + rva - va
    raise ValueError(hex(rva))


def pattern(data, secs, rva, n):
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    off = rva_to_off(secs, rva)
    code = data[off:off + n + 16]
    pat, mask = bytearray(), bytearray()
    for ins in md.disasm(code, 0x180000000 + rva):
        b = bytearray(ins.bytes)
        m = bytearray(b"\xff" * len(b))
        if ins.disp_size == 4 or (ins.imm_size == 4 and ins.mnemonic in ("call", "jmp") or ins.mnemonic.startswith("j") and len(b) >= 5):
            k = ins.disp_offset if ins.disp_size == 4 else len(b) - 4
            for j in range(k, k + 4):
                m[j] = 0
        pat += b
        mask += m
        if len(pat) >= n:
            break
    return bytes(pat), bytes(mask)


def main():
    known, rva, other = sys.argv[1], int(sys.argv[2], 16), sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 48
    a = open(known, "rb").read()
    b = open(other, "rb").read()
    pat, mask = pattern(a, sections(a), rva, n)
    import numpy as np
    bs = sections(b)
    text = next(s for s in bs if s[0] == ".text")
    _, va, vsz, raw, rsz = text
    hay = np.frombuffer(b[raw:raw + rsz], dtype=np.uint8)
    p = np.frombuffer(pat, dtype=np.uint8)
    m = np.frombuffer(mask, dtype=np.uint8).astype(bool)
    first = int(np.nonzero(m)[0][0])
    cand = np.nonzero(hay == p[first])[0] - first
    cand = cand[(cand >= 0) & (cand + len(p) <= len(hay))]
    hits = [int(c) for c in cand if np.array_equal(hay[c:c + len(p)][m], p[m])]
    print("pattern", pat.hex(), "hits", len(hits))
    for c in hits[:10]:
        print("  rva 0x%X" % (va + c))


if __name__ == "__main__":
    main()
