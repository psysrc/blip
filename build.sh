#!/bin/bash

set -e

# Create a single executable for the program
poetry run pyinstaller --distpath=build/bin --specpath=build --onefile "blip.py"
