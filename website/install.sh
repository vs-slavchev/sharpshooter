#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/vs-slavchev/sharpshooter.git"

if command -v uv &>/dev/null; then
    uv tool install "git+$REPO"
else
    pip install --user "git+$REPO"
fi

echo ""
echo "sharpshooter installed. Run it with: sharpshooter"
