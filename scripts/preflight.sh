#!/usr/bin/env bash
# preflight.sh - READ-ONLY compatibility check. Run it BEFORE any change.
#
# It writes nothing to the device. It checks that the device is the one this project was done on
# (Saraiva Lev com luz, SKU CYBOY4F-SA, Boo Reader 6.3 build 2643, rootfs version 18) and that
# the conditions for a safe write are met. If a REQUIRED check fails, do not continue.
#
# Usage:  scripts/preflight.sh            (needs `adb` in PATH and exactly one device with ADB on)
#
# Privacy: it only prints the two SKU characters of the serial number, never the serial itself.
# Windows: run it in Git Bash or WSL (it only needs bash and adb).

STOCK_BOORDR_MD5=5a6dc8b3277d1b1c4e9eef1672e3c637
STOCK_EBRMAIN_MD5=2619e5599ad530affeb6b6714939dd9e

fail=0; warn=0
ok()   { printf '  [ OK ] %s\n' "$*"; }
bad()  { printf '  [FAIL] %s\n' "$*"; fail=$((fail + 1)); }
note() { printf '  [WARN] %s\n' "$*"; warn=$((warn + 1)); }
sh_() { adb shell "$1" 2>/dev/null | tr -d '\r'; }

echo "== Device =="
n=$(adb devices | awk 'NR>1 && $2=="device"' | wc -l)
if [ "$n" -ne 1 ]; then bad "expected exactly 1 ADB device, found $n (open Menu > Advanced > Open ADB)"; exit 1; fi
ok "one ADB device"

kern=$(sh_ 'uname -r')
case "$kern" in 3.0.8*) ok "kernel $kern" ;; *) bad "kernel is '$kern', expected 3.0.8+" ;; esac

arch=$(sh_ 'uname -m')
[ "$arch" = armv7l ] && ok "armv7l" || bad "arch is '$arch', expected armv7l"

ver=$(sh_ 'cat /etc/version 2>/dev/null' | head -1)
[ "$ver" = 18 ] && ok "rootfs version 18" || bad "rootfs version is '$ver', expected 18"

sku=$(sh_ 'SN=$(nvram -s 2>/dev/null | cut -d= -f2); echo "$SN" | cut -c8-9')
[ "$sku" = 4F ] && ok "SKU code '4F' (Lev com luz)" || bad "SKU code is '$sku', expected 4F (the project was done on the 'Lev com luz')"

echo "== Stock software =="
shim=$(sh_ 'head -c 2 /mnt/app/boordr')
if [ "$shim" = '#!' ]; then
    note "/mnt/app/boordr is a script: a shim is probably already installed"
    bmd5=$(sh_ 'md5sum /mnt/app/boordr.stock 2>/dev/null' | cut -d' ' -f1)
    what="/mnt/app/boordr.stock"
else
    bmd5=$(sh_ 'md5sum /mnt/app/boordr' | cut -d' ' -f1)
    what="/mnt/app/boordr"
fi
[ "$bmd5" = "$STOCK_BOORDR_MD5" ] && ok "$what matches the known stock reader" || bad "$what md5 is '$bmd5' (expected $STOCK_BOORDR_MD5): different firmware build"
emd5=$(sh_ 'md5sum /mnt/app/ebrmain' | cut -d' ' -f1)
[ "$emd5" = "$STOCK_EBRMAIN_MD5" ] && ok "ebrmain matches" || bad "ebrmain md5 is '$emd5' (expected $STOCK_EBRMAIN_MD5)"

echo "== Conditions for a safe write =="
cap=$(sh_ 'cat /sys/class/power_supply/battery/capacity')
usb=$(sh_ 'cat /sys/class/power_supply/usb/online')
if [ -n "$cap" ] && [ "$cap" -ge 50 ] 2>/dev/null && [ "$usb" = 1 ]; then ok "battery ${cap}% and USB connected"
else bad "need battery >= 50% AND the USB cable connected (battery='${cap}', usb='${usb}')"; fi

root=$(sh_ 'mount' | awk '$3=="/" && $1=="/dev/nandd" {print $6}')
case "$root" in *ro*) ok "/ (nandd) is mounted read-only" ;; *) note "/ mount flags: '$root' (should be ro when idle)" ;; esac

free_kb=$(sh_ 'df / | tail -1' | awk '{print $4}')
if [ -n "$free_kb" ] && [ "$free_kb" -ge 20000 ] 2>/dev/null; then ok "rootfs free space ${free_kb} KB"
else bad "rootfs free space is '${free_kb}' KB (need >= 20000 KB; never go below ~15 MB)"; fi

fatw=$(sh_ 'mount' | awk '$3=="/mnt/fat" {print $6}')
case "$fatw" in *rw*) ok "/mnt/fat mounted rw" ;; *) bad "/mnt/fat is not mounted rw ('$fatw')" ;; esac

fatfree=$(sh_ 'df /mnt/fat | tail -1' | awk '{print $4}')
[ -n "$fatfree" ] && [ "$fatfree" -ge 300000 ] 2>/dev/null && ok "/mnt/fat free space ${fatfree} KB" || note "/mnt/fat free space is '${fatfree}' KB (KOReader needs ~90 MB)"

if sh_ '[ -e /mnt/update/CybUpdate.bin -o -e /mnt/fat/CybUpdate.bin -o -e /mnt/sd/CybUpdate.bin ] && echo yes' | grep -q yes; then
    bad "a CybUpdate.bin is present on the device: remove it (the boot would offer to re-flash)"
else ok "no CybUpdate.bin lying around"; fi

echo "== Frontlight (only needed for the min-light tweak) =="
reg=$(sh_ 'devmem 0x01c20e04 32')
per=$(( (reg >> 16) & 0xFFFF )) 2>/dev/null
[ "$per" = 23999 ] && ok "PWM period is 23999 (the value the light scripts expect)" || note "PWM period reads '$per' (expected 23999): do NOT install the light scripts"

echo
if [ "$fail" -eq 0 ]; then
    echo "RESULT: all required checks passed ($warn warning(s)). Next: make a verified backup (scripts/backup.sh)."
    exit 0
else
    echo "RESULT: $fail required check(s) FAILED. Do not change anything on this device."
    exit 1
fi
