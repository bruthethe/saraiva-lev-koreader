#!/bin/sh
# luz-minima.sh (min-light): lowers the frontlight floor of the Saraiva Lev (A13 PWM0).
# The stock video driver only uses 13.9%..50.9% light. When the register value is between the
# driver's dimmest step and step 128, this script compresses that range so the dimmest step
# reaches MIN_REM (8.3%). Above step 128 nothing changes. It writes ONE register only
# (PWM_CH0_PERIOD) and only if the period read back is the expected one.
#
# How: three watchers block waiting for an input event (touch, power/USB key, hardware keys).
# When an event arrives they run a 1 s burst of checks every 20 ms. A slow loop (3 s) is the
# safety net. Idle CPU use is negligible (~0.4%).
# Stop: create /tmp/luz.stop (or kill the PIDs). Disable over USB: create /mnt/fat/luz_off.txt.
REG=0x01c20e04
PER=23999        # period configured by the driver
DRV_MIN=3335     # "remaining" at frontlight 254 (driver floor)
KNEE=5327        # "remaining" at frontlight 128 (untouched from here up)
MIN_REM=2000     # wanted "remaining" at the dimmest step (~8.3%)

fix() {
    V=$(devmem $REG 32)
    N=$((V))
    P=$((N >> 16))
    A=$((N & 65535))
    [ "$P" -eq "$PER" ] || return
    R=$((PER - A))
    if [ "$R" -ge "$DRV_MIN" ] && [ "$R" -lt "$KNEE" ]; then
        NR=$((MIN_REM + (R - DRV_MIN) * (KNEE - MIN_REM) / (KNEE - DRV_MIN)))
        NV=$(( (PER << 16) | (PER - NR) ))
        devmem $REG 32 $(printf '0x%08X' $NV)
    fi
}

burst() {
    mkdir /tmp/luz.lock 2>/dev/null || return
    i=0
    while [ $i -lt 50 ]; do
        fix
        usleep 20000
        i=$((i + 1))
    done
    rmdir /tmp/luz.lock
}

watch_dev() {
    while [ ! -f /tmp/luz.stop ]; do
        dd if="$1" of=/dev/null bs=16 count=1 2>/dev/null
        burst
    done
}

rm -f /tmp/luz.stop
rmdir /tmp/luz.lock 2>/dev/null
fix
for d in /dev/input/event0 /dev/input/event1 /dev/input/event2; do
    [ -e "$d" ] && watch_dev "$d" &
done
# During the first ~30 s after start (boot) the stock reader still sets the light without any
# touch: back-to-back bursts cover that window.
b=0
while [ $b -lt 30 ] && [ ! -f /tmp/luz.stop ]; do
    burst
    b=$((b + 1))
done
# Safety net. If /mnt/fat/luz_off.txt exists (created over USB), the program exits.
while [ ! -f /tmp/luz.stop ]; do
    [ -f /mnt/fat/luz_off.txt ] && break
    fix
    sleep 3
done
touch /tmp/luz.stop
