"""
The installer, ``install.sh``: its options, and its pins agreeing with the Docker image's.

Installing for real needs sudo and the network, so it is checked by hand in a clean Ubuntu
container (see the script's header); these tests run the script only as far as its options.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.sh"
DOCKERFILE = ROOT / "deploy" / "docker" / "Dockerfile"


def run_install(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(INSTALL), *arguments], capture_output=True, text=True, check=False)


def test_the_installer_is_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(INSTALL)], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_help_names_the_dev_option_and_installs_nothing() -> None:
    result = run_install("--help")

    assert result.returncode == 0
    assert "--dev" in result.stdout
    assert "==" not in result.stdout


def test_an_unknown_option_is_refused_with_the_usage() -> None:
    result = run_install("--everything")

    assert result.returncode == 2
    assert "Usage: ./install.sh" in result.stderr


def test_the_installer_pins_the_uv_version_the_test_image_copies() -> None:
    installer = re.search(r"^uv_version=(\S+)$", INSTALL.read_text(), re.MULTILINE)
    image = re.search(r"astral-sh/uv:([0-9.]+)@", DOCKERFILE.read_text())

    assert installer is not None
    assert image is not None
    assert installer.group(1) == image.group(1)


def test_the_installer_takes_node_from_the_test_image_pins() -> None:
    dockerfile = DOCKERFILE.read_text()

    for name in ("NODE_VERSION", "NODE_SHA256_X64", "NODE_SHA256_ARM64"):
        assert re.search(rf"^ARG {name}=\S+$", dockerfile, re.MULTILINE), name
        assert f"dockerfile_arg {name}" in INSTALL.read_text()
