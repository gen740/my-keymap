# my-keymap

A Corne keymap extracted from `gen740/qmk_firmware`.
The build target is **`crkbd/rev4_1/standard:gen740` (RP2040)**, matching the original `compile.sh`.
This repository contains the Naginata and Dvorak implementations, code generators, and existing regression tests.

## Flashing

Enable Nix's `nix-command` and `flakes` features, then run the following from this directory.
Nix provides the QMK CLI and cross compiler; no separate installation is required.

```sh
nix run .#flash
```

The command builds the firmware and waits for an RP2040 UF2 volume.
Connect one half over USB and enter the bootloader, for example by double-tapping the reset button.
Once the copy finishes, connect the other half over USB and run the command again.
You need write access to the mounted volume.
On Linux, mount `RPI-RP2` using your file manager or another mounting tool.

If multiple RP2040 volumes are connected, or the volume is mounted outside the automatic search paths,
specify its mount point:

```sh
nix run .#flash -- --mount /Volumes/RPI-RP2
```

Automatic detection searches `/Volumes` on macOS and `/media`, `/run/media`, and `/mnt` on Linux.
It selects volumes whose `INFO_UF2.TXT` contains the Board-ID `RPI-RP2`.
Other RP2040 boards share this ID, so only put the keyboard you intend to flash into bootloader mode.

## Building and editing

```sh
nix build          # result/crkbd_rev4_1_standard_gen740.uf2
nix flake check -L # Build the firmware and run checks
nix fmt           # Format Nix files
```

Edit the files in `keyboards/crkbd/keymaps/gen740/`.
Each build regenerates the Dvorak and Naginata `*_keydata.c/h` files from the definitions in `generator/`.
Generation and compilation run in a temporary build directory without modifying your working tree.
The Nix commands replace the original `compile.sh`.

Run the existing input-processing regression tests on macOS with Xcode Command Line Tools installed:

```sh
python3 keyboards/crkbd/keymaps/gen740/tests/test_naginata.py -v
```

## Updating QMK

QMK is a Nix input tracking the official `qmk/qmk_firmware` repository's `master` branch.
Its commit and submodules are pinned in `flake.lock`.
QMK itself and other keyboards are not vendored in this repository.
Nix fetches the upstream source and constructs a build tree containing the core, the `crkbd` definitions,
the required layout metadata, and this keymap. There is no need to merge upstream history into the keymap repository.

```sh
nix flake update qmk
nix flake check -L
git add flake.lock
git commit -m "Update QMK firmware"
```

If a QMK breaking change causes the build to fail, update the keymap and commit the changes with the lock file.
To discard an uncommitted lock file update, run `git restore flake.lock`.
Use `nix flake update` to update all inputs, including Nixpkgs.
GitHub Actions builds the firmware on Linux and macOS and uploads the UF2 files as artifacts.

The original fork's change to disable the `pixel_rain` RGB effect is preserved in
`patches/disable-pixel-rain.patch`. There are no changes to the QMK core.

## Source and license

- Source: [gen740/qmk_firmware](https://github.com/gen740/qmk_firmware/tree/cac04fc46245029e689cde1cb198aad13114ebf5/keyboards/crkbd/keymaps/gen740)
- Source commit: `cac04fc46245029e689cde1cb198aad13114ebf5`
- QMK: [qmk/qmk_firmware](https://github.com/qmk/qmk_firmware)
- The keymap directory structure and `qmk.json` follow the [External QMK Userspace](https://docs.qmk.fm/newbs_external_userspace) conventions.
- The original license and per-file copyright notices are preserved. See [LICENSE](LICENSE).
