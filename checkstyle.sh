#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "Pycodestyle..."
pycodestyle register_temperatures.py || true

echo ""
echo "Pyflakes..."
pyflakes3 register_temperatures.py || true
