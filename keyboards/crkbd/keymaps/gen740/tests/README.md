# gen740 consumed-held-key regressions

Run from the repository root:

```sh
python3 keyboards/crkbd/keymaps/gen740/tests/test_naginata.py -v
```

The runner invokes an existing compiler by absolute path (`/usr/bin/clang` by
default; override with `--cc /absolute/path/to/cc`). It uses only Python standard
libraries, writes all build artifacts under `/tmp/gen740-dotou-fix/host`, and
compiles the real `naginata.c` and unchanged `naginata_keydata.c` together with
host-only QMK I/O stubs. Warnings are errors; AddressSanitizer and
UndefinedBehaviorSanitizer are enabled. No QMK installation is needed.

Each sequence starts in a fresh process and has balanced physical key events.
`+` means press and `-` means release. Checks include emitted key identities and,
where important, the exact output at each event. These are actual C runtime
checks, not a transcribed runtime model. Stub keycodes preserve symbolic
identity and shifted-key distinction but are not real USB HID values.

Coverage includes the `J+ D+ J- L+ D- L-` repro and release/order variants,
press rollback, sequential and rolling syllables, repeated voiced kana with
held J, incomplete prefixes, continuous reuse of consumed chord prefixes,
yoon, and pre/post thumb-shift kana. Existing fresh-only incomplete-prefix
behavior is intentionally pinned rather than redesigned.

An optional `--runtime /tmp/gen740-dotou-fix/naginata.before.c` builds a saved
original runtime with the same harness for regression-sensitivity checks.
This suite is not a firmware build or a keyboard/USB/IME test; firmware size,
physical typing behavior, and actual IME interpretation still need validation.
