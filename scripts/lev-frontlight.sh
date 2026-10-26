#!/bin/sh
# KOReader on the Lev: calls the stock /bin/frontlight tool and immediately applies the same
# compression as luz-minima.sh (13.9% -> 8.3% at the minimum), so there is no late-correction
# flash. KOReader calls this script instead of /bin/frontlight (see docs/INSTALL.md).
/bin/frontlight "$@"
[ -f /mnt/fat/luz_off.txt ] && exit 0
[ -n "$1" ] || exit 0
REG=0x01c20e04; PER=23999; DRV_MIN=3335; KNEE=5327; MIN_REM=2000
V=$(devmem $REG 32); N=$((V)); P=$((N>>16)); A=$((N&65535))
[ "$P" -eq "$PER" ] || exit 0
R=$((PER-A))
if [ "$R" -ge "$DRV_MIN" ] && [ "$R" -lt "$KNEE" ]; then
  NR=$((MIN_REM+(R-DRV_MIN)*(KNEE-MIN_REM)/(KNEE-DRV_MIN)))
  NV=$(( (PER<<16)|(PER-NR) ))
  devmem $REG 32 $(printf '0x%08X' $NV)
fi
