{
  description = "Clipton - Clipboard Manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {self, nixpkgs}: let
    supportedSystems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgsFor = system: import nixpkgs {inherit system;};
  in {
    packages = forAllSystems (system: let
      pkgs = pkgsFor system;
      # Read the manifest directly in Nix to avoid hardcoding version/name
      manifest = builtins.fromJSON (builtins.readFile ./manifest.json);
    in {
      default = pkgs.python3Packages.buildPythonApplication {
        pname = manifest.program;
        version = manifest.version;

        src = ./.;

        # 1. Patch out the sandbox-violating post-install step before building
        postPatch = ''
          sed -i 's/_post_install()//g' setup.py
        '';

        # 2. Recreate the systemd service file the "Nix Way" inside the package output
        postInstall = ''
          mkdir -p $out/lib/systemd/user
          cat > $out/lib/systemd/user/${manifest.program}.service <<EOF
          [Unit]
          Description=Daemon for ${manifest.title} (Clipboard Manager)

          [Service]
          Type=simple
          ExecStart=$out/bin/${manifest.program} watcher

          [Install]
          WantedBy=graphical.target
          EOF
        '';

        propagatedBuildInputs = with pkgs.python3Packages; [
          setuptools
          # Add any other Python dependencies (like pyperclip, dbus-python) here
        ];
      };
    });

    devShells = forAllSystems (system: let
      pkgs = pkgsFor system;
    in {
      default = pkgs.mkShell {
        packages = with pkgs; [
          python3
        ];
      };
    });
  };
}