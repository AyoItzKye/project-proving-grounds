"""Find code that references a string in a game DLL and disassemble around it.

usage: python -I xref.py <dll> <string> [--wide] [--before N] [--after N]
Finds every RIP-relative reference (lea/mov/cmp ..., [rip+disp32]) to the
string, then prints the instructions around each reference.
"""
import sys, argparse
import numpy as np
import pefile, capstone


def load(path):
    pe = pefile.PE(path, fast_load=True)
    data = open(path, 'rb').read()
    return pe, data


def off_to_rva(pe, off):
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return off - s.PointerToRawData + s.VirtualAddress
    return None


def text_section(pe):
    return next(s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text')


def rip_refs(pe, data, target_rva):
    """Code offsets whose disp32 resolves (as rip+disp, rip = disp end) to target."""
    t = text_section(pe)
    raw = np.frombuffer(data, dtype=np.uint8, count=t.SizeOfRawData, offset=t.PointerToRawData)
    n = len(raw) - 4
    disp = (raw[:n].astype(np.int64) | (raw[1:n + 1].astype(np.int64) << 8) |
            (raw[2:n + 2].astype(np.int64) << 16) | (raw[3:n + 3].astype(np.int64) << 24))
    disp = np.where(disp >= 2 ** 31, disp - 2 ** 32, disp)
    rva_after = t.VirtualAddress + np.arange(n, dtype=np.int64) + 4
    hits = np.nonzero(rva_after + disp == target_rva)[0]
    return [(int(h), t) for h in hits]


def disasm(pe, data, rva, before, after):
    t = text_section(pe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    base = pe.OPTIONAL_HEADER.ImageBase
    start = max(t.VirtualAddress, rva - before)
    # start on an instruction boundary: just after the nearest int3 padding
    off = start - t.VirtualAddress + t.PointerToRawData
    lo = max(t.PointerToRawData, off - 0x4000)
    pad = data.rfind(b'\xcc\xcc', lo, rva - t.VirtualAddress + t.PointerToRawData)
    if pad != -1:
        while data[pad] == 0xcc:
            pad += 1
        if pad < off:
            off = pad
            start = off - t.PointerToRawData + t.VirtualAddress
            before = rva - start
    code = data[off:off + before + after]
    out = []
    for ins in md.disasm(code, base + start):
        out.append(ins)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dll'); ap.add_argument('string')
    ap.add_argument('--wide', action='store_true')
    ap.add_argument('--before', type=int, default=0x60)
    ap.add_argument('--after', type=int, default=0x80)
    a = ap.parse_args()
    pe, data = load(a.dll)
    needle = a.string.encode('utf-16le' if a.wide else 'latin-1') + (b'\0\0' if a.wide else b'\0')
    base = pe.OPTIONAL_HEADER.ImageBase
    pos = data.find(needle)
    while pos != -1:
        rva = off_to_rva(pe, pos)
        print(f'string at file 0x{pos:x} rva 0x{rva:x} va 0x{base + rva:x}')
        for h, t in rip_refs(pe, data, rva):
            ref_rva = t.VirtualAddress + h
            print(f'  ref at va 0x{base + ref_rva:x}')
            for ins in disasm(pe, data, ref_rva, a.before, a.after):
                mark = '>>' if ins.address <= base + ref_rva < ins.address + ins.size else '  '
                print(f'    {mark} {ins.address:x}: {ins.mnemonic} {ins.op_str}')
        pos = data.find(needle, pos + 1)


if __name__ == '__main__':
    main()
