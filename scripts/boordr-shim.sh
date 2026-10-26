#!/bin/sh
# Lev shim, v2. Installed as /mnt/app/boordr. The stock reader is /mnt/app/boordr.stock
# (a hard link to the original file). ebrmain executes this script instead of the stock reader.
#
# - If /mnt/fat/koreader/.disabled exists (it can be created over USB) => stock reader.
# - The lev.koplugin KOReader plugin asks for "usb", "adb" or "stock" by writing to
#   /tmp/lev-mode and exiting KOReader; this shim runs the requested mode and comes back.
KO=/mnt/fat/koreader
STOCK=/mnt/app/boordr.stock
MODE=/tmp/lev-mode

mount_fat() { grep -q ' /mnt/fat ' /proc/mounts 2>/dev/null || mount /mnt/fat >/dev/null 2>&1; }
cable() { [ "$(cat /sys/class/power_supply/usb/online 2>/dev/null)" = 1 ]; }

external_mode() {   # $1 = usb | adb
    cd /
    sync
    if [ "$1" = usb ]; then
        # NEVER export the partition while it is mounted: the PC and the device writing at
        # the same time corrupt the FAT filesystem.
        umount /mnt/fat >/dev/null 2>&1 || { sleep 2; umount /mnt/fat >/dev/null 2>&1; } || return 1
        /etc/init.d/mass_storage.sh start
    else
        /etc/init.d/adb.sh start
    fi
    t=0
    while ! cable; do sleep 1; t=$((t + 1)); [ "$t" -ge 300 ] && break; done   # wait up to 5 min for the cable
    while cable; do sleep 2; done                                              # until it is unplugged
    if [ "$1" = usb ]; then /etc/init.d/mass_storage.sh stop; else /etc/init.d/adb.sh stop; fi
    sync
    return 0
}

mount_fat

while :; do
    if [ -x "$KO/koreader.sh" ] && [ ! -e "$KO/.disabled" ]; then
        rm -f "$MODE"
        cd "$KO" || exec "$STOCK" "$@"
        KO_VIA_BOORDR_SHIM=1
        export KO_VIA_BOORDR_SHIM
        T0=$(cut -d. -f1 /proc/uptime)
        ./koreader.sh
        rc=$?
        T1=$(cut -d. -f1 /proc/uptime)
        cd /

        m=$(cat "$MODE" 2>/dev/null)
        case "$m" in
            usb|adb) rm -f "$MODE"; external_mode "$m"; mount_fat; continue ;;
            stock)   rm -f "$MODE"; mount_fat; : >"$KO/.disabled"; sync; exec "$STOCK" "$@" ;;
        esac

        # Safety switch: two failures in a row, each within 120 s, disable KOReader automatically.
        if [ "$rc" -ne 0 ] && [ $((T1 - T0)) -lt 120 ]; then
            n=$(cat "$KO/.fails" 2>/dev/null)
            n=$(( ${n:-0} + 1 ))
            echo "$n" >"$KO/.fails"
            if [ "$n" -ge 2 ]; then : >"$KO/.disabled"; rm -f "$KO/.fails"; fi
            sync
        else
            rm -f "$KO/.fails"
        fi
        # Exit codes ebrmain understands (from KOReader's own installer): 101 = power off, 11 = relaunch.
        [ "$rc" -eq 0 ] && exit 101
        exit 11
    fi
    exec "$STOCK" "$@"
done
