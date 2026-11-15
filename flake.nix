{
  description = "gen740's Corne keymap";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    # Include QMK's pinned libraries, so updating this input updates them together.
    qmk = {
      url = "git+https://github.com/qmk/qmk_firmware?ref=master&shallow=1&submodules=1";
      flake = false;
    };
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "aarch64-darwin"
        "x86_64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];
      imports = [ ./nix/keymap.nix ];
    };
}
