#!/bin/bash
# Run all unit tests for the SuperCluster API

# Activate the virtual environment
source ../.venv/bin/activate

# Run the tests with pytest
cd tests && python -m pytest 