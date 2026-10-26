# Technical map of the stock binaries (build 2643)

**Only valid for the exact stock files below.** Addresses are virtual addresses of static ARM (ET_EXEC,
base 0x8000, no symbols). Nothing from the binaries is published here, only addresses and observations.
`[CONFIRMED]` = read in the disassembly, `[HYPOTHESIS]` = interpretation.

| File | md5 |
|---|---|
| `/mnt/app/boordr` (the reader, 39.6 MB) | `5a6dc8b3277d1b1c4e9eef1672e3c637` |
| `/mnt/app/ebrmain` (supervisor, 1.7 MB) | `2619e5599ad530affeb6b6714939dd9e` |

## Tools (read-only, on the PC)

Python with `capstone` and `pyelftools` (`pip install capstone pyelftools`):
- `tools/re/re-xref.py <bin> "<text>"`: where the code uses a string (literal-pool `ldr` and `movw/movt` pairs), with the surrounding function.
- `tools/re/re-addrxref.py <bin> <addr>`: references to a global address.
- `tools/re/re-callers.py <bin> <addr>`: callers of a function.
- `tools/re/re-disasm.py <bin> <addr> <n>`: annotated disassembly.

Method warning: hand-reading ARM is slow and imprecise; jump tables appear as fake instructions in a naive
disassembly. A decompiler (Ghidra) would be faster; none was needed for what was done here.

## ebrmain (the supervisor)

- Static, ARM. `_start` (0x80e0) calls `__libc_start_main` with `main` = **0xd610**, which builds an application
  object (constructor at 0x8c20) and calls the main loop **0xd530**. Global object at 0x1b74e0 (vtable pointer;
  virtual methods at +0x54, +0x60, +0x8c, +0x90, +0x94) and a state struct at 0x1b74c4 (+4 "cyio loaded" flag,
  +8 time of the first failure, +0xc failure counter).
- Loop 0xd530: the first time it runs `insmod /ebrmain/cyio.o`; then it calls **0xcc40** (launches the reader and
  waits) while the return value is non-zero; on exit `rmmod cyio`.
- **0xcc40 is the reader watchdog.** It picks `/ebrmain/boordr` or `/mnt/app/boordr` (strings 0x17265c / 0x17266c)
  depending on a configuration field (on this device `/ebrmain` does not exist), launches the process with a mode
  argument (strings `"53"`, `"101"`, `"102"`, `"52"`) and waits; status is read at `sp+0xbc`.
- If the reader dies by **signal** (status & 0x7f != 0) or exits with **255**, it counts as a failure (code 13; 255
  puts the counter at 3). The first failure time is stored; **three failures within 60 s** (0xea60 ms) take the
  "code 11" path (0xd474); otherwise it just relaunches. **A broken reader does NOT bring `ebrmain` down**; what is
  lost is the UI, and with it USB and ADB.
- Exit-code jump table (codes 10..104, at 0xcd80): {10,12} -> 0xd380 (becomes 14 except 11) -> 0xcfac;
  {11,14,103} -> 0xcfac; {13} -> 0xcf38 (failure count); {50,51,100,101} -> 0xcff4 (clean restart: zeroes the counter,
  reads the global object; 51 -> 0xf630; 50 and 101 -> 0xd410, which destroys the global object and **returns 0,
  ending the loop**; 100 relaunches with a flag); {102,104} -> 0xd2b0 (redraw/restart the interface);
  {15..99} -> 0xd080 (relaunch, return 1). The meaning of each code *for the reader* is interpretation.
- **Code 11 (0xd474)** [CONFIRMED in the disassembly]: sleeps 1 s, calls UI helpers 0x20870 (which fills the
  frame buffer, a blank/flash) and 0xa620, runs `rm /mnt/fat/system/.fonts.cache-1`, and jumps back. It does **not**
  start USB mass storage.
- Resource directory function (0x10260): builds `/mnt/fat/res` (0x172b7c) and keeps it only if both
  `access("/mnt/fat/boordr")` and `access("/mnt/fat/res")` succeed; otherwise `/mnt/app/res` (0x172b9c). So
  `/mnt/fat/boordr` (any file) is only a **developer flag that switches ebrmain's own resource directory**;
  there is no evidence that `ebrmain` executes a `boordr` from the FAT. (An earlier hypothesis of a reader override
  was refuted.)
- Small helpers: 0xd810 `adb(bool)` -> `/etc/init.d/adb.sh start|stop`; 0xd840 virtual call then `sync`; 0xd880
  `echo "" > <path in obj+0x164>`; 0xd8b0 `echo <value> > <path>` (sysfs writes).
- Strings of interest: `/etc/init.d/adb.sh`, `mass_storage.sh start|stop|stop_sd`, `/mnt/{sd,fat,ext1,ext2}/cybook_upgrade`,
  `/mnt/{sd,fat}/CybUpdate.bin`, `/mnt/sd/CybUpdate.lock`, `/private/.newupdate`, `nvram -u`, `/private/usbms`,
  `/sys/class/leds/frontlight/brightness` (a path that does not exist on this device: other models).

## boordr (the reader)

- C++ (boost, cairo, ICU, an embedded browser engine, SQLite). `.text` 33.8 MB at 0x80e0..0x203f000, `.rodata` at
  0x203f9f0, `.bss` 0x25abd30..0x263d854. Menu icons `bcMain{Home,Library,Shop,FrontLight,ContextualMenu}.svg`
  (also under `Gen6UI/`), stores `saraiva|bookeen|thalia|adlibris` selected by the SKU suffix, caches
  `system/library` and `system/thumbnail`.
- **Navigation bar drawing function: 0x166d40.** Loops over a global list and picks the icon with a `switch` on the
  item type. Item count at `*(0x25b3d88)`.
- **Global registry at 0x25b3d88:** `+0` count, `+4` mutex?, `+8` pointer to a vector of item pointers, `+0xc/+0x10` end/capacity.
  Static initializer 0x166190; referenced by 13 functions in 0x165f20..0x168100.
- **Bar widget constructors** (the same code compiled twice): **0x167990** and **0x167d80**. They read the list and,
  for every item, build a 0x1c-byte object, measuring the widest/tallest icon. Touch handling: 0x1661f0.
- **Item ids** (drawing switch at 0x167050): `0x4f` Home, `0x50` Library, `0x51` **Shop**, `0x52` Frontlight,
  `0x53`/`0x54` Menu. The item id is stored at `item+4`.
- **Default list builder:** when the list is empty (count 0) the constructors push `0x4f`, `0x50`, `0x51`
  unconditionally, `0x52` only if `widget+0xb4 != 0`, then `0x53` or `0x54` depending on the return value of 0x3e550(0x25abec0).
  The widths come from a division by 5 (magic 0x66666667 at 0x167350).
- The Home screen's "Shop" tile (third row) is a different widget and **was not located**. The banner is a JPEG
  (750x150, `.thx` extension) taken from `system/user/store/estore_*` on the user partition, else from the built-in
  `/mnt/app/res/img/estoresa.jpg`; decoded images are cached in `system/thumbnail`.

## Candidate patch (research only, NEVER applied)

Replacing, in each bar constructor, `mov r2,#0x51` (0xE3A02051) by a branch over the block that pushes the Shop
item: 0x167BEC -> 0x167C18 and 0x167FDC -> 0x168008 (8 bytes). See `experimental/patch-boordr-noshop.py`.
Open risk: code assuming fixed positions, and the divide-by-5 layout. Since the project moved to KOReader, this was
dropped.

## RAM and space (stock reader)

Of 151 MB, about 92 MB are free; `boordr` uses ~24 MB RSS, `ebrmain` ~0.1 MB. The rootfs (242 MB used, 86%):
boordr 38.8 MB, `res/dict` 29 MB, `res/dat` 25.7 MB (two ICU data files), `res/fonts` 19 MB, `/lib` 16.5 MB (the
Wi-Fi driver alone is 12 MB), `/usr` 14.7 MB, `/system` 13.5 MB (13 factory/update screens of 777 KB and waveforms).
