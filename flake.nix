{
  description = "Clipton - Clipboard Manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {self, nixpkgs}: let
    supportedSystems = [
      "x86_64-linux"
      "aarch64-linux"
    ];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
  in {
    packages = forAllSystems (system:
      let
        pkgs = import nixpkgs {inherit system;};

        # Read the manifest directly in Nix so we know the program name
        manifest = builtins.fromJSON (builtins.readFile ./manifest.json);
      in {
        default = pkgs.python3Packages.buildPythonApplication {
          pname = manifest.program;
          version = manifest.version;
          pyproject = true;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          build-system = [
            pkgs.python3Packages.setuptools
          ];

          src = ./.;

          # These are runtime dependencies the script calls via subprocess
          buildInputs = with pkgs; [
            wl-clipboard
            rofi
            libnotify
          ];

          preBuild = ''
            export FAKE_HOME=$(mktemp -d)
            export HOME=$FAKE_HOME
            sed -i '/subprocess\.run(.*systemctl.*/d' setup.py
          '';

          postInstall = ''
            mkdir -p $out/lib/systemd/user
            cp $FAKE_HOME/.config/systemd/user/${manifest.program}.service $out/lib/systemd/user/

            # Fix the ExecStart path
            sed -i "s|$FAKE_HOME/.local/bin/|$out/bin/|g" $out/lib/systemd/user/${manifest.program}.service

            # Instead of hardcoding wayland-1, we tell systemd to wait for the session
            # environment to be imported. This is much more stable on NixOS.
            sed -i '/\[Service\]/a Environment=PYTHONUNBUFFERED=1' $out/lib/systemd/user/${manifest.program}.service

            # We add this to ensure the service restarts if the compositor isn't ready yet
            sed -i '/\[Service\]/a RestartSec=3' $out/lib/systemd/user/${manifest.program}.service
          '';

          postFixup = ''
            # This ensures clipton always finds its tools without needing them in your global PATH
            wrapProgram $out/bin/${manifest.program} \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.wl-clipboard pkgs.rofi pkgs.libnotify ]}
          '';
        };
      });

    devShells = forAllSystems (system:
      let
        pkgs = import nixpkgs {inherit system;};
      in {
        default = pkgs.mkShell {
          packages = [
            pkgs.python3
            pkgs.python3Packages.pip
            pkgs.python3Packages.virtualenv
          ];
        };
      });
  };
}