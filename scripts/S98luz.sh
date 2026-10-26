#!/bin/sh
# S98luz.sh: starts /usr/bin/luz-minima.sh in the background. Never blocks the boot.
# To disable: delete this file (rootfs mounted rw) or create /mnt/fat/luz_off.txt over USB
# (the program then exits by itself).
[ -x /usr/bin/luz-minima.sh ] && ( setsid /usr/bin/luz-minima.sh </dev/null >/dev/null 2>&1 & )
exit 0
