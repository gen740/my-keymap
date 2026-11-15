{
  lib,
  stdenv,
  qmk,
  gcc-arm-embedded,
  python3,
  qmkSource,
}:
stdenv.mkDerivation {
  pname = "crkbd-gen740";
  version = "1.0";

  # Copy only the build system, core, libraries and Corne definition. No other
  # keyboards or upstream keymaps are part of the build tree or this repository.
  dontUnpack = true;
  nativeBuildInputs = [
    qmk
    gcc-arm-embedded
    (python3.withPackages (ps: [ ps.toml ]))
  ];
  configurePhase = ''
    runHook preConfigure
    mkdir source
    cd source
    cp -R ${qmkSource}/{Makefile,paths.mk,builddefs,data,drivers,lib,platforms,quantum,tmk_core,util} .
    # QMK CLI uses these files to recognize a firmware source tree.
    cp ${qmkSource}/requirements{,-dev}.txt .
    mkdir -p keyboards/crkbd
    cp -R ${qmkSource}/keyboards/crkbd/. keyboards/crkbd/
    # QMK validates the community layouts advertised by the Corne definition.
    mkdir -p layouts/default/{split_3x5_3,split_3x6_3}
    for layout in split_3x5_3 split_3x6_3; do
      cp ${qmkSource}/layouts/default/"$layout"/*.json layouts/default/"$layout"/
    done
    chmod -R u+w .
    rm -rf keyboards/crkbd/keymaps
    mkdir -p keyboards/crkbd/keymaps
    cp -R ${../keyboards/crkbd/keymaps/gen740} keyboards/crkbd/keymaps/gen740
    chmod -R u+w keyboards/crkbd/keymaps/gen740
    patch -p1 < ${../patches/disable-pixel-rain.patch}
    # Make invokes uf2conv.py directly; /usr/bin/env is absent in Nix sandboxes.
    patchShebangs util
    export HOME="$TMPDIR/home"
    mkdir -p "$HOME"
    export QMK_HOME="$PWD"
    # Keep user-wide QMK configuration and external overlays out of the build.
    unset QMK_USERSPACE ORIG_CWD
    runHook postConfigure
  '';
  buildPhase = ''
    runHook preBuild
    (
      cd keyboards/crkbd/keymaps/gen740
      python3 generator/code_generator.py dvorak
      python3 generator/code_generator.py naginata
    )
    make crkbd/rev4_1/standard:gen740 SKIP_GIT=yes SKIP_VERSION=yes -j"$NIX_BUILD_CORES"
    runHook postBuild
  '';
  installPhase = ''
    runHook preInstall
    mkdir -p "$out"
    cp crkbd_rev4_1_standard_gen740.uf2 "$out/"
    runHook postInstall
  '';
  dontFixup = true;
  meta = {
    description = "gen740 keymap for Corne rev4.1 standard (RP2040)";
    license = lib.licenses.gpl2Plus;
    platforms = lib.platforms.unix;
  };
}
