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

          # Tell Nix to use the modern build system for setup.py
          pyproject = true;
          build-system = [
            pkgs.python3Packages.setuptools
          ];

          src = ./.;

          propagatedBuildInputs = with pkgs.python3Packages; [
            # Add any python dependencies your app needs here
          ];

          preBuild = ''
            export FAKE_HOME=$(mktemp -d)
            export HOME=$FAKE_HOME

            # Strip the systemctl command from setup.py so it doesn't crash the isolated sandbox
            sed -i '/subprocess\.run(.*systemctl.*/d' setup.py
          '';

          # Intercept the generated file before the sandbox is destroyed
          postInstall = ''
            # 1. Create the systemd user directory in the Nix store
            mkdir -p $out/lib/systemd/user

            # 2. Copy the service file that setup.py generated in our fake home
            cp $FAKE_HOME/.config/systemd/user/${manifest.program}.service $out/lib/systemd/user/

            # 3. Fix the broken ExecStart path.
            # setup.py wrote ExecStart=/build/tmp.../.local/bin/clipton.
            # We rewrite it to point to the actual Nix store binary: $out/bin/clipton
            sed -i "s|$FAKE_HOME/.local/bin/|$out/bin/|g" $out/lib/systemd/user/${manifest.program}.service
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