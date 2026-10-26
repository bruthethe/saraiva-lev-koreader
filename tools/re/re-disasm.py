"""Disassembles an excerpt of a static ARM binary, annotating strings and calls.

Usage: python tools/re/re-disasm.py <binary> <address_hex> <n_instructions>
Annotates: movw/movt and pc-relative ldr that build string addresses; bl targets.
"""
import struct, sys
import capstone
from elftools.elf.elffile import ELFFile

path, start, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
data = open(path, 'rb').read(); e = ELFFile(open(path, 'rb'))
t = e.get_section_by_name('.text'); ta, to, ts = t['sh_addr'], t['sh_offset'], t['sh_size']
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM); md.detail = True

def va_to_str(val):
    for seg in e.iter_segments():
        if seg['p_type'] == 'PT_LOAD' and seg['p_vaddr'] <= val < seg['p_vaddr'] + seg['p_filesz']:
            off = seg['p_offset'] + (val - seg['p_vaddr'])
            s = data[off:off + 100].split(b'\0')[0]
            if len(s) >= 2 and all(32 <= c < 127 for c in s): return s.decode()
    return None

def word_at(va):
    return struct.unpack_from('<I', data, to + va - ta)[0]

regs = {}
a = start
for _ in range(n):
    if not (ta <= a < ta + ts): break
    ins = next(md.disasm(data[to + a - ta: to + a - ta + 4], a), None)
    if not ins:
        print('%08x:  .word 0x%08x' % (a, word_at(a))); a += 4; continue
    note = ''
    if ins.mnemonic == 'movw' and ins.operands[1].type == capstone.arm.ARM_OP_IMM:
        regs[ins.operands[0].reg] = ins.operands[1].imm & 0xFFFF
    elif ins.mnemonic == 'movt' and ins.operands[0].reg in regs:
        val = ((ins.operands[1].imm & 0xFFFF) << 16) | regs[ins.operands[0].reg]
        s = va_to_str(val)
        note = '   ; =0x%x%s' % (val, ('  "%s"' % s) if s else '')
    elif ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str and ins.operands[-1].type == capstone.arm.ARM_OP_MEM:
        tg = a + 8 + ins.operands[-1].mem.disp
        if ta <= tg < ta + ts - 3:
            val = word_at(tg); s = va_to_str(val)
            note = '   ; =0x%x%s' % (val, ('  "%s"' % s) if s else '')
    print('%08x:  %-8s %s%s' % (a, ins.mnemonic, ins.op_str, note))
    a += 4
