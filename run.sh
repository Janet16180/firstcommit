#!/usr/bin/env bash
# Launch First Commit from this checkout, including when called from another directory.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
    printf 'uv is missing. Run "%s/install.sh" first.\n' "$root" >&2
    exit 1
fi

cd "$root"
exec uv run --frozen firstcommit serve "$@"
