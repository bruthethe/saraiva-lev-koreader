# What was done to the device, in order

A condensed, de-identified log of every change made to the author's device, with the undo for each.
Read-only work (reading files over ADB, backups, offline analysis) is not listed in detail.

## Read-only phase
- Enabled ADB (empty `adb_debug` on the user partition + Menu > Advanced > Open ADB).
- Read the init scripts, update scripts, mounts and partitions; pulled `nanda`..`nandf` and verified each image's md5
  against `md5sum /dev/nandX` on the device (all six equal).
- Built a rootfs-only restore `CybUpdate.bin` on the PC and validated it with the updater's own checks. **Never
  tried on the device**, by decision.

## Removing the store banner (Home screen ad)
1. User partition: moved `system/user/store/estore_*` out of the way. The built-in `estoresa.jpg` appeared instead.
2. **Rootfs write #1:** replaced `/mnt/app/res/img/estoresa.jpg` with an all-white JPEG (same size and format),
   using `remount,rw` -> push to `.novo` -> md5 -> `chmod` + `mv` -> `sync` -> `remount,ro`.
   Undo: push the original back the same way.
3. The old banner kept coming back because the reader **caches decoded images** in `system/thumbnail`. Moving that
   cache to a backup folder and running `killall boordr` (the supervisor relaunches the reader) fixed it.
   Lesson: the file format (baseline vs progressive JPEG) was not the issue; the cache was.

## Minimum frontlight
1. Measured the driver's step table by reading the PWM register while setting `/bin/frontlight` steps.
2. Prototyped `luz-minima.sh` in `/tmp` and iterated: 1 s polling flashed in the dark; 100 ms polling used 6.8% CPU; the
   event-driven version uses ~0.4%.
3. **Rootfs write #2** (two NEW files, nothing existing altered): `/usr/bin/luz-minima.sh` and `/etc/init.d/S98luz.sh`.
   Undo: delete both, or create `luz_off.txt` on the user partition.

## KOReader
1. Built KOReader's `bookeen` target in Docker (see BUILD-KOREADER.md).
2. Dry runs from the user partition with the stock reader paused (`kill -STOP` / `kill -CONT`): screen, touch, CBZ,
   frontlight, button mapping (centre button = key 139), power-button sleep.
3. Frontlight in KOReader: first through `/bin/frontlight` (worked, with a ~1 s flash before the daemon corrected it);
   then through `lev-frontlight.sh` (correction in the same call, flash almost imperceptible).
4. **Rootfs write #3:** shim v1 at `/mnt/app/boordr` (original kept as `boordr.stock`, hard link), `.disabled` present
   so it was transparent. Rebooted: stock reader came up normally.
5. Removed `.disabled`, rebooted: KOReader at boot. But the PC saw **nothing** on USB (the stock reader provides USB).
   Went back to the stock reader by renaming a file to `.disabled` from inside KOReader.
6. Read `ebrmain`'s handling of exit code 11 (it does not start USB), found the cable sensor
   (`/sys/class/power_supply/usb/online`) and wrote the plugin plus **shim v2** (USB/ADB modes, safety switch).
7. **Rootfs write #4:** shim v2 (atomic `cp` to `.new` + `mv`). Removed `.disabled`, rebooted: KOReader at boot, the
   plugin's USB mode worked, KOReader came back after unplugging.
8. Real-world use: manga reading, landscape rotation, sleep overnight on battery.

## One incident
Before the first reboot with the shim, the stock reader was restarted with `killall boordr` as a quick test and
the touchscreen stopped responding once; a forced reboot fixed it. Cause unknown, never reproduced.
