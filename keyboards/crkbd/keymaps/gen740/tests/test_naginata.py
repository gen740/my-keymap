#!/usr/bin/env python3
"""Compile and exercise the actual gen740 runtime and generated trie (no QMK).

Only Python standard libraries and an existing absolute-path C compiler are used.
All compilation artifacts go under /tmp/gen740-dotou-fix.
"""
import argparse
import itertools
import os
from pathlib import Path
import re
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
KEYMAP = HERE.parent
SCRATCH = Path('/tmp/gen740-dotou-fix/host')


def build(compiler, runtime):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    source = (KEYMAP / 'naginata_keydata.c').read_text()
    names = sorted(set(re.findall(r'\bKC_\w+', source)) | {'KC_LNG1', 'KC_LNG2'})
    codes = {name: i + 1 for i, name in enumerate(names)}
    # These symbolic values need not be USB HID codes: runtime comparisons and
    # emitted identities stay consistent. S() retains a distinct shift bit.
    codes['KC_LNG1'] = codes['KC_LANGUAGE_1']
    codes['KC_LNG2'] = codes['KC_LANGUAGE_2']
    stub = '''#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define SAFE_RANGE 0x6000
#define S(k) ((k) | 0x100)
typedef struct { struct { bool pressed; } event; } keyrecord_t;
void tap_code16(uint16_t key);
void tap_code(uint8_t key);
void layer_move(uint8_t layer);
'''
    stub += ''.join(f'#define {name} {code}\n' for name, code in codes.items())
    (SCRATCH / 'qmk_stub.h').write_text(stub)
    binary = SCRATCH / 'naginata_host'
    command = [compiler, '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-g', '-O1',
               '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
               '-DQMK_KEYBOARD_H="qmk_stub.h"',
               f'-DNG_RUNTIME_SOURCE="{runtime}"',
               '-I', str(SCRATCH), '-I', str(KEYMAP),
               str(HERE / 'host.c'), '-o', str(binary)]
    result = subprocess.run(command, capture_output=True, text=True)
    (SCRATCH / 'build.log').write_text(' '.join(command) + '\n' + result.stdout + result.stderr)
    result.check_returncode()
    return binary, codes


class NaginataTests(unittest.TestCase):
    def run_sequence(self, sequence, expected, event_outputs=None):
        tokens = sequence.split()
        # Catch accidental malformed physical sequences in the regression data.
        held = set()
        for token in tokens:
            key, down = token[:-1], token[-1] == '+'
            self.assertEqual(key not in held, down, token)
            if down:
                held.add(key)
            else:
                held.remove(key)
        self.assertFalse(held, sequence)
        result = subprocess.run([str(BINARY), *tokens], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '', result.stderr)
        rows = [[int(k) for k in line.split()] for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), len(tokens))
        want = [CODES['KC_' + char.upper()] for char in expected]
        self.assertEqual([k for row in rows for k in row], want, sequence)
        if event_outputs is not None:
            self.assertEqual(rows, [[CODES['KC_' + c.upper()] for c in word]
                                    for word in event_outputs], sequence)

    def test_exact_repro_and_final_release_orders(self):
        for presses in ('J+ D+', 'D+ J+'):
            for first, held in (('J', 'D'), ('D', 'J')):
                for releases in (f'{held}- L-', f'L- {held}-'):
                    with self.subTest(presses=presses, first=first, releases=releases):
                        seq = f'{presses} {first}- L+ {releases}'
                        # Keep do on the first release; u on L release.
                        rows = ['', '', 'do', '', '', 'u'] if releases.startswith(held) else [
                            '', '', 'do', '', 'u', '']
                        self.run_sequence(seq, 'dou', rows)
        self.run_sequence('J+ D+ J- L+ L- L+ L- D-', 'douu',
                          ['', '', 'do', '', 'u', '', 'u', ''])

    def test_chord_release_before_next_press(self):
        for presses in ('J+ D+', 'D+ J+'):
            for releases in ('J- D-', 'D- J-'):
                with self.subTest(presses=presses, releases=releases):
                    self.run_sequence(f'{presses} {releases} L+ L-', 'dou',
                                      ['', '', 'do', '', '', 'u'])

    def test_consumed_press_rollback(self):
        for presses in ('J+ D+', 'D+ J+'):
            for releases in ('D- W-', 'W- D-'):
                with self.subTest(presses=presses, releases=releases):
                    self.run_sequence(f'{presses} J- W+ {releases}', 'doki',
                                      ['', '', 'do', '',
                                       'ki' if releases == 'W- D-' else '',
                                       '' if releases == 'W- D-' else 'ki'])

    def test_plain_sequential_and_rolling(self):
        self.run_sequence('D+ D- L+ L- W+ W-', 'touki')
        self.run_sequence('D+ L+ D- L-', 'tou', ['', '', 'to', 'u'])
        # Unfinished fresh-only prefixes retain their preexisting behavior.
        self.run_sequence('D+ L+ L- D-', 'to', ['', '', '', 'to'])
        self.run_sequence('J+ I+ I- J-', 'a', ['', '', '', 'a'])
        self.run_sequence('D+ W+ D- W-', 'toki', ['', 'to', '', 'ki'])
        self.run_sequence('W+ L+ W- L-', 'kiu')
        self.run_sequence('D+ D- D+ D-', 'toto')

    def test_repeated_voiced_with_held_j(self):
        self.run_sequence('J+ D+ D- D+ D- W+ W- S+ S- J-', 'dodogige',
                          ['', '', 'do', '', 'do', '', 'gi', '', 'ge', ''])
        # J can become fresh again after release while D remains consumed/held.
        self.run_sequence('J+ D+ J- J+ J- D-', 'dodo')

    def test_continuous_consumed_prefix_with_new_children(self):
        # A complete J,D,L chord must still mean doxu, not be split into do,u.
        for presses in ('J+ D+ L+', 'D+ J+ L+'):
            for tail in itertools.permutations(('J-', 'D-', 'L-')):
                with self.subTest(presses=presses, tail=tail):
                    self.run_sequence(presses + ' ' + ' '.join(tail), 'doxu')
        # D remains a valid chord prefix for toxu even after producing do.
        for tail in itertools.permutations(('D-', 'L-', 'M-')):
            with self.subTest(tail=tail):
                self.run_sequence('J+ D+ J- L+ M+ ' + ' '.join(tail), 'dotoxu')

    def test_yoon_and_continuous_yoon(self):
        for tail in itertools.permutations(('J-', 'W-', 'H-')):
            with self.subTest(tail=tail):
                self.run_sequence('J+ W+ H+ ' + ' '.join(tail), 'gya')
        self.run_sequence('W+ H+ H- H+ H- W-', 'kyakya')
        # Preserve release-boundary/pressed-order behavior, not v18 buffering.
        self.run_sequence('J+ W+ J- H+ H- W-', 'gikya')

    def test_shifted_kana(self):
        for shift in ('LSFT2', 'RSFT2'):
            for presses in (f'{shift}+ E+', f'E+ {shift}+'):
                for releases in (f'E- {shift}-', f'{shift}- E-'):
                    with self.subTest(presses=presses, releases=releases):
                        self.run_sequence(f'{presses} {releases}', 'ri',
                                          ['', '', 'ri', ''])
            self.run_sequence(f'{shift}+ E+ E- W+ W- {shift}-', 'rinu')
        # Continuous letter-shift behavior is not limited to J or thumb shift.
        self.run_sequence('Q+ J+ J- K+ K- Q-', 'xaxi')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc', default='/usr/bin/clang')
    parser.add_argument('--runtime', type=Path, default=KEYMAP / 'naginata.c',
                        help='Optional scratch baseline runtime for sensitivity checks')
    args, remaining = parser.parse_known_args()
    if not os.path.isabs(args.cc):
        parser.error('--cc must be an absolute path')
    BINARY, CODES = build(args.cc, args.runtime.resolve())
    unittest.main(argv=[__file__, *remaining])
