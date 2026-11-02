"""Find functions in a DLL that store to all the given struct offsets (e.g. a setter for
player +0x50/+0x54/+0x56). Uses the exception directory for function bounds.

usage: python -I find_stores.py <dll> <offset hex> [<offset hex> ...]
"""
import sys
import pefile
import capstone

pe = pefile.PE(sys.argv[1], fast_load=True)
pe.parse_data_directories([pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
want = {int(a, 16) for a in sys.argv[2:]}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
img = pe.get_memory_mapped_image()
for e in pe.DIRECTORY_ENTRY_EXCEPTION:
    b, end = e.struct.BeginAddress, e.struct.EndAddress
    if end - b > 4000:
        continue
    seen = set()
    for ins in md.disasm(img[b:end], b):
        if ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        dst = ins.operands[0]
        if dst.type == capstone.x86.X86_OP_MEM and dst.mem.disp in want and dst.mem.base not in (0, capstone.x86.X86_REG_RSP, capstone.x86.X86_REG_RIP):
            seen.add(dst.mem.disp)
    if seen == want:
        print(f"{b:x}-{end:x}")
