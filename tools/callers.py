"""List direct call/jmp sites (E8/E9 rel32) of RVAs in a DLL, with the function each sits in.

usage: python -I callers.py <dll> <rva hex> [<rva hex> ...]
"""
import sys
import numpy as np
import pefile

pe = pefile.PE(sys.argv[1], fast_load=True)
pe.parse_data_directories([pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
text = next(s for s in pe.sections if s.Name.startswith(b".text"))
code = np.frombuffer(text.get_data(), np.uint8)
va0 = text.VirtualAddress
rel = code[1:-3].astype(np.int64) | code[2:-2].astype(np.int64) << 8 | code[3:-1].astype(np.int64) << 16 | code[4:].astype(np.int64) << 24
rel = np.where(rel >= 1 << 31, rel - (1 << 32), rel)
pos = np.arange(len(rel))
funcs = sorted((e.struct.BeginAddress, e.struct.EndAddress) for e in getattr(pe, "DIRECTORY_ENTRY_EXCEPTION", []))
starts = np.array([f[0] for f in funcs])
for want in (int(a, 16) for a in sys.argv[2:]):
    hit = pos[(va0 + pos + 5 + rel == want) & ((code[:-4] == 0xE8) | (code[:-4] == 0xE9))]
    print(f"{want:x}:", ", ".join(f"{va0 + h:x} (in {starts[np.searchsorted(starts, va0 + h, 'right') - 1]:x})" for h in hit) or "none")
