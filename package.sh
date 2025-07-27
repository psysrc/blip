#!/bin/bash

set -e

PACKAGE_DIR=package/
MAIN_NAME=blip
EXE_NAME=blip.app

mkdir -p $PACKAGE_DIR

# Create a single executable for the program
poetry run pyinstaller --onefile "$MAIN_NAME.py"
cp "dist/$MAIN_NAME" "$PACKAGE_DIR/$EXE_NAME"

# Clean up intermediate files and folders
rm -rf dist/
rm -rf build/
rm -f "$MAIN_NAME.spec"
