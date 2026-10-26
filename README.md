# saraiva-lev-koreader

Run [KOReader](https://koreader.rocks/) on the **Saraiva "Lev com luz"** e-reader (Bookeen firmware,
Allwinner A13), keep the stock reader as a fallback, and get a dimmer minimum frontlight.
Everything here was done on one real device, with backups, over ADB, without opening the case.

> ## Read this first
> **This repository is published as-is, for information.** I am not a maintainer and do **not**
> plan to be one: no support, no updates, no answers to issues or pull requests (Issues and
> Discussions are turned off, and the repository may be archived). If you want to improve it,
> fork it.
>
> **You can brick your device.** There is no UART access in this project, the boot partitions are
> never touched on purpose, and the restore image in this repo has **never been tested on a device**
> (see [docs/RECOVERY.md](docs/RECOVERY.md)). You do everything at your own risk. The authors and
> contributors accept no responsibility for damaged devices, lost data or anything else. See the
> [MIT License](LICENSE).
>
> This is **not affiliated with, or endorsed by**, Saraiva, Bookeen or the KOReader project.

## What this is

The Saraiva Lev's store and sync services no longer exist, and its stock reader (Boo Reader 6.3)
cannot open CBZ files and has weak zoom. This project:

- builds KOReader's official `bookeen` target and runs it on the Lev;
- installs a tiny **shim** at `/mnt/app/boordr` so KOReader starts at boot, with the original
  reader kept untouched as `/mnt/app/boordr.stock`;
- adds an automatic **safety switch** (two quick KOReader failures disable it and start the stock
  reader) and a `.disabled` flag you can create over USB or from inside KOReader;
- adds a small KOReader **plugin** that gives you *USB mode*, *ADB* and *back to stock reader*
  from KOReader's menu (KOReader itself has no USB mass-storage mode on this device);
- lowers the minimum frontlight from the driver's 13.9% to about 8.3% by writing a single PWM
  register ([docs/FRONTLIGHT.md](docs/FRONTLIGHT.md));
- documents how the firmware works and a map of the stock binaries for build 2643
  ([docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md), [docs/TECHNICAL-BINARY-MAP.md](docs/TECHNICAL-BINARY-MAP.md)).

## Supported device (only this one)

| | |
|---|---|
| Device | Saraiva **Lev com luz** (serial characters 8-9 = `4F`, SKU `CYBOY4F-SA`) |
| Firmware | Boo Reader **6.3**, boot[7] rootfs[18], **build 2643**, Linux 3.0.8+ armv7l, 256 MB RAM, NAND |
| Not supported | Saraiva "Lev" without light (`4S`), Muse/Odyssey/Ocean, other builds. **Do not try.** |

The firmware is Saraiva-specific; public Bookeen firmwares (2326, 2350, 2536...) are **not** valid
for it. [`scripts/preflight.sh`](scripts/preflight.sh) checks all of this on your device, read-only,
and aborts if anything differs.

## Status: what was tested

Tested on one device (details and caveats in [docs/KNOWN-ISSUES.md](docs/KNOWN-ISSUES.md)):

| Feature | Status |
|---|---|
| KOReader draws on the e-ink panel, touch works | works |
| CBZ opening (manga), zoom modes, rotation to landscape | works (pinch zoom needs practice; touch in landscape looked right) |
| Centre button = Home in KOReader | works |
| Frontlight through KOReader, with the 8.3% minimum | works |
| Boot straight into KOReader, stock reader as fallback (`.disabled`) | works |
| USB mass storage from the KOReader menu (plugin) | works |
| Auto-sleep on battery | one real-world report: slept overnight and woke up, ~100% to ~90% including some reading. **Not a controlled measurement** |
| Plugin ADB mode, plugin "back to stock reader" | **not tested** |
| Wi-Fi in KOReader | **not tested** |
| Restore `CybUpdate.bin` from microSD | **never tested** |
| `scripts/preflight.sh` | **never run on a device** (syntax-checked only) |
| The shim and plugin **as published here** | They are translations of the files that were tested: same logic, but comments, function names and the mode file (`/tmp/lev-mode`) were renamed afterwards and **not re-tested on the device**. Run `sh -n` on the shim before installing it and test it with `.disabled` present (INSTALL step 7) |

## Documentation

1. [docs/INSTALL.md](docs/INSTALL.md): step by step, each step with its undo. Start here.
2. [docs/RECOVERY.md](docs/RECOVERY.md): what to do when something goes wrong, and what cannot be recovered.
3. [docs/KNOWN-ISSUES.md](docs/KNOWN-ISSUES.md): tested matrix, quirks, open problems.
4. [docs/BUILD-KOREADER.md](docs/BUILD-KOREADER.md): how the KOReader build was produced.
5. [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md), [docs/FRONTLIGHT.md](docs/FRONTLIGHT.md),
   [docs/TECHNICAL-BINARY-MAP.md](docs/TECHNICAL-BINARY-MAP.md): research notes.
6. [docs/LOG.md](docs/LOG.md): what was done to the device, in order.
7. [docs/CREDITS.md](docs/CREDITS.md): prior art this builds on.

## What is deliberately NOT in this repository

- Any Saraiva/Bookeen binary or image (`ebrmain`, `boordr`, `nand*.img`, `CybUpdate.bin`): you make
  your own backup. Only md5 checksums and addresses are published.
- A prebuilt KOReader (AGPL: a binary would need its source offered alongside). Build it
  ([docs/BUILD-KOREADER.md](docs/BUILD-KOREADER.md)) or use upstream artifacts.
- Anything personal (serial number, MAC, Wi-Fi, accounts). Never post those if you write about your own device.

## Using an AI assistant on this

If you work on this with an AI coding assistant, point it at [AGENTS.md](AGENTS.md) first: it holds the
hard safety rules (read-only first, confirm every write, never touch boot partitions, backup before
anything). It reduces the chance of a mistake; it does not replace your own judgement.

## License

Code: [MIT](LICENSE). Text and documentation: [CC BY 4.0](LICENSE-DOCS.md).
Built with the help of an AI assistant (Claude), under human direction and on real hardware.
