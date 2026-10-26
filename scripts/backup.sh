#!/usr/bin/env bash
# backup.sh - READ-ONLY backup of the device partitions (nanda..nandf) with md5 verification.
# nandg is the user/books partition and is not copied here (copy your books yourself).
# Usage: scripts/backup.sh /path/to/backup-dir        (needs ~1.1 GB free)
# Keep the backup OUT of cloud-synced folders: nande contains the device identity (serial, MAC)
# and the user partition may contain Wi-Fi passwords and DRM activation data.
set -u
dest=${1:?usage: backup.sh <destination-dir>}
mkdir -p "$dest"
bad=0
for p in nanda nandb nandc nandd nande nandf; do
    adb pull "/dev/$p" "$dest/$p.img" >/dev/null || { echo "$p: pull FAILED"; bad=1; continue; }
    local_md5=$(md5sum "$dest/$p.img" | cut -d' ' -f1)
    dev_md5=$(adb shell "md5sum /dev/$p" | tr -d '\r' | cut -d' ' -f1)
    if [ "$local_md5" = "$dev_md5" ]; then echo "$p: OK"; else echo "$p: MISMATCH ($local_md5 vs $dev_md5)"; bad=1; fi
done
exit $bad
