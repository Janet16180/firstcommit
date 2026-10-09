#!/usr/bin/env bash
# Install what First Commit needs on a fresh WSL Ubuntu 24.04: git and uv, then
# the game's Python dependencies. "install.sh --dev" also installs Node and ESLint for the page
# tests. Safe to run again: each step skips what is already there.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
dockerfile=$root/deploy/docker/Dockerfile

uv_version=0.12.6
uv_sha256_x86_64=8681d8921e7d520fb368991dcf5f9c1905b80f5bf2a265a0ed085c8d8e342477
uv_sha256_aarch64=d58030acd26159499ac82f32da12d1b3c12a3a1bfc414232d9082070c03e128d

dev=false
with_docker=false

usage() {
    cat <<EOF
Usage: ./install.sh [--dev] [--docker]

Installs git, bash-completion and uv $uv_version, then runs "uv sync".
  --docker also install Docker Engine for container play
  --dev   also install Node (the version the Docker test image pins) and ESLint
EOF
}

say() {
    printf '\n== %s\n' "$*"
}

fail() {
    printf '%s\n' "$@" >&2
    exit 1
}

# Root in a container has no sudo; everyone else needs it.
as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    else
        sudo "$@"
    fi
}

check_system() {
    # shellcheck disable=SC1091
    . /etc/os-release
    if [ "${ID:-}" != ubuntu ] || [ "${VERSION_ID:-}" != 24.04 ]; then
        fail "This script is for Ubuntu 24.04 (found ${PRETTY_NAME:-an unknown system})."
    fi
    if ! grep -qi microsoft /proc/version; then
        printf 'Note: this does not look like WSL; continuing anyway.\n'
    fi
}

install_packages() {
    install_apt_packages git bash-completion less nano ca-certificates curl xz-utils
}

install_apt_packages() {
    local package
    local missing=()
    for package in "$@"; do
        if ! dpkg-query -W -f='${Status}\n' "$package" 2>/dev/null | grep -qx 'install ok installed'; then
            missing+=("$package")
        fi
    done
    if [ "${#missing[@]}" -eq 0 ]; then
        say "Required system packages are already installed"
        return
    fi
    say "Installing missing system packages: ${missing[*]}"
    if ! as_root apt-get update; then
        fail "apt could not update its package lists; required packages are missing: ${missing[*]}." \
            "Fix the repository error printed above, then run ./install.sh again."
    fi
    as_root env DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends "${missing[@]}"
}

# Docker's own apt repository, as in https://docs.docker.com/engine/install/ubuntu/.
install_docker() {
    if command -v docker >/dev/null; then
        say "Docker is already installed"
    else
        say "Installing Docker Engine"
        as_root install -m 0755 -d /etc/apt/keyrings
        as_root curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        as_root chmod a+r /etc/apt/keyrings/docker.asc
        local arch codename
        arch=$(dpkg --print-architecture)
        codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
        echo "deb [arch=$arch signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $codename stable" \
            | as_root tee /etc/apt/sources.list.d/docker.list >/dev/null
        as_root apt-get update
        as_root env DEBIAN_FRONTEND=noninteractive apt-get install --yes \
            docker-ce docker-ce-cli containerd.io docker-buildx-plugin
    fi
    if [ "$(id -u)" -ne 0 ] && ! id -nG | grep -qw docker; then
        as_root usermod -aG docker "$(id -un)"
        docker_group_added=true
    fi
    if [ "$(ps -o comm= -p 1)" = systemd ]; then
        as_root systemctl enable --now docker
    else
        printf 'systemd is off in this WSL, so Docker will not start by itself.\n'
        printf 'Add "[boot]\\nsystemd=true" to /etc/wsl.conf, then run "wsl --shutdown" from Windows.\n'
    fi
}

install_uv() {
    if command -v uv >/dev/null && [ "$(uv --version | cut -d' ' -f2)" = "$uv_version" ]; then
        say "uv $uv_version is already installed"
        return
    fi
    say "Installing uv $uv_version"
    local arch sum tarball
    arch=$(uname -m)
    case "$arch" in
        x86_64) sum=$uv_sha256_x86_64 ;;
        aarch64) sum=$uv_sha256_aarch64 ;;
        *) fail "No uv build pinned for $arch." ;;
    esac
    tarball=uv-$arch-unknown-linux-gnu.tar.gz
    curl -fsSLo "/tmp/$tarball" "https://github.com/astral-sh/uv/releases/download/$uv_version/$tarball"
    echo "$sum  /tmp/$tarball" | sha256sum --check --quiet
    mkdir -p "$HOME/.local/bin"
    tar -xzf "/tmp/$tarball" -C "$HOME/.local/bin" --strip-components=1
    rm "/tmp/$tarball"
    export PATH="$HOME/.local/bin:$PATH"
}

# The Node version and checksums come from the Docker test image, so the two never disagree.
dockerfile_arg() {
    sed -n "s/^ARG $1=//p" "$dockerfile"
}

install_node() {
    local version arch sum tarball
    version=$(dockerfile_arg NODE_VERSION)
    if command -v node >/dev/null && [ "$(node --version)" = "v$version" ]; then
        say "Node $version is already installed"
        return
    fi
    say "Installing Node $version"
    case "$(uname -m)" in
        x86_64) arch=x64 sum=$(dockerfile_arg NODE_SHA256_X64) ;;
        aarch64) arch=arm64 sum=$(dockerfile_arg NODE_SHA256_ARM64) ;;
        *) fail "No Node build pinned for $(uname -m)." ;;
    esac
    tarball=node-v$version-linux-$arch.tar.xz
    curl -fsSLo "/tmp/$tarball" "https://nodejs.org/dist/v$version/$tarball"
    echo "$sum  /tmp/$tarball" | sha256sum --check --quiet
    as_root tar -xJf "/tmp/$tarball" -C /usr/local --strip-components=1 --no-same-owner
    rm "/tmp/$tarball"
}

install_eslint() {
    install_apt_packages eslint
}

sync_game() {
    say "Installing the game's Python dependencies"
    (cd "$root" && uv sync --frozen)
}

print_next_steps() {
    say "Done"
    printf 'Play:               ./run.sh\n'
    if [ "$with_docker" = true ]; then
        if [ "${docker_group_added:-false}" = true ]; then
            printf 'For Docker, open a new WSL terminal (or run "newgrp docker") to activate your group membership.\n'
        fi
        printf 'Play in Docker:     deploy/docker/run\n'
    fi
    if [ "$dev" = true ]; then
        printf 'Run the tests:      uv run pytest -q\n'
    fi
}

main() {
    for argument in "$@"; do
        case "$argument" in
            --dev) dev=true ;;
            --docker) with_docker=true ;;
            -h | --help) usage; exit 0 ;;
            *) usage >&2; exit 2 ;;
        esac
    done
    check_system
    install_packages
    if [ "$with_docker" = true ]; then
        install_docker
    fi
    install_uv
    if [ "$dev" = true ]; then
        install_node
        install_eslint
    fi
    sync_game
    print_next_steps
}

main "$@"
