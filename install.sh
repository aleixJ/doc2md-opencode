#!/usr/bin/env sh
# Copy-only installer for the doc2md-opencode skill and command.
# No network access; only files inside the target .opencode are modified.
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SOURCE_ROOT="$SCRIPT_DIR/.opencode"

PROJECT="."
GLOBAL=0

while [ $# -gt 0 ]; do
    case "$1" in
        --global) GLOBAL=1; shift ;;
        --path)
            if [ $# -lt 2 ]; then
                echo "--path requires a project directory" >&2
                exit 1
            fi
            PROJECT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--global | --path <project-dir>]"
            exit 0
            ;;
        *) PROJECT="$1"; shift ;;
    esac
done

if [ ! -d "$SOURCE_ROOT" ]; then
    echo "Cannot find source directory: $SOURCE_ROOT" >&2
    exit 1
fi

if [ "$GLOBAL" -eq 1 ]; then
    DEST_ROOT="${HOME}/.config/opencode"
else
    DEST_ROOT="${PROJECT}/.opencode"
fi

mkdir -p "$DEST_ROOT/skills" "$DEST_ROOT/commands"
cp -R "$SOURCE_ROOT/skills/." "$DEST_ROOT/skills/"
cp -R "$SOURCE_ROOT/commands/." "$DEST_ROOT/commands/"

# Never ship Python bytecode caches.
find "$DEST_ROOT" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

echo "Installed doc2md-opencode into: $DEST_ROOT"

# Probe by execution, not just presence, so broken shims are skipped.
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [ -n "$PYTHON" ]; then
    echo "Detected Python launcher: $PYTHON"
    if ! "$PYTHON" -c "import pymupdf" >/dev/null 2>&1; then
        echo "WARNING: PyMuPDF is not installed. Run:  $PYTHON -m pip install pymupdf" >&2
    fi
else
    echo "WARNING: No working Python launcher found. Install Python 3.8+ and PyMuPDF." >&2
fi
