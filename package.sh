#!/bin/bash

set -e

PACKAGE=package/
mkdir -p $PACKAGE

# Create a single executable for the program
poetry run pyinstaller --onefile main.py
cp dist/main $PACKAGE/blip.app

# Clean up intermediate files and folders
rm -rf dist/
rm -rf build/
rm -f main.spec
