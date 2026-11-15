# my-keymap

`gen740/qmk_firmware` から切り出した Corne 用 keymap です。
対象は元の `compile.sh` と同じ **`crkbd/rev4_1/standard:gen740`（RP2040）** です。
薙刀式・Dvorak の実装、生成器、既存の回帰テストを移植しています。

## 書き込み

Nix の `nix-command` と `flakes` を有効にして、このディレクトリで実行します。
QMK CLI やクロスコンパイラを別途インストールする必要はありません。

```sh
nix run .#flash
```

ファームウェアをビルドした後、RP2040 の UF2 ボリュームを待ちます。
書き込む側を USB 接続し、リセットボタンのダブルタップなどで bootloader に入れてください。
コピーが終わったら、反対側も USB 接続して同じコマンドを実行します。
書き込みにはマウント済みのボリュームへの書き込み権限が必要です。
Linux ではファイルマネージャーなどで `RPI-RP2` をマウントしてください。

複数の RP2040 が接続されている場合や自動検出範囲外にマウントした場合は、明示できます。

```sh
nix run .#flash -- --mount /Volumes/RPI-RP2
```

自動検出は macOS の `/Volumes`、Linux の `/media`・`/run/media`・`/mnt` を対象にし、
`INFO_UF2.TXT` の Board-ID が `RPI-RP2` のボリュームへ書き込みます。
Corne 以外の RP2040 も同じ ID を使うため、書き込むキーボードだけを bootloader に入れてください。

## ビルドと編集

```sh
nix build          # result/crkbd_rev4_1_standard_gen740.uf2
nix flake check -L # ファームウェアのビルド検証
nix fmt           # Nix ファイルの整形
```

編集対象は `keyboards/crkbd/keymaps/gen740/` です。
`generator/` の定義から、ビルド時に Dvorak・薙刀式の `*_keydata.c/h` を再生成します。
生成とコンパイルは作業用ディレクトリ内で行われ、手元のファイルは変更しません。
元の `compile.sh` は Nix のコマンドに置き換えています。

既存の入力処理の回帰テスト（macOS、Xcode Command Line Tools が必要）:

```sh
python3 keyboards/crkbd/keymaps/gen740/tests/test_naginata.py -v
```

## QMK の更新

QMK 本体は公式 `qmk/qmk_firmware` の `master` を Nix input として参照し、
コミットと submodule を `flake.lock` に固定しています。
このリポジトリには QMK 本体や他のキーボードをコピーしません。
Nix は upstream ソースを取得しますが、ビルド用ツリーには core と `crkbd` の定義、
この keymap だけを配置します。keymap と upstream の履歴を merge する必要はありません。

```sh
nix flake update qmk
nix flake check -L
git add flake.lock
git commit -m "Update QMK firmware"
```

QMK の破壊的変更でビルドが失敗した場合は keymap を修正してから lock と一緒に commit します。
更新を取り消すには `git restore flake.lock` を実行してください。
Nixpkgs なども含めた更新は `nix flake update` です。
GitHub Actions でも Linux と macOS でビルドし、UF2 を artifact として保存します。

元の fork にあった RGB の `pixel_rain` 無効化だけを
`patches/disable-pixel-rain.patch` に分離しています。
QMK core への変更はありません。

## 移植元とライセンス

- 移植元: [gen740/qmk_firmware](https://github.com/gen740/qmk_firmware/tree/cac04fc46245029e689cde1cb198aad13114ebf5/keyboards/crkbd/keymaps/gen740)
- 元コミット: `cac04fc46245029e689cde1cb198aad13114ebf5`
- QMK: [qmk/qmk_firmware](https://github.com/qmk/qmk_firmware)
- [External QMK Userspace](https://docs.qmk.fm/newbs_external_userspace) に準じた keymap 配置と `qmk.json` を使用しています。
- 元のライセンスと各ファイルの著作権表示を維持しています。[LICENSE](LICENSE) を参照してください。
