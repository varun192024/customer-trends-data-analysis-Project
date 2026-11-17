#!/bin/bash
# -------------------------------------------------------------
# Customer Behavior Analytics - Open Standalone HTML Dashboard
# -------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "dashboard.html" ]; then
    echo "dashboard.html not found. Generating it now..."
    ./venv/bin/python run_pipeline.py
fi

echo "Opening dashboard.html in your default web browser..."
open dashboard.html

