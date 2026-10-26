# Building KOReader for the Lev

KOReader's `bookeen` target is **already in upstream** (koreader / koreader-base). This project did not
change the build; it only changes one Lua line and adds a small plugin on the device (see INSTALL.md).
Do **not** commit or redistribute the resulting binaries from this repository (AGPL: if you share a
build you must offer its source).

## What was used

| | |
|---|---|
| Build image | Docker `koreader/kobookeen:5.0.0-22.04` (cross compiler `arm-bookeen-linux-gnueabi`) |
| koreader | upstream `master` snapshot of 2026-10-24, version string `v0000.00-0-g400ba0e65c_2026-10-24_bookeen` |
| koreader-base | submodule at `33b43b5b21a2f2aa7a8b5ad53b6d83d3954f51c0` |
| Result | a `koreader-bookeen-*.zip` of about 39 MiB (md5 of the build used: `4754d5b1d540b13dcb75956a98d409ca`; yours will differ) |

Upstream lists "Saraiva Lev com luz (CYBOY4F-SA)" in `frontend/device/bookeen/device.lua`, so no
device-definition change was needed. An older, still-open upstream PR (#15920, Cybook Muse support) was
not required.

## Steps (Linux/macOS/Windows with Docker)

On Windows, keep the source **inside a Docker volume** (NTFS breaks the symbolic links used by the build)
and give WSL enough memory (about 6 GB; the default is often too low and the compiler gets killed).

```
docker volume create lev-ko
docker run --rm --user root -v lev-ko:/src koreader/kobookeen:5.0.0-22.04 chown ko:ko /src
docker run --rm -v lev-ko:/src -v "$PWD/out:/out" koreader/kobookeen:5.0.0-22.04 bash -lc '
  set -e; cd /src
  git clone --depth 1 https://github.com/koreader/koreader.git
  cd koreader && git submodule update --init --depth 1 base
  ./kodev fetch-thirdparty
  ./kodev build bookeen
  ./kodev release bookeen
  cp koreader-bookeen-*.zip /out/'
```

It takes a while (it downloads and compiles all third-party libraries). Check that the binaries are ARM:
`file koreader/luajit` should say ARM. The zip unpacks to a top-level `koreader/` folder.

To pin the exact versions used here, check out the koreader commit `400ba0e65c` and the base commit above
instead of the current `master`; newer snapshots may or may not behave the same on this device.

## Notes

- The zip's `luajit` and libraries are real files (FAT has no symlinks); unzip on the device with `unzip`
  (busybox) as in INSTALL.md.
- The one Lua change (INSTALL step 5) is in `frontend/device/bookeen/powerd.lua`: `setIntensityHW` calls
  `lev-frontlight.sh` instead of `/bin/frontlight`. If a newer KOReader changed that function, adapt it.
