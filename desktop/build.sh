#!/bin/bash
# Build the KnowledgeNet desktop app with PyInstaller. Run from the desktop/ folder.
cd "$(dirname "$0")"

# Define variables
APP_NAME="KnowledgeNet"
DIST_FOLDER="dist"
DMG_NAME="${APP_NAME}.dmg"
EXE_NAME="${APP_NAME}.exe"
VOL_NAME="${APP_NAME} Installer"
MAIN_FILE="main.py"
BACKEND_PATH="../backend"
INSTALLER_SRC="_installer"
VENV_DIR="venv"
REQUIREMENTS_FILE="../requirements-desktop.txt"
OS_TYPE=$(uname -s)

# Check if requirements.txt exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "Error: $REQUIREMENTS_FILE not found!"
  exit 1
fi

# Check if main.py exists
if [ ! -f "$MAIN_FILE" ]; then
  echo "Error: $MAIN_FILE not found!"
  exit 1
fi

# Check if backend directory exists
if [ ! -d "$BACKEND_PATH" ]; then
  echo "Error: $BACKEND_PATH directory not found!"
  exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment (adjust based on OS)
if [ "$OS_TYPE" = "Darwin" ] || [ "$OS_TYPE" = "Linux" ]; then
  source "$VENV_DIR/bin/activate"
elif [ "$OS_TYPE" = "CYGWIN_NT-*" ] || [ "$OS_TYPE" = "MINGW*" ]; then
  source "$VENV_DIR/Scripts/activate"
else
  echo "Error: Unsupported OS for virtual environment activation!"
  exit 1
fi

# Install dependencies
echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r "$REQUIREMENTS_FILE"

# Build for the current OS
if [ "$OS_TYPE" = "Darwin" ]; then
  # macOS build
  pyinstaller \
    --name "$APP_NAME" \
    --windowed \
    --add-data "$BACKEND_PATH:backend" \
    --add-data "assets:assets" \
    "$MAIN_FILE"

  # Check if dist folder was created
  if [ ! -d "$DIST_FOLDER" ]; then
    echo "Error: $DIST_FOLDER folder not found after PyInstaller!"
    exit 1
  fi

  # Copy _installer to dist/NewProject.app/Contents
  INSTALLER_DEST="$DIST_FOLDER/$APP_NAME.app/Contents"
  if [ -f "$INSTALLER_SRC" ]; then
    mkdir -p "$INSTALLER_DEST"
    cp "$INSTALLER_SRC" "$INSTALLER_DEST/"
    echo "Copied _installer to $INSTALLER_DEST"
  else
    echo "Warning: _installer not found, skipping copy."
  fi

  # Move _internal from dist/NewProject to dist/NewProject.app/Contents
  INTERNAL_SRC="$DIST_FOLDER/$APP_NAME/_internal"
  INTERNAL_DEST="$DIST_FOLDER/$APP_NAME.app/Contents"
  if [ -d "$INTERNAL_SRC" ]; then
    mkdir -p "$INTERNAL_DEST"
    mv "$INTERNAL_SRC" "$INTERNAL_DEST/"
    if [ $? -ne 0 ]; then
      echo "Error: Failed to move _internal to $INTERNAL_DEST!"
      exit 1
    fi
    echo "Moved _internal to $INTERNAL_DEST"
  else
    echo "Warning: _internal directory not found in $INTERNAL_SRC, skipping move."
  fi

  # Check if the app exists
  if [ ! -d "$DIST_FOLDER/$APP_NAME.app" ]; then
    echo "Error: $DIST_FOLDER/$APP_NAME.app not found!"
    exit 1
  fi

  # Create the DMG
  hdiutil create -volname "$VOL_NAME" -srcfolder "$DIST_FOLDER/$APP_NAME.app" -ov -format UDZO "$DMG_NAME"
  echo "DMG created successfully: $DMG_NAME"

elif [ "$OS_TYPE" = "Linux" ] || [ "$OS_TYPE" = "CYGWIN_NT-*" ] || [ "$OS_TYPE" = "MINGW*" ]; then
  # Windows/Linux build (assuming cross-compilation or native Windows with adjustments)
  pyinstaller \
    --name "$APP_NAME" \
    --windowed \
    --add-data "$BACKEND_PATH;backend" \
    --add-data "assets;assets" \
    --icon "app-icon.ico" \
    "$MAIN_FILE"

  # Check if dist folder was created
  if [ ! -d "$DIST_FOLDER" ]; then
    echo "Error: $DIST_FOLDER folder not found after PyInstaller!"
    exit 1
  fi

  # Copy _installer to dist/NewProject
  INSTALLER_DEST="$DIST_FOLDER/$APP_NAME"
  if [ -f "$INSTALLER_SRC" ]; then
    mkdir -p "$INSTALLER_DEST"
    cp "$INSTALLER_SRC" "$INSTALLER_DEST/"
    echo "Copied _installer to $INSTALLER_DEST"
  else
    echo "Warning: _installer not found, skipping copy."
  fi

  # Check if the exe exists
  if [ ! -f "$DIST_FOLDER/$APP_NAME/$EXE_NAME" ]; then
    echo "Error: $DIST_FOLDER/$APP_NAME/$EXE_NAME not found!"
    exit 1
  fi

  # Optional: Create a simple installer using NSIS (if installed)
  if command -v makensis >/dev/null 2>&1; then
    echo "Creating NSIS installer..."
    cat > installer.nsi << EOL
      !define APPNAME "$APP_NAME"
      !define COMPANYNAME "YourCompany"
      !define EXEFILE "\${APPNAME}.exe"
      OutFile "\${APPNAME}_Setup.exe"
      InstallDir "\$PROGRAMFILES\\\$APP_NAME"
      Page directory
      Page instfiles
      Section "Install"
        SetOutPath \$INSTDIR
        File "\${DIST_FOLDER}\\${APP_NAME}\\${EXEFILE}"
        CreateShortcut "\$DESKTOP\\\$APP_NAME.lnk" "\$INSTDIR\\${EXEFILE}"
        WriteUninstaller "\$INSTDIR\\uninstall.exe"
      SectionEnd
      Section "Uninstall"
        Delete "\$DESKTOP\\\$APP_NAME.lnk"
        RMDir /r "\$INSTDIR"
      SectionEnd
EOL
    makensis installer.nsi
    echo "NSIS installer created: ${APP_NAME}_Setup.exe"
  else
    echo "Warning: NSIS not found. Only executable created in $DIST_FOLDER/$APP_NAME/"
  fi
else
  echo "Error: Unsupported OS or cross-compilation not configured!"
  exit 1
fi

# Deactivate virtual environment
deactivate
echo "Virtual environment deactivated."