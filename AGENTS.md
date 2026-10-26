# Instructions for AI coding assistants

This repository documents modifying the firmware of one specific e-reader (Saraiva "Lev com luz",
Boo Reader 6.3 build 2643). A mistake can leave the device **permanently unbootable** (there is no
UART in this project and no proven recovery for the boot partitions). If you are an AI assistant
helping a human with this, follow these rules. They are stricter than usual on purpose.

## How to behave
- Read `README.md`, `docs/INSTALL.md`, `docs/RECOVERY.md` and `docs/KNOWN-ISSUES.md` before doing anything.
- Start read-only: run `scripts/preflight.sh` and report the result. If it fails, STOP and tell the
  human. Do not "fix" a failing check by changing the device.
- Show the exact command and what it changes, and wait for the human's explicit OK, **before every
  command that writes** to the device (adb push, dd, mount rw, mv, rm, reboot). An approval for one
  step is not an approval for the next one.
- One small, reversible change at a time. After each: is `adb shell` still alive? Did the device
  reboot normally? Then the next change.
- Report faithfully: what was done, what failed, what was NOT tested. Never claim a step worked
  without checking its result on the device.
- Say when you are guessing. The notes in `docs/` mark confirmed facts vs hypotheses; keep that marking.
- Language: answer in the human's language.

## Hard rules (never)
- Never write (`dd`, `cat >`, flashing) to `/dev/nanda`, `/dev/nandb` or `/dev/nandc`: boot loader,
  U-Boot environment, kernel. Never touch `/init`, `/linuxrc`, `/etc/inittab`, `/etc/fstab`,
  `/sbin/init`, busybox, libraries in `/lib`, or the update scripts (`S00`..`S42`, `/bin/update.sh`).
- Never replace or delete `ebrmain`, `boordr.stock` (the original reader) or `DjvuServer`. New
  software goes **next to** the original.
- Never install a `CybUpdate.bin` or a firmware of another model/version, and never leave a
  `CybUpdate.bin` on the device (the boot offers to re-flash everything).
- Never write to `/dev/nandd` while it is mounted; never run `mkfs`/`fsck` on a mounted partition.
- Never `rm -rf` with a variable or a wildcard at the root. Absolute, literal paths only.
- Never write with the battery below 50% or without the USB cable; never reboot or unplug during a write.
- Never leave `/` mounted read-write: always finish with `mount -o remount,ro /`.
- Never leave the rootfs with less than ~15 MB free.
- Never modify the user partition's `system/` or `.adobe-digital-editions` (DRM activation).

## Privacy
- Never print, log or commit: serial number, MAC address, Wi-Fi configuration, DRM activation data,
  or account files (`aplists.xml`, `userconf`, `activation.xml`, `sn.txt`, `wifi.txt`, `rescueurl`).
  If you must inspect them, mask the values BEFORE printing and check the mask.
- Never put device images or firmware into this repository or into a cloud-synced folder.

## Environment notes that save time
- ADB only comes up from the stock reader's menu (Menu > Advanced > Open ADB) or from the plugin
  after KOReader is installed. It drops often, and background processes die with the `adb shell`
  session. `adb exec-out` does not work: use `adb pull`.
- Heavy analysis (strings, grep, disassembly of big binaries) belongs on the PC, not on the device.
- Mass storage and ADB are mutually exclusive on the USB gadget.
- Shell scripts must keep LF line endings.

## Maintenance
The human who published this does not maintain it. Do not suggest opening issues or pull requests
upstream for it; suggest a fork if changes are wanted.
