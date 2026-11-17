#!/bin/bash
# -------------------------------------------------------------
# Customer Behavior Analytics - Streamlit Dashboard Launcher
# -------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting it up..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Ensure data pipeline has been run
if [ ! -f "customer_shopping_behavior_cleaned.csv" ]; then
    echo "Running data pipeline first..."
    ./venv/bin/python run_pipeline.py
fi

echo "=================================================="
echo "🚀 Launching Customer Behavior Analytics Dashboard"
echo "   URL: http://localhost:8501"
echo "=================================================="

./venv/bin/streamlit run app.py --server.headless=false

