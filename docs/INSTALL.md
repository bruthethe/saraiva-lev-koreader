# Install guide

Read the disclaimer in the [README](../README.md) first. **Every step has an undo. Do not skip the
checks.** If a step does not behave as described, stop and read [RECOVERY.md](RECOVERY.md).

The order matters: everything up to step 6 only touches the **user (FAT) partition** and is undone by
deleting files. The first write to the **rootfs** is step 7.

Conventions: `adb` is `adb` from the Android platform-tools. Commands starting `adb shell ...` run on
the Lev as root.

---

## 0. Prerequisites

- A Lev com luz, firmware build 2643, **battery >= 50% and the USB cable connected for every write**.
- A PC with `adb` and about 3 GB free, and (to build KOReader) Docker, see [BUILD-KOREADER.md](BUILD-KOREADER.md).
- Time: don't start this if you can't finish the step you are on. Never reboot or unplug mid-write.
- Keep backups **outside** cloud-synced folders (the images contain your device identity).

## 1. Enable ADB on the stock reader

1. Connect the Lev to the PC. It appears as a USB drive.
2. Create an empty file named `adb_debug` in the root of that drive. Eject it.
3. Reconnect the cable; if the Lev asks to "view files", decline. Then on the Lev: **Menu > Advanced > Open ADB**.
4. `adb devices` must list the device. (ADB and USB drive mode are mutually exclusive; ADB drops often, just
   re-open it from the menu.)

## 2. Preflight (read-only)

```
scripts/preflight.sh
```

It checks model, firmware, the md5 of the stock `boordr` and `ebrmain`, battery/USB, free space, mounts
and the frontlight PWM period. **If any required check fails, stop: this guide is not for your device.**

## 3. Back up (read-only) and verify

```
scripts/backup.sh /path/to/backup        # or scripts\backup.ps1 -Destination D:\lev-backup
```

It pulls `nanda`..`nandf` and compares the md5 of each image with the one computed on the device.
All six must print `OK`. Copy your books yourself (`nandg` is not copied).

Optional but recommended: build the restore image and validate it on the PC
(`scripts/build-restore.py`, `scripts/verify-restore.py`). **It has never been tested on a device**
([RECOVERY.md](RECOVERY.md)). Keep the backup somewhere safe.

## 4. Stage KOReader on the user partition (FAT only, nothing active yet)

Get a `koreader-bookeen-*.zip` ([BUILD-KOREADER.md](BUILD-KOREADER.md)), then:

```
adb push koreader-bookeen-*.zip /mnt/fat/ko.zip
adb shell "cd /mnt/fat && unzip -oq ko.zip && rm ko.zip && touch /mnt/fat/koreader/.disabled && sync"
adb shell "ls -a /mnt/fat/koreader | head"
```

`.disabled` is what keeps KOReader inactive for now. **Undo:** delete `/mnt/fat/koreader`.

## 5. Light script for KOReader and the plugin (FAT only)

```
adb push scripts/lev-frontlight.sh /mnt/fat/koreader/lev-frontlight.sh
adb shell "chmod 755 /mnt/fat/koreader/lev-frontlight.sh"
adb push plugin/lev.koplugin /mnt/fat/koreader/plugins/lev.koplugin
```

Make KOReader call the light script instead of `/bin/frontlight`. On the PC:

```
adb pull /mnt/fat/koreader/frontend/device/bookeen/powerd.lua powerd.lua
sed -i "s#'/bin/frontlight ' \.\. tostring(inv_intensity)#'/mnt/fat/koreader/lev-frontlight.sh ' .. tostring(inv_intensity)#" powerd.lua
grep -n lev-frontlight powerd.lua        # must show exactly one line (in setIntensityHW)
adb push powerd.lua /mnt/fat/koreader/frontend/device/bookeen/powerd.lua
```

Only do the `lev-frontlight` part if preflight reported PWM period 23999. Without it the frontlight
simply works with the stock 13.9% floor.

## 6. Optional dry run (nothing installed)

You can see KOReader on the panel without installing anything. The stock reader is **paused** (not
killed) while KOReader runs. Keep this `adb shell` session open: background processes die with it.

```
adb shell
cd /mnt/fat/koreader
BP=$(pidof boordr); kill -STOP $BP
sh ./koreader.sh > /mnt/fat/koreader-run.log 2>&1 &
# ... try it on the device; then, from the same shell:
killall luajit; sleep 1; killall -9 luajit
kill -CONT $BP
```

If the ADB session drops while the stock reader is paused, it stays frozen: hold the power button to
reboot (nothing was written to the system). Optionally `rm /mnt/fat/koreader-run.log` afterwards.

## 7. Install the shim (FIRST WRITE TO THE ROOTFS)

The shim becomes `/mnt/app/boordr`; the original stays as `/mnt/app/boordr.stock` (a hard link, so it
takes no extra space, and at no instant is there a missing reader: the shim replaces `boordr` with an
atomic rename). With `.disabled` present the shim just runs the stock reader, so this step changes
nothing visible.

Check first: battery >= 50%, cable connected, `scripts/preflight.sh` passes, backup verified.

```
adb push scripts/boordr-shim.sh /tmp/boordr.new
adb shell "md5sum /mnt/app/boordr /tmp/boordr.new; sh -n /tmp/boordr.new && echo syntax-ok"
adb shell "mount -o remount,rw / && cp /tmp/boordr.new /mnt/app/boordr.new && chmod 755 /mnt/app/boordr.new && ln /mnt/app/boordr /mnt/app/boordr.stock && mv /mnt/app/boordr.new /mnt/app/boordr; sync; mount -o remount,ro /"
adb shell "mount | grep ' / '; ls -l /mnt/app; md5sum /mnt/app/boordr.stock"
```

Required results: `/` is `ro` again; `boordr.stock` has md5 `5a6dc8b3277d1b1c4e9eef1672e3c637`; `boordr` is
the small script. The shim must have **LF** line endings (see `.gitattributes`).

**Undo:** `adb shell "mount -o remount,rw / && mv /mnt/app/boordr.stock /mnt/app/boordr; sync; mount -o remount,ro /"`
(the rename replaces the shim atomically).

Now reboot normally and confirm the stock reader comes up exactly as before:
`adb shell reboot`. After boot, the running reader should be `/mnt/app/boordr.stock <arg>`.

## 8. (Optional) Minimum-light tweak at boot (rootfs, two NEW files)

Only if preflight said the PWM period is 23999. Two new files, nothing existing is altered:

```
adb push scripts/luz-minima.sh /tmp/.luz.new
adb push scripts/S98luz.sh /tmp/.S98luz.new
adb shell "sh -n /tmp/.luz.new && sh -n /tmp/.S98luz.new && echo ok"
adb shell "mount -o remount,rw / && cp /tmp/.luz.new /usr/bin/.luz.new && cp /tmp/.S98luz.new /etc/init.d/.S98luz.new && chmod 755 /usr/bin/.luz.new /etc/init.d/.S98luz.new && mv /usr/bin/.luz.new /usr/bin/luz-minima.sh && mv /etc/init.d/.S98luz.new /etc/init.d/S98luz.sh; sync; mount -o remount,ro /"
```

(The hidden temporary names don't match the `S??*` pattern that `rcS` runs, so a half-copied file is
never executed.) It runs in the background after the update check and before the reader, and can
never block the boot. **Disable without a shell:** create `luz_off.txt` in the root of the user
partition over USB. **Undo:** `mount -o remount,rw /; rm /etc/init.d/S98luz.sh /usr/bin/luz-minima.sh; sync; mount -o remount,ro /`.

## 9. Switch KOReader on

```
adb shell "rm -f /mnt/fat/koreader/.disabled /mnt/fat/koreader/.fails; sync"
adb shell reboot
```

The Lev boots (a bit slower) straight into KOReader and opens its quick-start document the first
time. **While KOReader runs, the stock reader's USB/ADB handling is gone**: use the plugin
(Tools > "Lev: USB, ADB, stock reader") for USB mode. If the Windows PC shows nothing when you
plug the cable in, that is expected: choose USB mode in the plugin first.

## 10. Verify

- Touch works; open a CBZ; try zoom modes and rotation.
- Frontlight: set the minimum and check it is the dim one; look for flashes.
- Plugin > USB mode: the PC sees a USB drive; eject it from the PC, unplug, KOReader returns.
- Short press on the power button: sleep; short press again: wake.
- Plugin > "Back to the stock reader": KOReader closes and the stock reader starts (**not tested by the
  author**; if it fails use the recovery methods).
- Use it for a day or two before trusting it.

## Going back to the stock reader (any time)

1. In KOReader: plugin > "Back to the stock reader"; or in KOReader's file manager open
   `/mnt/fat/koreader`, long-press a file (for example `README.md`), rename it to `.disabled`, then
   restart the device. Or over USB mode (plugin) create an empty `.disabled` in the `koreader` folder.
2. To remove the shim completely, see step 7 "Undo".
