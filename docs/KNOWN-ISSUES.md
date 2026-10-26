# Known issues and test status

Everything below comes from **one device**, tested by one person. "Works" means "I saw it work
on that device", not "guaranteed".

## Test matrix

| Area | Result | Notes |
|---|---|---|
| KOReader on the panel (758x1024 portrait) | works | Detected as generic "Bookeen". First start opens the quick-start document. |
| Touch | works | gt80x touchscreen on `event2`. |
| CBZ / manga | works | Opens in ~0.5-1 s (3-4 MB chapter). Pinch zoom needs practice; zoom modes (page, width, content, rows, manual) all switch. |
| Rotation to landscape | works | Image rotates (software). Taps/scroll looked right in landscape; not stress-tested. A gesture can be bound to "toggle rotation". |
| Centre hardware button | works | Key code 139, which KOReader maps to "Home". |
| Power button, short press | works | Screensaver and sleep; short press again wakes. |
| Sleep on battery | anecdotal | The device was left reading with the light at minimum, fell asleep, and the next morning it had auto-slept; battery went from 100% to ~90% including ~10 minutes of reading. Unknown hours, not a controlled measurement. With the USB cable connected the device never enters deep sleep (the uptime counter keeps running). |
| Frontlight | works | Through KOReader's own menu. Minimum is ~8.3% with the tweak. A very brief flash toward the stock level can still be glimpsed right when the light turns on. |
| Boot into KOReader through the shim | works | The boot is a little slower than the stock reader. |
| Safety switch / `.disabled` | works | `.disabled` made by renaming a file from inside KOReader was used to return to the stock reader. The *automatic* trigger (two quick failures) was never triggered in practice. |
| USB mass storage from the plugin | works | PC sees the drive; KOReader returns after unplugging. Eject from the PC before unplugging. |
| Plugin: Enable ADB | **not tested** | The code path mirrors the stock `adb.sh`. |
| Plugin: Back to the stock reader | **not tested** | |
| KOReader menu "Exit" | **not observed** | The shim returns code 101, which per KOReader's own installer means "power off". |
| Wi-Fi in KOReader | **not tested** | KOReader's Bookeen port has Wi-Fi scripts; the Lev's 8188eu module was not exercised. |
| microSD restore image | **never tested** | See RECOVERY.md. |
| `scripts/preflight.sh` | **never run on a device** | Syntax-checked only. Its md5 constants come from the author's own stock files. |
| Published shim/plugin text | **not re-tested as published** | Translated copies of the tested files (same logic; names and the mode file renamed). |

## Known problems

- **No USB while KOReader runs.** The stock reader is what enables USB mass storage and ADB; KOReader's
  Bookeen port has no such mode. Plug in the cable and the PC sees nothing. Use the plugin's USB mode.
  Exit code 11 does not seem to expose the USB: the `ebrmain` handler for it (around 0xd474 in build 2643)
  only waits, blanks the screen, deletes the font cache and relaunches the reader. This contradicts a
  comment in KOReader's installer; the author read the handler but did not trace every path.
- **One unexplained touch freeze.** Right after a restart of the stock reader (`killall boordr`, used as a
  quick test), the touch stopped responding once and the device had to be force-rebooted. The cause was
  not determined; it may be the stock reader's known freeze, or not related. It did not happen again
  after a clean boot.
- **Stock features do not migrate:** the stock reader's dictionaries, the Adobe DRM (ADE) activation and
  the library database stay with the stock reader. KOReader does not read Adobe-DRM books.
- **The stock "Shop" tile/items** are untouched (they remain in the stock reader, which is only used as
  a fallback now). A binary patch to hide them exists as research only ([`experimental/`](../experimental)).
- **KOReader version.** The build used here is an upstream snapshot (see BUILD-KOREADER.md). The upstream
  Bookeen port's authors noted its installer and first boot had not been tested on hardware; this project
  supplies its own shim instead of upstream's `cybook_upgrade` installer.
- **RAM is tight** (256 MB total; roughly 6-22 MB stayed free while KOReader ran, plus some page cache).
  Very large documents may fail.
- **The light tweak writes a hardware register directly.** It only acts when the PWM period reads 23999
  and the value is inside a measured range; below an "active" count of ~22500 the LED turns off.
  Do not use other values.

## Things nobody found out

- What `nandb`'s environment keys for recovery/fastboot correspond to on the hardware (no known button).
- Whether the boot loader has a rescue route beyond the rootfs updater.
- Why the touch froze that once.
