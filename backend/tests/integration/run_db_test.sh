#!/bin/bash
# Script to run the database connection test

# Change to the script's directory
cd "$(dirname "$0")"

# Activate the virtual environment
source ../../.venv/bin/activate

# Run the database connection test
python test_db_connection.py

# Deactivate the virtual environment
deactivate 