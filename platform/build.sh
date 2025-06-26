#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Configuration
# -----------------------------
APP_NAME="KnowledgeNet"
DIST_FOLDER="dist"
DMG_NAME="${APP_NAME}.dmg"
EXE_NAME="${APP_NAME}.exe"
VOL_NAME="${APP_NAME} Installer"
MAIN_FILE="main.py"
BACKEND_PATH="../KnowledgeNetBackend"
INSTALLER_SRC="_internal"
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
OS_TYPE="$(uname -s)"

# -----------------------------
# Sanity checks
# -----------------------------
if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "Error: $REQUIREMENTS_FILE not found!" >&2
  exit 1
fi

if [[ ! -f "$MAIN_FILE" ]]; then
  echo "Error: $MAIN_FILE not found!" >&2
  exit 1
fi

if [[ ! -d "$BACKEND_PATH" ]]; then
  echo "Error: backend directory $BACKEND_PATH not found!" >&2
  exit 1
fi

# -----------------------------
# 1. Create & activate venv
# -----------------------------
if [[ ! -d "$VENV_DIR" ]]; then
  echo "==> Creating virtual environment in ./$VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
fi

echo "==> Activating virtual environment ..."
case "$OS_TYPE" in
  Darwin|Linux)
    source "$VENV_DIR/bin/activate"
    ;;
  CYGWIN*|MINGW*)
    source "$VENV_DIR/Scripts/activate"
    ;;
  *)
    echo "Error: Unsupported OS type '$OS_TYPE' for venv activation" >&2
    exit 1
    ;;
esac

# -----------------------------
# 2. Install requirements
# -----------------------------
echo "==> Installing dependencies from $REQUIREMENTS_FILE ..."
pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE"

# -----------------------------
# 3. Build & Package (Standalone)
# -----------------------------
if [[ "$OS_TYPE" == "Darwin" ]]; then
  echo "==> Running PyInstaller for macOS (one-file standalone)..."
  pyinstaller \
    --onefile \
    --name "$APP_NAME" \
    --windowed \
    --add-data "KnowledgeNetBackend:KnowledgeNetBackend" \
    "$MAIN_FILE"

#  echo "==> Copying installer assets into bundle ..."
#  APP_BUNDLE="${DIST_FOLDER}/${APP_NAME}.app/Contents"
#  [[ -f "$INSTALLER_SRC" ]] && mkdir -p "$APP_BUNDLE" && cp "$INSTALLER_SRC" "$APP_BUNDLE/"
#
#  INTERNAL_SRC="${DIST_FOLDER}/${APP_NAME}/_internal"
#  [[ -d "$INTERNAL_SRC" ]] && mkdir -p "$APP_BUNDLE" && mv "$INTERNAL_SRC" "$APP_BUNDLE/"
#
  # -----------------------------
  # Copy KnowledgeNetBackend and focus.gif to MacOS folder
  # -----------------------------
  MACOS_DIR="${DIST_FOLDER}/${APP_NAME}.app/Contents/MacOS"
  [[ -d "$BACKEND_PATH" ]] && cp -r "$BACKEND_PATH" "$MACOS_DIR/"
  [[ -f "../focus.gif" ]] && cp "./focus.gif" "$MACOS_DIR/"

  echo "==> Copied KnowledgeNetBackend and focus.gif to $MACOS_DIR"

  echo "==> Creating DMG: $DMG_NAME"
  hdiutil create \
    -volname "$VOL_NAME" \
    -srcfolder "$DIST_FOLDER/$APP_NAME.app" \
    -format UDZO \
    "$DMG_NAME"

  echo "✅ macOS .dmg built at $(pwd)/$DMG_NAME"

else
  echo "==> Running PyInstaller for Linux/Windows (one-file standalone)..."
  pyinstaller \
    --onefile \
    --name "$APP_NAME" \
    --windowed \
    --add-data "$BACKEND_PATH;KnowledgeNetBackend" \
    --icon "app-icon.ico" \
    "$MAIN_FILE"

  echo "==> Copying installer assets into dist folder ..."
  INSTALLER_DEST="$DIST_FOLDER/$APP_NAME"
  [[ -f "$INSTALLER_SRC" ]] && mkdir -p "$INSTALLER_DEST" && cp "$INSTALLER_SRC" "$INSTALLER_DEST/"

  if command -v makensis &>/dev/null; then
    echo "==> Generating NSIS installer..."
    cat > installer.nsi <<EOL
!define APPNAME "${APP_NAME}"
!define COMPANYNAME "YourCompany"
!define EXEFILE "\${APPNAME}.exe"
OutFile "\${APPNAME}_Setup.exe"
InstallDir "\$PROGRAMFILES\\\$APPNAME"
Page directory
Page instfiles
Section "Install"
  SetOutPath \$INSTDIR
  File "${DIST_FOLDER}\\${APP_NAME}\\${EXE_NAME}"
  CreateShortcut "\$DESKTOP\\\$APPNAME.lnk" "\$INSTDIR\\${EXE_NAME}"
  WriteUninstaller "\$INSTDIR\\uninstall.exe"
SectionEnd
Section "Uninstall"
  Delete "\$DESKTOP\\\$APPNAME.lnk"
  RMDir /r "\$INSTDIR"
SectionEnd
EOL
    makensis installer.nsi
    echo "✅ NSIS installer created: ${APP_NAME}_Setup.exe"
  else
    echo "⚠️  NSIS not found; executable is in $DIST_FOLDER/$APP_NAME/"
  fi
fi

# -----------------------------
# 4. Cleanup
# -----------------------------
echo "==> Deactivating virtual environment"
deactivate

echo "🎉 Build & packaging complete!"
