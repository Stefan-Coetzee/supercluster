#!/usr/bin/env python3
"""
Test script for supercluster FastAPI service with database integration
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from fastapi.testclient import TestClient
import json
import numpy as np

# Add parent directory to path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from .test_index_manager import MockSuperCluster, SAMPLE_GEOJSON

# Create a TestClient for the FastAPI app
client = TestClient(app)

# Sample test data - reduce size for faster tests
SAMPLE_POINTS = [
    {"latitude": 0.0, "longitude": 0.0, "gender": "female", "country_of_residence": "Kenya"},
    {"latitude": 1.0, "longitude": 1.0, "gender": "male", "country_of_residence": "Nigeria"},
]

class MockSuperCluster:
    def getClusters(self, top_left, bottom_right, zoom):
        return [
            {
                'id': 1,
                'count': 2,
                'expansion_zoom': zoom + 1,
                'longitude': 0.5,
                'latitude': 0.5
            }
        ]

class MockIndexManager:
    def __init__(self):
        self.calls = []
        self.indexes = {}
    
    def get_index(self, filters=None, force_refresh=False):
        self.calls.append(('get_index', filters))
        return 'test_key', MockSuperCluster()
    
    def get_original_features(self, index_key):
        return SAMPLE_GEOJSON
    
    def get_stats(self):
        return {
            "cache_hits": 0,
            "cache_misses": 0,
            "cached_indexes": 0,
            "cache_ratio": "0.0",
            "current_memory_mb": "0.0",
            "memory_history": []
        }

@pytest.fixture(autouse=True)
def mock_index_manager(monkeypatch):
    """Mock the index manager for all tests"""
    mock_manager = MockIndexManager()
    monkeypatch.setattr("main.index_manager", mock_manager)
    return mock_manager

def test_api(mock_index_manager):
    """Test the supercluster API endpoints"""
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    
    # Test getting clusters
    params = {
        "west": -180,
        "south": -85,
        "east": 180,
        "north": 85,
        "zoom": 4
    }
    
    response = client.get("/api/getClusters", params=params)
    assert response.status_code == 200
    clusters = response.json()
    assert "features" in clusters
    assert isinstance(clusters["features"], list)
    
    # Test with filters
    params["gender"] = "female"
    response = client.get("/api/getClusters", params=params)
    assert response.status_code == 200
    clusters = response.json()
    assert "features" in clusters

def test_api_error_cases():
    """Test error handling"""
    # Invalid zoom
    response = client.get("/api/getClusters", params={
        "west": -180,
        "south": -85,
        "east": 180,
        "north": 85,
        "zoom": "invalid"
    })
    assert response.status_code == 422

    # Missing parameters
    response = client.get("/api/getClusters", params={
        "zoom": 4  # Missing bbox coordinates
    })
    assert response.status_code == 422

if __name__ == "__main__":
    test_api() 