"""Disassemble a range of a game DLL with string/rip-target annotations.

usage: python -I disasm.py <dll> <start_va_hex> <end_va_hex>
       python -I disasm.py <dll> func <va_hex>      (whole function containing va)
       python -I disasm.py <dll> callers <va_hex>   (every direct call/jmp to va)
"""
import sys, re
import numpy as np
import pefile, capstone

path = sys.argv[1]
pe = pefile.PE(path, fast_load=True)
d = open(path, 'rb').read()
base = pe.OPTIONAL_HEADER.ImageBase
t = next(s for s in pe.sections if s.Name.startswith(b'.text'))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)


def va2off(va):
    r = va - base
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return r - s.VirtualAddress + s.PointerToRawData
    return None


def label(va):
    o = va2off(va)
    if o is None or o >= len(d):
        return ''
    raw = d[o:o + 64]
    s = raw.split(b'\0')[0]
    if len(s) >= 3 and all(32 <= b < 127 for b in s):
        return repr(s.decode())
    w = raw.split(b'\0\0')[0]
    try:
        ws = (w + b'\0').decode('utf-16le').rstrip('\0')
        if len(ws) >= 3 and ws.isprintable():
            return 'L' + repr(ws)
    except UnicodeDecodeError:
        pass
    return ''


def dis(start, end):
    o = va2off(start)
    for ins in md.disasm(d[o:o + (end - start)], start):
        note = ''
        m = re.search(r'rip ([+-]) 0x([0-9a-f]+)', ins.op_str)
        if m:
            tgt = ins.address + ins.size + int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            note = f'   ; {tgt:x} {label(tgt)}'
        print(f'{ins.address:x}: {ins.mnemonic} {ins.op_str}{note}')


def func_bounds(va):
    o = va2off(va)
    s = d.rfind(b'\xcc\xcc', t.PointerToRawData, o)
    while d[s] == 0xcc:
        s += 1
    e = d.find(b'\xcc\xcc\xcc', o)
    to_va = lambda off: base + t.VirtualAddress + off - t.PointerToRawData
    return to_va(s), to_va(e)


def callers(target):
    lo = t.PointerToRawData
    raw = np.frombuffer(d, dtype=np.uint8, count=t.SizeOfRawData, offset=lo)
    n = len(raw) - 5
    op = raw[:n]
    disp = (raw[1:n + 1].astype(np.int64) | (raw[2:n + 2].astype(np.int64) << 8) |
            (raw[3:n + 3].astype(np.int64) << 16) | (raw[4:n + 4].astype(np.int64) << 24))
    disp = np.where(disp >= 2 ** 31, disp - 2 ** 32, disp)
    va_next = base + t.VirtualAddress + np.arange(n, dtype=np.int64) + 5
    hit = np.nonzero(((op == 0xE8) | (op == 0xE9)) & (va_next + disp == target))[0]
    for h in hit:
        va = base + t.VirtualAddress + int(h)
        fs, _ = func_bounds(va)
        print(f'{"call" if raw[h] == 0xE8 else "jmp "} at {va:x}  (in function {fs:x})')


if sys.argv[2] == 'func':
    s, e = func_bounds(int(sys.argv[3], 16))
    print(f'function {s:x}..{e:x}')
    dis(s, e)
elif sys.argv[2] == 'callers':
    callers(int(sys.argv[3], 16))
else:
    dis(int(sys.argv[2], 16), int(sys.argv[3], 16))
