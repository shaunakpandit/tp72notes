{
  description = "Transcribe TP-7 voice notes into daily markdown notes";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      tp72notes = pkgs.python3Packages.buildPythonApplication {
        pname = "tp72notes";
        version = "0.1.0";
        pyproject = true;
        src = ./.;
        build-system = [ pkgs.python3Packages.setuptools ];
        dependencies = [ pkgs.python3Packages.faster-whisper ];
        nativeCheckInputs = [ pkgs.python3Packages.unittestCheckHook ];
      };
    in
    {
      packages.${system}.default = tp72notes;

      devShells.${system}.default = pkgs.mkShell {
        packages = [ (pkgs.python3.withPackages (python: [ python.faster-whisper ])) ];
      };

      nixosModules.default = import ./nix/module.nix self;
    };
}
