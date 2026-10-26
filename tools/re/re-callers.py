"""Lists who calls (bl/b/blx) a function of a static ARM binary and shows nearby strings.

Usage: python tools/re/re-callers.py <binary> <address_hex> [show_caller_asm_N]
  - without the 3rd argument: only lists the callers and the function (prologue push ... lr) holding each.
  - with N: disassembles N instructions around the first caller.
"""
import struct, sys
import capstone
from elftools.elf.elffile import ELFFile

path, target = sys.argv[1], int(sys.argv[2], 16)
show_n = int(sys.argv[3]) if len(sys.argv) > 3 else 0
data = open(path, 'rb').read(); e = ELFFile(open(path, 'rb'))
t = e.get_section_by_name('.text'); ta, to, ts = t['sh_addr'], t['sh_offset'], t['sh_size']
tb = data[to:to + ts]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM); md.detail = True

def va_to_str(val):
    for seg in e.iter_segments():
        if seg['p_type'] == 'PT_LOAD' and seg['p_vaddr'] <= val < seg['p_vaddr'] + seg['p_filesz']:
            off = seg['p_offset'] + (val - seg['p_vaddr'])
            s = data[off:off + 80].split(b'\0')[0]
            if len(s) >= 3 and all(32 <= c < 127 for c in s): return s.decode()
    return None

def func_start(a):
    for x in range(a, max(ta, a - 8192), -4):
        ins = next(md.disasm(tb[x - ta:x - ta + 4], x), None)
        if ins and ins.mnemonic in ('push', 'stmdb') and 'lr' in ins.op_str: return x
    return None

callers = []
for k in range(0, ts - 3, 4):
    a = ta + k
    ins = next(md.disasm(tb[k:k + 4], a), None)
    if ins and ins.mnemonic in ('bl', 'b', 'blx') and ins.operands and ins.operands[0].type == capstone.arm.ARM_OP_IMM:
        if ins.operands[0].imm == target: callers.append((a, ins.mnemonic))
print('callers of', hex(target), ':', len(callers))
for a, m in callers[:60]:
    print('  %s %08x  (function starts at %s)' % (m, a, hex(func_start(a)) if func_start(a) else '?'))

if show_n and callers:
    center = callers[0][0]
    a = max(ta, center - show_n * 4)
    end = min(ta + ts, center + show_n * 4)
    while a < end:
        ins = next(md.disasm(tb[a - ta:a - ta + 4], a), None)
        if not ins: a += 4; continue
        extra = ''
        if ins.mnemonic in ('movw',) and ins.operands[1].type == capstone.arm.ARM_OP_IMM:
            nxt = next(md.disasm(tb[a - ta + 4:a - ta + 8], a + 4), None)
            if nxt and nxt.mnemonic == 'movt' and nxt.operands[0].reg == ins.operands[0].reg:
                val = (nxt.operands[1].imm << 16) | ins.operands[1].imm
                s = va_to_str(val)
                extra = '   ; =0x%x%s' % (val, ('  "%s"' % s) if s else '')
        print('%08x:  %-8s %s%s' % (a, ins.mnemonic, ins.op_str, extra))
        a += 4
