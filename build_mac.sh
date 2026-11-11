#!/bin/bash
# Build Student Python Review as a standalone macOS .app bundle.
#
# Usage (from this folder, in Terminal):
#   chmod +x build_mac.sh      (only needed once)
#   ./build_mac.sh             # normal build
#   ./build_mac.sh --skip-install   # skip reinstalling pyinstaller/pillow
#   ./build_mac.sh --sign "Developer ID Application: Your Name (TEAMID)"
#
# Output:
#   dist/StudentPythonReview.app
#
# Distribute:
#   Right-click dist/StudentPythonReview.app -> Compress, then share the .zip.
#   See BUILD.md for code signing / notarization so students don't see a
#   Gatekeeper warning.

set -e
cd "$(dirname "$0")"

SKIP_INSTALL=0
SIGN_IDENTITY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-install)
            SKIP_INSTALL=1
            shift
            ;;
        --sign)
            SIGN_IDENTITY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Python: $(python3 --version)"
echo "Working directory: $(pwd)"

if [[ ! -d "Problems" ]]; then
    echo "ERROR: Problems folder not found. Expected: $(pwd)/Problems"
    exit 1
fi

if [[ $SKIP_INSTALL -eq 0 ]]; then
    echo
    echo "Installing / upgrading build and runtime packages..."
    python3 -m pip install --upgrade pip
    python3 -m pip install --upgrade pyinstaller pillow
fi

echo
echo "Building from StudentPythonReview-mac.spec (macOS .app bundle)..."
python3 -m PyInstaller --noconfirm --clean StudentPythonReview-mac.spec

APP="dist/StudentPythonReview.app"
if [[ ! -d "$APP" ]]; then
    echo "ERROR: Build finished but $APP was not found."
    exit 1
fi

# Always ad-hoc sign at minimum so Gatekeeper has a signature to check
# (prevents the "damaged and can't be opened" error after zipping/downloading).
if [[ -n "$SIGN_IDENTITY" ]]; then
    echo
    echo "Code signing with identity: $SIGN_IDENTITY"
    codesign --force --deep --options runtime --sign "$SIGN_IDENTITY" "$APP"
else
    echo
    echo "Ad-hoc signing (no Developer ID identity supplied)..."
    codesign --force --deep --sign - "$APP"
fi

echo
echo "Build succeeded."
echo "App bundle: $APP"
echo
echo "Tip: compress the .app before sharing it:"
echo "  ditto -c -k --sequesterRsrc --keepParent \"$APP\" dist/StudentPythonReview-macOS.zip"
echo
echo "See BUILD.md for code signing with your Apple Developer ID and notarization."
