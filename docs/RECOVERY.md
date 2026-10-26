# Recovery: when something goes wrong

Be honest with yourself about the limits: **without UART there is no way to recover from a broken
boot partition (`nanda`, `nandb`, `nandc`), and this project never writes to them on purpose.**
Everything this project changes is in the rootfs (`nandd`, only a few files) and the user partition,
so the recoveries below cover those.

## Decision table

| Symptom | Try, in order |
|---|---|
| KOReader starts but misbehaves / you want the stock reader | 1. Plugin > "Back to the stock reader". 2. In KOReader's file manager, rename a file inside `/mnt/fat/koreader` to `.disabled`, then restart. 3. Plugin > USB mode, create an empty `.disabled` in the `koreader` folder from the PC. |
| KOReader fails to start | Nothing to do: after two failed starts (each within 120 s) the shim creates `.disabled` itself and the stock reader starts. Be patient a couple of minutes. |
| The device is frozen | Hold the power button to reboot. Nothing persistent depends on the running session. |
| Touch frozen right after boot | Hold power to reboot. (One unexplained case happened, see KNOWN-ISSUES.) |
| The PC shows nothing when you plug the cable in | Expected while KOReader runs: use the plugin's USB mode, or switch to the stock reader. |
| You need ADB while KOReader runs | Plugin > "Enable ADB", or switch to the stock reader and use Menu > Advanced > Open ADB. |
| The shim must go away | With ADB: `mount -o remount,rw /; mv /mnt/app/boordr.stock /mnt/app/boordr; sync; mount -o remount,ro /` (atomic: it replaces the shim). |
| `/` was left read-write | `mount -o remount,ro /` |
| A script you installed hangs the boot | The light hook is a background process after the update check and cannot block it. Create `luz_off.txt` on the user partition to stop it. |

## Restoring the rootfs from a microSD (**NEVER TESTED**)

The firmware's own updater (`/etc/init.d/S42check_update.sh`, `/bin/update.sh`) runs **from the
rootfs**, before the reader starts, and looks for `CybUpdate.bin` on the microSD and then on the user
partition. `scripts/build-restore.py` builds such a file containing only the rootfs (`ROOT` entry,
version 18) from your own `nandd.img` backup and `scripts/verify-restore.py` validates it on the PC the
same way the updater does (tar.bz2, length, md5).

- It does **not** contain the boot partitions, on purpose: a power failure while writing those would be
  an unrecoverable brick.
- It only helps if the kernel, busybox, `rcS` and the `S00`..`S42` scripts still run. If they do not, it
  cannot help.
- The updater needs battery >= 50% or USB power, skips entries whose version is lower than the
  installed one (version 18), and deletes the `.bin` afterwards (create `.update_lock` next to it to
  keep it and have the device power off at the end).
- **The author never tested this on a device.** Treat it as a plausible safety net, not a guarantee.
- **Never leave a `CybUpdate.bin` on the device** (microSD or USB) outside of an intentional restore:
  the boot would offer to re-flash.

## Restoring files by ADB (device still boots far enough for ADB)

```
adb shell "mount -o remount,rw /"
adb push <your-backed-up-original-file> /mnt/app/<name>.new
adb shell "md5sum /mnt/app/<name>.new"            # compare with your backup
adb shell "chmod 755 /mnt/app/<name>.new && mv /mnt/app/<name>.new /mnt/app/<name>; sync; mount -o remount,ro /"
```

Use a temporary name and `mv` (atomic rename): never overwrite a file in place.

Restoring a whole partition with `dd` to `/dev/nandd` while it is mounted as `/` is **dangerous** and
was never validated here. Do not do it unless there is no alternative.

## What cannot be recovered

- Anything that damages `nanda`/`nandb`/`nandc` (loader, U-Boot environment, kernel).
- Overwriting `nande` (`/priv`): it holds the device identity and calibration (waveforms, vcom).
- Reformatting the user partition: the boot script `S20userfs.sh` **reformats** FAT partitions whose
  header it does not recognize. Never corrupt the header of `nandg`/`nande`/`nandf`.
- DRM activation data in `/mnt/fat/.adobe-digital-editions` and `/mnt/fat/system` if deleted without a copy.
