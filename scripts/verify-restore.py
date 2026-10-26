"""Validates a CybUpdate.bin the way /bin/update.sh does: bzcat | tar -x, then length and md5 of each
`contents` line, and compares the image with the prefix of the backup.
Usage: python -I scripts/verify-restore.py <CybUpdate.bin> <nandd.img>
"""
import bz2, hashlib, sys, tarfile

binf, backup = sys.argv[1], sys.argv[2]
ok = True
with tarfile.open(binf, 'r:bz2') as tar:
    names = tar.getnames()
    print('files in the tar:', names)
    contents = tar.extractfile('contents').read().decode()
    for line in contents.splitlines():
        typ, name, length, md5, ver = line.split('|')
        blob = tar.extractfile(name).read()
        good = len(blob) == int(length) and hashlib.md5(blob).hexdigest() == md5
        h = hashlib.md5()
        with open(backup, 'rb') as f:
            left = len(blob)
            while left:
                chunk = f.read(min(left, 1 << 20)); h.update(chunk); left -= len(chunk)
        same = h.hexdigest() == md5
        print('%s %s len=%s ver=%s: contents %s, same as backup: %s' % (typ, name, length, ver, 'OK' if good else 'FAILED', same))
        ok = ok and good and same
    if not contents.endswith('\n'):
        print('WARNING: `contents` has no trailing newline (the updater `while read` would skip the last line)'); ok = False
print('RESULT:', 'OK' if ok else 'FAILED')
sys.exit(0 if ok else 1)
