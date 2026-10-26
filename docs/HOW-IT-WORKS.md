# How the Saraiva Lev works inside

Research notes from reading the device over ADB (read-only) and the stock binaries on a PC.
`[CONFIRMED]` = seen in a file or on the device. `[HYPOTHESIS]` = not verified. No personal
identifiers are recorded here.

## 1. What the device is

- [CONFIRMED] The firmware is **Saraiva-specific**: `/system/device_info.sh` knows two models, read from
  characters 8-9 of the serial number (`4S` = "Lev", `4F` = "Lev com luz"). The "Lev com luz" is SKU
  `CYBOY4F-SA`. It is a Bookeen platform (Cybook Muse family) with a Saraiva firmware, **not** the same as
  the public Muse/Odyssey firmwares (2326, 2350, 2536...). Installing one of those is a variant swap, not a version swap.
- [CONFIRMED] 1024x758 panel, Allwinner A13 ("AWA13"), Linux 3.0.8+ (jenkins build of 2018-02-12), Buildroot 2011.02,
  init is busybox, 256 MB RAM (about 90-115 MB free with the stock reader).

## 2. Storage (NAND) and partitions

| Device | Size | Role |
|---|---|---|
| nanda (`/dev/boot`) | 32 MB | FAT16 with the Allwinner boot folder: `BOOT.AXF`, `SCRIPT.BIN` (FEX hardware config), `LINUX/U-BOOT.BIN`, `LINUX/BIMAGE` (kernel), boot logo |
| nandb | 16 MB | **U-Boot environment** (text) |
| nandc | 16 MB | Android-format boot image (`ANDROID!`, sun5i): kernel + ramdisk; `root=/dev/nandc` in the cmdline is this ramdisk |
| nandd (`/dev/rootfs`) | 512 MB | ext4 root filesystem (about 242 MB used), mounted **read-only** on `/` |
| nande (`/dev/priv`) | 32 MB | FAT on `/priv`: `store/nvram` (identity, MAC, calibration), waveform, vcom, ADE and Wi-Fi config |
| nandf (`/dev/update`) | 500 MB | scratch area for the updater |
| nandg (`/dev/fat`) | ~2.7 GB | the user/books partition, FAT, mounted on `/mnt/fat` |

`/priv/store/nvram` holds the device identity and calibration: never touch it.

## 3. Boot sequence

1. Allwinner loader (`BOOT.AXF`) -> U-Boot (environment in nandb: `bootcmd=run setargs boot_normal`,
   `boot_normal=nand read 40007800 boot;boota 40007800`, `root=/dev/nandc init=/init`). The environment also
   has `boot_recovery`/`boot_fastboot` triggered by key-value ranges; what hardware button that is, and whether
   the "recovery" partition exists, is unknown.
2. Kernel -> `/init` (busybox) -> `/etc/inittab` -> `/etc/init.d/rcS`, which runs the `S??*` scripts in order
   and *sources* the `.sh` ones in a subshell (a syntax error or `exit` only aborts that script; a hang hangs the boot).
3. Relevant order: `S01modules` -> `S10udev` -> `S20userfs` (checks/**formats** the FAT partitions if the header
   is not recognized) -> `S22Mount` -> `S33Store` -> `S40factory_reset` -> **`S42check_update`** -> `S80late_boot`
   (sets the frontlight) -> *(`S98luz.sh` in this project)* -> **`S99ebrmain`** (starts `/mnt/app/ebrmain`).
4. `ebrmain` (1.7 MB, static ARM) is a **supervisor**: it launches `/mnt/app/boordr` (the reader, 39.6 MB, with the
   store integration, C++, boost/cairo/ICU/SQLite) and relaunches it if it dies. `DjvuServer` is a helper.

## 4. The firmware updater

- [CONFIRMED] `/etc/init.d/S42check_update.sh` and `/bin/update.sh` run **from the rootfs**, before `ebrmain`.
  They look for `CybUpdate.bin` (four spellings) on `/mnt/sd` and then `/mnt/fat`.
- Format: `bzcat file | tar -x` yields a `contents` file with lines `TYPE|file|length|md5|version`; `LOAD` -> nanda,
  `BOOT` -> nandc, `ROOT` -> nandd. Length and md5 are checked, then a raw `dd`.
- **Version guard:** an entry with a version lower than the installed one (`/etc/version` = 18 for ROOT) is
  *skipped*. A "downgrade" ROOT simply does not get written.
- Needs battery >= 50% or USB power. With `.update_lock` next to the file it keeps the `.bin` and powers off at the
  end; otherwise it deletes the `.bin` and reboots.
- Consequence: a `CybUpdate.bin` on a **microSD** can restore the rootfs even if the reader is broken, as long
  as the kernel, busybox, `rcS` and `S00..S42` still run. `ebrmain` also has its own update logic
  (`/mnt/*/cybook_upgrade`, `CybUpdate.lock`, `/private/.newupdate`, `nvram -u`); not analysed in depth.
  A file named `cybook_upgrade` on `/mnt/{sd,fat,ext1,ext2}` seems to be run once by `ebrmain` at start-up (the
  KOReader port's installer relies on this); this project did not use it.

## 5. USB and ADB

- [CONFIRMED] `/etc/init.d/mass_storage.sh` and `/etc/init.d/adb.sh` configure the Android-style USB gadget
  (`/sys/class/android_usb/android0`). They are **mutually exclusive**. `mass_storage.sh start` exports `/dev/fat`
  as a raw block device: it must be **unmounted** first or the filesystem can be corrupted.
- The scripts are called from the stock reader's UI side (the `ebrmain` binary contains the strings). The ADB
  daemon is never started at boot; it only starts from the menu (Menu > Advanced > Open ADB, with an empty
  `adb_debug` file on the user partition).
- The `adbd` on this device does not support `exec-out`; use `adb pull`. The USB cable is detectable through
  `/sys/class/power_supply/usb/online`.
- [CONFIRMED] The stock reader's menu shows the USB prompt; KOReader's Bookeen port has no USB mass-storage mode,
  hence the shim and plugin in this project.

## 6. Input devices

`event0` = `sun4i-keyboard` (hardware centre button, key 139), `event1` = `axp20-supplyer` (power button),
`event2` = `gt80x` (touchscreen). Frontlight: see [FRONTLIGHT.md](FRONTLIGHT.md).

## 7. The shim design

`ebrmain` executes `/mnt/app/boordr` (resource dir: `/mnt/app/res`; the stock reader is spawned with a numeric
mode argument such as `101`). The shim replaces that path with a script, keeps the original as
`/mnt/app/boordr.stock` (a hard link) and:

- starts `/mnt/fat/koreader/koreader.sh` unless `/mnt/fat/koreader/.disabled` exists or KOReader is missing,
  otherwise `exec`s the stock reader with the original arguments (transparent);
- returns codes `ebrmain` understands (see below) when KOReader exits;
- runs "USB" / "ADB" modes on request of the plugin (unmounting the FAT first), and returns to KOReader when the cable is unplugged;
- disables KOReader after two failures in a row within 120 s each.

`ebrmain`'s supervisor logic (see [TECHNICAL-BINARY-MAP.md](TECHNICAL-BINARY-MAP.md)): a reader that dies by
signal or exits with 255 counts as a failure; three failures within 60 s go to a "code 11" path; a broken reader
does **not** bring `ebrmain` down, but the UI (and with it USB and ADB) is lost.

## 8. Hazards found

- `S20userfs.sh` **reformats** the FAT/update/priv partitions whose header is not recognized as FAT (data loss).
- A hanging script in `init.d` stops `ebrmain` from starting, and therefore USB and ADB. Any hook must run in the
  background, with a timeout, **after** `S42`.
- Rewriting busybox, `/lib/ld-linux`, libc, `inittab`, `rcS` or `S01..S42` breaks the microSD recovery route.
- `S33Store.sh` has an early `exit 0`: the code below never runs. Don't be misled when reading it.
- ADB accumulates zombie `[sh]` processes; a reboot cleans them.
- The stock reader caches decoded UI images in `system/thumbnail` on the user partition, and that cache wins over the
  source files (this is why changing a banner image has no visible effect until the cache is moved and the reader restarted).
