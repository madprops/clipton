from setuptools import setup, find_packages
from pathlib import Path
import json
import subprocess

with open("manifest.json", "r") as file:
    manifest = json.load(file)

title = manifest["title"]
program = manifest["program"]
version = manifest["version"]

package_data = {}

def _post_install():
    _create_service_file()

def _create_service_file():
    path_to_bin = Path(f"~/.local/bin/{program}").expanduser().resolve()

    content = f"""[Unit]
Description=Daemon for Clipton (Clipboard Manager)

[Service]
Type=simple
ExecStart={path_to_bin} watcher

[Install]
WantedBy=graphical.target
"""

    service_dir = Path("~/.config/systemd/user").expanduser().resolve()
    service_dir.mkdir(parents=True, exist_ok=True)
    service_file = Path(service_dir, f"{program}.service").expanduser().resolve()
    print(service_file)

    with open(service_file, "w") as f:
        f.write(content)

    subprocess.run(["systemctl", "--user", "daemon-reload"])

setup(
    name = title,
    version = version,
    packages = find_packages(where="."),
    package_dir = {"": "."},
    package_data = package_data,
    py_modules=[program],
    entry_points = {
        "console_scripts": [
            f"{program}={program}:main",
        ],
    },
)

_post_install()