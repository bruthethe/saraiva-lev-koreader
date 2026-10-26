"""Builds a rootfs-ONLY restore CybUpdate.bin (ROOT -> /dev/nandd) from a backup image.

Format (read from the device's /bin/update.sh): a tar.bz2 holding `contents` and the files it lists.
Each line of `contents`: TYPE|file|length|md5|version. The updater skips an entry whose version is
lower than /etc/version (18 on this firmware).

NOT TESTED ON A DEVICE. It only runs on the PC and never touches the device. Use verify-restore.py
on the result. See docs/RECOVERY.md for the limits (it does not restore the boot partitions).

Usage: python -I scripts/build-restore.py <nandd.img> <output.bin> [version]
"""
import bz2, hashlib, io, struct, sys, tarfile

src, out = sys.argv[1], sys.argv[2]
ver = int(sys.argv[3]) if len(sys.argv) > 3 else 18

with open(src, 'rb') as f:
    f.seek(1024)
    sb = f.read(1024)
magic = struct.unpack_from('<H', sb, 56)[0]
if magic != 0xEF53:
    sys.exit('ext2/3/4 superblock not found (magic=%#x)' % magic)
blocks_lo = struct.unpack_from('<I', sb, 4)[0]
log_bs = struct.unpack_from('<I', sb, 24)[0]
feat_incompat = struct.unpack_from('<I', sb, 96)[0]
blocks_hi = struct.unpack_from('<I', sb, 0x150)[0] if feat_incompat & 0x80 else 0
fs_size = ((blocks_hi << 32) | blocks_lo) * (1024 << log_bs)
print('filesystem size: %d bytes (%.1f MB)' % (fs_size, fs_size / 2**20))

NAME = 'rootfs.fex'
data = open(src, 'rb').read(fs_size)
assert len(data) == fs_size
md5 = hashlib.md5(data).hexdigest()
contents = ('ROOT|%s|%d|%s|%d\n' % (NAME, len(data), md5, ver)).encode()

with open(out, 'wb') as raw, bz2.BZ2File(raw, 'wb', compresslevel=9) as bz:
    with tarfile.open(fileobj=bz, mode='w|') as tar:
        for name, blob in (('contents', contents), (NAME, data)):
            ti = tarfile.TarInfo(name)
            ti.size, ti.mode, ti.uid, ti.gid, ti.mtime = len(blob), 0o644, 0, 0, 0
            tar.addfile(ti, io.BytesIO(blob))
print('written:', out)
print('contents:', contents.decode().strip())
