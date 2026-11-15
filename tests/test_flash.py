import contextlib
import importlib.util
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "flash", Path(__file__).resolve().parents[1] / "tools/flash.py"
)
flash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flash)


class FlashTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.volume = self.root / "RPI-RP2"
        self.volume.mkdir()
        (self.volume / "INFO_UF2.TXT").write_text("Board-ID: RPI-RP2\r\n")
        self.firmware = self.root / "firmware.uf2"
        self.write_uf2(0xE48BFF56)

    def write_uf2(self, family):
        block = bytearray(512)
        struct.pack_into("<8I", block, 0, 0x0A324655, 0x9E5D5157,
                         0x2000, 0x10000000, 256, 0, 1, family)
        struct.pack_into("<I", block, 508, 0x0AB16F30)
        self.firmware.write_bytes(block)

    def run_flash(self, *arguments):
        with patch.object(sys, "argv", ["flash", "--firmware", str(self.firmware), *arguments]):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                flash.main()

    def test_copy_to_selected_bootloader(self):
        self.run_flash("--mount", str(self.volume))
        self.assertEqual((self.volume / "NEW.UF2").read_bytes(), self.firmware.read_bytes())

    def test_reject_other_firmware_family(self):
        self.write_uf2(0xADA52840)
        with self.assertRaises(SystemExit) as error:
            self.run_flash("--mount", str(self.volume))
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.volume / "NEW.UF2").exists())

    def test_reject_multiple_bootloaders(self):
        with patch.object(flash, "find_volumes", return_value=[self.volume, self.root / "another"]):
            with self.assertRaises(SystemExit) as error:
                self.run_flash()
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.volume / "NEW.UF2").exists())

    def test_wait_until_bootloader_appears(self):
        with patch.object(flash, "find_volumes", side_effect=[[], [self.volume]]):
            with patch.object(flash.time, "sleep"):
                self.run_flash()
        self.assertEqual((self.volume / "NEW.UF2").read_bytes(), self.firmware.read_bytes())

    def test_filter_other_board(self):
        (self.volume / "INFO_UF2.TXT").write_text("Board-ID: another-board\n")
        self.assertFalse(flash.is_rp2040_volume(self.volume))
        self.assertFalse(flash.is_rp2040_volume(self.root / "missing"))


if __name__ == "__main__":
    unittest.main()
