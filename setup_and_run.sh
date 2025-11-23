#!/bin/bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (including selenium)
pip install -r requirements.txt

# Run the GUI
streamlit run app.py
