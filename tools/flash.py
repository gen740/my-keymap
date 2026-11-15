#!/usr/bin/env python3
"""Copy the built firmware to one RP2040 UF2 bootloader volume."""

import argparse
import os
from pathlib import Path
import shutil
import struct
import sys
import time


def is_rp2040_volume(path):
    try:
        return any(
            line.strip() == "Board-ID: RPI-RP2"
            for line in (path / "INFO_UF2.TXT").read_text().splitlines()
        )
    except (OSError, UnicodeError):
        return False


def find_volumes():
    roots = [Path("/Volumes")] if sys.platform == "darwin" else [
        Path("/media"), Path("/mnt"), Path("/run/media")
    ]
    candidates = set()
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for child in root.iterdir():
                candidates.add(child)
                # Linux automounters commonly use /media/<user>/<label>.
                if child.is_dir():
                    candidates.update(child.iterdir())
        except OSError:
            continue
    return sorted(path for path in candidates if is_rp2040_volume(path))


def main():
    parser = argparse.ArgumentParser(
        description="Flash crkbd/rev4_1/standard:gen740 (RP2040). "
        "Reset one half into its UF2 bootloader, then repeat for the other half."
    )
    parser.add_argument("--firmware", required=True, type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--mount", type=Path, help="RP2040 bootloader mount point")
    args = parser.parse_args()

    # Check the format and RP2040 family before copying anything.
    firmware = args.firmware.read_bytes()
    if len(firmware) == 0 or len(firmware) % 512:
        parser.error("invalid UF2 file size")
    for offset in range(0, len(firmware), 512):
        header = struct.unpack_from("<8I", firmware, offset)
        if (header[:2] != (0x0A324655, 0x9E5D5157)
                or not header[2] & 0x2000 or header[7] != 0xE48BFF56
                or struct.unpack_from("<I", firmware, offset + 508)[0] != 0x0AB16F30):
            parser.error("firmware must be an RP2040 UF2")

    print("Waiting for an RP2040 UF2 volume; reset the connected half (Ctrl-C to cancel).", flush=True)
    while True:
        if args.mount:
            volumes = [args.mount] if is_rp2040_volume(args.mount) else []
        else:
            volumes = find_volumes()
        if len(volumes) > 1:
            parser.error("multiple RP2040 volumes found; select one with --mount: "
                         + ", ".join(map(str, volumes)))
        if volumes:
            break
        time.sleep(0.25)

    destination = volumes[0] / "NEW.UF2"
    print(f"Flashing {volumes[0]}", flush=True)
    with args.firmware.open("rb") as source, destination.open("wb") as output:
        shutil.copyfileobj(source, output)
        output.flush()
        os.fsync(output.fileno())
    print("UF2 copied. Repeat with the other half connected by USB.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except OSError as error:
        sys.exit(str(error))
