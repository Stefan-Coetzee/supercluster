#!/bin/bash
# Script to run the integration tests

# Exit on error, undefined variables, and propagate pipeline failures
set -euo pipefail

echo "🧪 Running integration tests..."

# Change to the script's directory
cd "$(dirname "$0")"

# Ensure the integration directory exists
if [ ! -d "integration" ]; then
    echo "❌ Error: integration directory not found"
    exit 1
fi

# Check if we have any test files
if [ "$(find integration -name 'test_*.py' | wc -l)" -eq 0 ]; then
    echo "❌ Error: No test files found in integration directory"
    exit 1
fi

# Activate the virtual environment
if [ ! -f "../../.venv/bin/activate" ]; then
    echo "❌ Error: Virtual environment not found at ../../.venv"
    exit 1
fi

echo "🔄 Activating virtual environment..."
source ../../.venv/bin/activate

# Check for required dependencies
if ! python -c "import pytest, pymysql, dotenv" 2>/dev/null; then
    echo "❌ Error: Missing required dependencies. Please install with:"
    echo "pip install pytest pymysql python-dotenv"
    exit 1
fi

# Run the integration tests only
echo "🚀 Running integration tests..."
python -m pytest integration/ -v

# Report test status
TEST_STATUS=$?
if [ $TEST_STATUS -eq 0 ]; then
    echo "✅ Integration tests passed successfully!"
else
    echo "❌ Integration tests failed with exit code $TEST_STATUS"
fi

# Deactivate the virtual environment
echo "🔄 Deactivating virtual environment..."
deactivate

exit $TEST_STATUS 