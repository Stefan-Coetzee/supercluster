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

# Add parent directory to path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from test_index_manager import MockSuperCluster, SAMPLE_GEOJSON

# Create a TestClient for the FastAPI app
client = TestClient(app)

class MockIndexManager:
    """Mock implementation of IndexManager for API tests"""
    def __init__(self):
        self.calls = []
        self.indexes = {}
        self.geojson_cache = {}
    
    def get_index(self, filters=None, force_refresh=False):
        self.calls.append(('get_index', filters, force_refresh))
        
        # Generate a deterministic key for the filters
        key = 'all'
        if filters:
            key = '_'.join(f"{k}={v}" for k, v in sorted(filters.items()))
        
        # Create a mock SuperCluster
        if key not in self.indexes:
            self.indexes[key] = MockSuperCluster()
            # Also store mock GeoJSON
            self.geojson_cache[key] = SAMPLE_GEOJSON
        
        return key, self.indexes[key]
    
    def get_original_features(self, index_key):
        self.calls.append(('get_original_features', index_key))
        return self.geojson_cache.get(index_key, [])
    
    def get_stats(self):
        self.calls.append(('get_stats',))
        return {
            "cache_hits": 5,
            "cache_misses": 2,
            "cached_indexes": len(self.indexes),
            "cache_ratio": "0.71"
        }
    
    def clear_cache(self):
        self.calls.append(('clear_cache',))
        self.indexes = {}
        self.geojson_cache = {}

@pytest.fixture
def mock_index_manager():
    """Mock the index manager for API tests"""
    mock_manager = MockIndexManager()
    
    with patch('main.index_manager', mock_manager):
        yield mock_manager

def test_api():
    """Test the supercluster API endpoints"""
    # 1. Test the root endpoint
    response = client.get("/")
    print("Root endpoint:", response.json())
    
    # 2. Get available filters
    response = client.get("/api/availableFilters")
    print("\nAvailable filters:", json.dumps(response.json(), indent=2))
    
    # 3. Get clusters with no filters
    print("\nFetching clusters with no filters...")
    response = client.post("/api/getClusters", json={
        "bbox": [-180, -85, 180, 85],
        "zoom": 4,
        "filters": None
    })
    
    assert response.status_code == 200, f"Error: {response.text}"
    clusters = response.json()
    cluster_count = len(clusters.get("features", []))
    print(f"Retrieved {cluster_count} clusters/points at zoom level 4")
    
    # 4. Get clusters at different zoom levels
    zoom_levels = [0, 8, 12]
    
    for zoom in zoom_levels:
        print(f"\nFetching clusters at zoom level {zoom}...")
        response = client.post("/api/getClusters", json={
            "bbox": [-180, -85, 180, 85],
            "zoom": zoom,
            "filters": None
        })
        
        assert response.status_code == 200, f"Error at zoom {zoom}: {response.text}"
        clusters = response.json()
        cluster_count = len(clusters.get("features", []))
        print(f"Retrieved {cluster_count} clusters/points at zoom level {zoom}")
    
    # 5. Test with gender filter
    print("\nFetching clusters with gender filter...")
    response = client.post("/api/getClusters", json={
        "bbox": [-180, -85, 180, 85],
        "zoom": 4,
        "filters": {
            "gender": "Male"
        }
    })
    
    assert response.status_code == 200, f"Error with filter: {response.text}"
    clusters = response.json()
    cluster_count = len(clusters.get("features", []))
    print(f"Retrieved {cluster_count} clusters/points with gender filter")
    
    # 6. Get cache stats
    print("\nFetching cache stats...")
    response = client.get("/api/stats")
    print("Cache stats:", json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text)
    
    # 7. Clear cache
    print("\nClearing cache...")
    response = client.post("/api/clearCache")
    print("Clear cache response:", response.json() if response.status_code == 200 else response.text)

def test_error_handling_get_clusters():
    """Test error handling in getClusters endpoint"""
    # Simulate an error in index_manager.get_index
    with patch('main.index_manager.get_index', side_effect=Exception("Test error")):
        response = client.post("/api/getClusters", json={
            "bbox": [-180, -85, 180, 85],
            "zoom": 4,
            "filters": None
        })
        
        # The API should return 500 for server errors
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"]

if __name__ == "__main__":
    test_api() 