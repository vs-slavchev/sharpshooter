#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/vs-slavchev/sharpshooter.git"

if command -v pipx &>/dev/null; then
    pipx install "git+$REPO"
elif command -v uv &>/dev/null; then
    uv tool install "git+$REPO"
else
    echo "pipx or uv is required to install sharpshooter."
    echo ""
    echo "  Install pipx:  https://pipx.pypa.io/stable/installation/"
    echo "  Install uv:    https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo ""
echo "sharpshooter installed. Run it with: sharpshooter"
