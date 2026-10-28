#!/usr/bin/env bash
set -e

echo "======================================================"
echo "   AirCasta - macOS Backend Build Script"
echo "======================================================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$PROJECT_ROOT/bin"
mkdir -p "$BIN_DIR"

# Check for Homebrew
if ! command -v brew &>/dev/null; then
    echo "[ERROR] Homebrew not found. Please install Homebrew from https://brew.sh/"
    exit 1
fi

echo "[1/3] Installing dependencies via Homebrew..."
brew install cmake ninja openssl@3 libplist gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-libav

echo "[2/3] Cloning & Building UxPlay backend for macOS..."
TEMP_SRC="/tmp/UxPlay"
if [ ! -d "$TEMP_SRC" ]; then
    git clone --depth 1 https://github.com/FDH2/UxPlay.git "$TEMP_SRC"
fi

cd "$TEMP_SRC"
mkdir -p build && cd build
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja

echo "[3/3] Copying executable to $BIN_DIR/uxplay..."
cp uxplay "$BIN_DIR/uxplay"
chmod +x "$BIN_DIR/uxplay"

echo "======================================================"
echo "[SUCCESS] macOS AirPlay backend binary built successfully at:"
echo "$BIN_DIR/uxplay"
echo "Run AirCasta via: python3 main.py"
echo "======================================================"
