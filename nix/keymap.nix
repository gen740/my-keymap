{ inputs, ... }:
{
  perSystem =
    { pkgs, config, ... }:
    {
      packages.firmware = pkgs.callPackage ./firmware.nix {
        qmkSource = inputs.qmk;
      };
      packages.default = config.packages.firmware;

      packages.flash = pkgs.writeShellApplication {
        name = "flash";
        runtimeInputs = [ pkgs.python3 ];
        text = ''
          exec python3 ${../tools/flash.py} \
            --firmware ${config.packages.firmware}/crkbd_rev4_1_standard_gen740.uf2 "$@"
        '';
      };
      apps.flash = {
        type = "app";
        program = "${config.packages.flash}/bin/flash";
      };
      apps.default = config.apps.flash;

      checks.firmware = config.packages.firmware;
      checks.flash = pkgs.runCommand "flash-tests" { nativeBuildInputs = [ pkgs.python3 ]; } ''
        cp -R ${../tools} tools
        cp -R ${../tests} tests
        python3 tests/test_flash.py -v
        touch "$out"
      '';
      devShells.default = pkgs.mkShell {
        packages = [
          pkgs.qmk
          pkgs.gcc-arm-embedded
          (pkgs.python3.withPackages (ps: [ ps.toml ]))
        ];
      };
      formatter = pkgs.nixfmt;
    };
}
