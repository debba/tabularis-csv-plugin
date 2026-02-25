#!/usr/bin/env bash
# Copies the plugin into the Tabularis plugins directory for local development.

set -euo pipefail

PLUGIN_ID="csv"

case "$(uname -s)" in
  Linux*)
    PLUGINS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/tabularis/plugins"
    ;;
  Darwin*)
    PLUGINS_DIR="$HOME/Library/Application Support/com.debba.tabularis/plugins"
    ;;
  CYGWIN*|MINGW*|MSYS*)
    PLUGINS_DIR="${APPDATA}/com.debba.tabularis/plugins"
    ;;
  *)
    echo "Unsupported OS: $(uname -s)" >&2
    exit 1
    ;;
esac

DEST="$PLUGINS_DIR/$PLUGIN_ID"
mkdir -p "$DEST"

cp plugin.py manifest.json "$DEST/"
chmod +x "$DEST/plugin.py"

echo "Installed to: $DEST"
