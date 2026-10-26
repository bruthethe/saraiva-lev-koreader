# Frontlight on the Lev, and the minimum-light tweak

[CONFIRMED] unless noted.

## Hardware

- `/bin/frontlight N` (N = 0 brightest, 255 off) issues ioctl `0x142` on `/dev/disp` (a get ioctl `0x143` exists).
- The light is the A13's **PWM0**: FEX settings `lcd_pwm_ch=0`, `lcd_pwm_freq=1000`, `lcd_pwm_pol=0`. Registers:
  control `0x01C20E00` (0x7F), period/active `0x01C20E04` = `(period << 16) | active`, **period = 23999** (1 kHz).
- Light fraction = `(period - active) / period`. Define `remaining = 23999 - active`.
- Level 255 turns the light off by another mechanism: the register does not change.
- The driver's table (kernel, not in `SCRIPT.BIN`) maps the steps to `remaining` values. Measured:

| step | remaining | | step | remaining |
|---|---|---|---|---|
| 254 | 3335 (13.9%) | | 112 | 5663 |
| 240 | 3479 | | 96 | 7007 |
| 224 | 3647 | | 80 | 7679 |
| 208 | 3791 | | 64 | 8327 |
| 192 | 3959 | | 48 | 9239 |
| 176 | 4343 | | 32 | 10223 |
| 160 | 4679 | | 16 | 11231 |
| 144 | 4991 | | 0 | 12215 (50.9%) |
| 128 | 5327 | | | |

The driver therefore never goes below 13.9%, which can hurt in the dark.

## Writing the register directly

`devmem 0x01c20e04 32 <value>` works; the light gets dimmer than the stock floor. **The LED turns off** when
`active` is above roughly 22500 (`remaining` under ~2200). The target used here is `remaining = 2000` (about 8.3%).

## The tweak (`scripts/luz-minima.sh`, `scripts/lev-frontlight.sh`)

It compresses the range between step 254 (3335) and step 128 (5327) onto 2000..5327; above step 128 nothing changes.
It only writes when the period reads 23999 and the value is inside that range.

- `luz-minima.sh` (boot daemon, for the stock reader): three `dd` watchers block on `/dev/input/event0|1|2`; an event
  triggers a 1 s burst of checks every 20 ms; a 3 s loop is the safety net; ~0.4% CPU idle (a 100 ms polling
  version took 6.8%). Because the stock driver writes first and the script corrects after, a faint flash of the stock
  level can be seen right when the light turns on.
- `lev-frontlight.sh` (for KOReader): KOReader calls it instead of `/bin/frontlight`; it runs the stock tool and then
  applies the same correction immediately, so the flash is almost imperceptible.
- Notes: `usleep` exists on the device (`sleep` only takes integers); there is no `timeout`, `inotifyd` or `taskset`;
  background processes started from an `adb shell` die with the session (the boot hook does not have that problem).
- Disable: `luz_off.txt` in the user partition root (the daemon exits and the KOReader script skips the correction).
- Limit: to remove the brief flash completely one would patch the kernel's table (boot partition, **not** done).
