"""Read-only reverse-engineering tool for the Lev's static ARM binaries.

Given a text string present in the binary, finds the places in the code that reference it
(`ldr rX, [pc, #off]` loading the string address from the literal pool, or a movw/movt pair)
and disassembles the surrounding function.

Usage (Python with capstone and pyelftools installed):
  python tools/re/re-xref.py <binary> "<exact text>" [instructions_before] [instructions_after]
Example:
  python tools/re/re-xref.py ebrmain "/mnt/fat/boordr" 40 80
"""
import struct, sys
import capstone
from elftools.elf.elffile import ELFFile

path, needle = sys.argv[1], sys.argv[2].encode()
before = int(sys.argv[3]) if len(sys.argv) > 3 else 40
after = int(sys.argv[4]) if len(sys.argv) > 4 else 60

f = open(path, 'rb'); e = ELFFile(f)
data = open(path, 'rb').read()
text = e.get_section_by_name('.text')
t_addr, t_off, t_size = text['sh_addr'], text['sh_offset'], text['sh_size']
tbytes = data[t_off:t_off + t_size]

def file_to_vaddr(off):
    for seg in e.iter_segments():
        if seg['p_type'] == 'PT_LOAD' and seg['p_offset'] <= off < seg['p_offset'] + seg['p_filesz']:
            return seg['p_vaddr'] + (off - seg['p_offset'])
    return None

# 1) virtual addresses where the string appears as a complete text (between NULs)
addrs = []
i = -1
while True:
    i = data.find(needle, i + 1)
    if i < 0: break
    if data[i - 1:i] in (b'\0', b'') and data[i + len(needle):i + len(needle) + 1] == b'\0':
        v = file_to_vaddr(i)
        if v is not None: addrs.append(v)
if not addrs:
    sys.exit('string "%s" not found as a complete text' % needle.decode())
print('string at:', [hex(a) for a in addrs])

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
md.detail = True

# 2) literal-pool words that hold those addresses
pool = {}
for k in range(0, len(tbytes) - 3, 4):
    w = struct.unpack_from('<I', tbytes, k)[0]
    if w in addrs: pool[t_addr + k] = w

# 3) pc-relative ldr instructions that load those pool words
xrefs = []
for pa in pool:
    for back in range(8, 4096, 4):
        ia = pa - back
        if ia < t_addr: break
        ins = next(md.disasm(tbytes[ia - t_addr:ia - t_addr + 4], ia), None)
        if ins and ins.mnemonic.startswith('ldr') and 'pc' in ins.op_str and '[pc' in ins.op_str:
            op = ins.operands[-1]
            if op.type == capstone.arm.ARM_OP_MEM and op.mem.base == capstone.arm.ARM_REG_PC:
                tgt = ia + 8 + op.mem.disp
                if tgt == pa: xrefs.append(ia)
# 3b) addresses built with movw/movt (ARMv7), typical of the application code
low = {}   # register -> (value, address of the movw)
for k in range(0, len(tbytes) - 3, 4):
    a = t_addr + k
    ins = next(md.disasm(tbytes[k:k + 4], a), None)
    if not ins or ins.mnemonic not in ('movw', 'movt'): continue
    op0, op1 = ins.operands[0], ins.operands[1]
    if op1.type != capstone.arm.ARM_OP_IMM: continue
    if ins.mnemonic == 'movw':
        low[op0.reg] = (op1.imm & 0xFFFF, a)
    else:
        lo = low.get(op0.reg)
        if lo and a - lo[1] <= 48:
            val = ((op1.imm & 0xFFFF) << 16) | lo[0]
            if val in addrs: xrefs.append(lo[1])
xrefs = sorted(set(xrefs))
print('references in the code:', [hex(x) for x in xrefs])

def show(center):
    start = max(t_addr, center - before * 4)
    # try to start at the nearest prologue (push {..., lr}) before the point
    for a in range(center, max(t_addr, center - 2048), -4):
        ins = next(md.disasm(tbytes[a - t_addr:a - t_addr + 4], a), None)
        if ins and ins.mnemonic in ('push', 'stmdb') and 'lr' in ins.op_str:
            start = max(start, a) if a > center - before * 4 else a
            break
    print('---- function/excerpt starting at', hex(start), '(ref at', hex(center) + ') ----')
    end = min(t_addr + t_size, center + after * 4)
    a = start
    while a < end:
        ins = next(md.disasm(tbytes[a - t_addr:a - t_addr + 4], a), None)
        if not ins:
            w = struct.unpack_from('<I', tbytes, a - t_addr)[0]
            print('%08x:  .word 0x%08x' % (a, w)); a += 4; continue
        extra = ''
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
            op = ins.operands[-1]
            if op.type == capstone.arm.ARM_OP_MEM:
                tgt = a + 8 + op.mem.disp
                if t_addr <= tgt < t_addr + t_size - 3:
                    val = struct.unpack_from('<I', tbytes, tgt - t_addr)[0]
                    extra = '   ; =0x%08x' % val
                    off = None
                    for seg in e.iter_segments():
                        if seg['p_type'] == 'PT_LOAD' and seg['p_vaddr'] <= val < seg['p_vaddr'] + seg['p_filesz']:
                            off = seg['p_offset'] + (val - seg['p_vaddr']); break
                    if off is not None:
                        s = data[off:off + 80].split(b'\0')[0]
                        if len(s) >= 3 and all(32 <= c < 127 for c in s): extra += '  "%s"' % s.decode()
        print('%08x:  %-8s %s%s' % (a, ins.mnemonic, ins.op_str, extra))
        a += 4
for x in xrefs[:3]: show(x)
