"""EXPERIMENTAL, NEVER APPLIED TO A DEVICE. Do not use this unless you know what you are doing.

Generates a copy of the stock `boordr` WITHOUT the "Shop" item (id 0x51) in the navigation bar.

The bar constructor (compiled twice: 0x167990 and 0x167d80 in build 2643) pushes the default item
ids onto the global vector at 0x25b3d88. In each copy the instruction `mov r2,#0x51` opens the
block that pushes the Shop item; we replace it with `b <instruction after the block>`.

Open risks: code elsewhere might assume fixed item positions, and the item width comes from a
division by 5, so with 4 items the bar may leave an empty slot. Untested. The Home-screen "Shop"
tile is a different widget and was not located.

Because this project replaces the whole reader with KOReader, this patch is kept only as research.
It only works on the exact stock `boordr` with md5 5a6dc8b3277d1b1c4e9eef1672e3c637 (build 2643).

Usage: python patch-boordr-noshop.py <original_boordr> <output>
It does not touch the device.
"""
import hashlib, struct, sys

src, dst = sys.argv[1], sys.argv[2]
data = bytearray(open(src, 'rb').read())

# vaddr -> file offset in the text segment: off = vaddr - 0x8000 (ET_EXEC, .text 0x80e0 @ 0xe0)
# (instruction_address, original_instruction, branch_target)
PATCHES = [
    (0x167BEC, 0xE3A02051, 0x167C18),   # constructor A: mov r2,#0x51  -> b 0x167c18
    (0x167FDC, 0xE3A02051, 0x168008),   # constructor B: mov r2,#0x51  -> b 0x168008
]

def branch(frm, to):
    off = (to - (frm + 8)) // 4
    assert (to - (frm + 8)) % 4 == 0 and -0x800000 <= off < 0x800000
    return 0xEA000000 | (off & 0xFFFFFF)

for addr, orig, tgt in PATCHES:
    o = addr - 0x8000
    cur, = struct.unpack_from('<I', data, o)
    if cur != orig:
        sys.exit('unexpected bytes at 0x%x: %08x (expected %08x). Different binary from the one analysed.' % (addr, cur, orig))
    struct.pack_into('<I', data, o, branch(addr, tgt))
    print('0x%x: %08x -> %08x' % (addr, orig, branch(addr, tgt)))

open(dst, 'wb').write(data)
print('original md5:', hashlib.md5(open(src, 'rb').read()).hexdigest())
print('patched md5:', hashlib.md5(bytes(data)).hexdigest())
print('size:', len(data))
