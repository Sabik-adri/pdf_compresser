#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check for ghostscript
if ! command -v gs &>/dev/null; then
  echo "ERROR: Ghostscript not found. Install with: sudo apt install ghostscript"
  exit 1
fi

# Use project venv if it exists, else fall back to system python3
PYTHON="$SCRIPT_DIR/venv/bin/python"
if [ ! -f "$PYTHON" ]; then
  PYTHON="python3"
fi

echo "Starting PDF Compressor at http://127.0.0.1:8000"
"$PYTHON" manage.py runserver 0.0.0.0:8000
