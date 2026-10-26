"""Finds references to an ADDRESS (not a string) in a static ARM binary: movw/movt pairs.
Useful for global variables (.data/.bss) and objects.

Usage: python tools/re/re-addrxref.py <binary> <address_hex> [tolerance_bytes]
  If tolerance_bytes > 0, also lists references to addresses within [addr, addr+tolerance).
"""
import struct, sys
import capstone
from elftools.elf.elffile import ELFFile

path, target = sys.argv[1], int(sys.argv[2], 16)
tol = int(sys.argv[3]) if len(sys.argv) > 3 else 0
data = open(path, 'rb').read(); e = ELFFile(open(path, 'rb'))
t = e.get_section_by_name('.text'); ta, to, ts = t['sh_addr'], t['sh_offset'], t['sh_size']
tb = data[to:to + ts]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM); md.detail = True
lo, hi = target, target + max(tol, 1)

def func_start(a):
    for x in range(a, max(ta, a - 8192), -4):
        ins = next(md.disasm(tb[x - ta:x - ta + 4], x), None)
        if ins and ins.mnemonic in ('push', 'stmdb') and 'lr' in ins.op_str: return x
    return None

hits = []
low = {}
for k in range(0, ts - 3, 4):
    a = ta + k
    ins = next(md.disasm(tb[k:k + 4], a), None)
    if not ins or ins.mnemonic not in ('movw', 'movt'): continue
    o0, o1 = ins.operands[0], ins.operands[1]
    if o1.type != capstone.arm.ARM_OP_IMM: continue
    if ins.mnemonic == 'movw':
        low[o0.reg] = (o1.imm & 0xFFFF, a)
    else:
        l = low.get(o0.reg)
        if l and a - l[1] <= 48:
            v = ((o1.imm & 0xFFFF) << 16) | l[0]
            if lo <= v < hi: hits.append((l[1], v))
print('references (movw/movt):', len(hits))
seen = {}
for a, v in hits:
    fs = func_start(a)
    seen.setdefault(fs, []).append((a, v))
for fs, lst in sorted(seen.items(), key=lambda x: (x[0] is None, x[0])):
    print('  function %s: %s' % (hex(fs) if fs else '?', ', '.join('%x(+%d)' % (a, v - target) for a, v in lst[:6])))
