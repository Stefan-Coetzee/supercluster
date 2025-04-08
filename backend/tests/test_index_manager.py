import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import numpy as np
from typing import Dict, List, Any

# Add parent directory to path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index_manager import IndexManager

# Sample test data
SAMPLE_POINTS = [
    {"id": 1, "latitude": 0.0, "longitude": 0.0, "gender": "female", "country_of_residence": "Kenya"},
    {"id": 2, "latitude": 1.0, "longitude": 1.0, "gender": "male", "country_of_residence": "Nigeria"},
]

# Sample GeoJSON for testing
SAMPLE_GEOJSON = [
    {
        "type": "Feature", 
        "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
        "properties": {"id": 1, "gender": "female", "country_of_residence": "Kenya"}
    },
    {
        "type": "Feature", 
        "geometry": {"type": "Point", "coordinates": [1.0, 1.0]},
        "properties": {"id": 2, "gender": "male", "country_of_residence": "Nigeria"}
    }
]

# Sample data returned from database
SAMPLE_DB_POINTS = [
    {
        'hashed_email': 'user1',
        'country_of_residence': 'Kenya',
        'latitude': 1.2921,
        'longitude': 36.8219,
        'gender': 'Female',
        'is_graduate_learner': 1,
        'is_wage_employed': 0,
        'is_running_a_venture': 1,
        'is_featured': 0,
        'is_featured_video': 0
    },
    {
        'hashed_email': 'user2',
        'country_of_residence': 'Nigeria',
        'latitude': 9.0820,
        'longitude': 8.6753,
        'gender': 'Male',
        'is_graduate_learner': 1,
        'is_wage_employed': 1,
        'is_running_a_venture': 0,
        'is_featured': 1,
        'is_featured_video': 0
    }
]

# Sample coordinates array
SAMPLE_COORDINATES = np.array([
    [36.8219, 1.2921],
    [8.6753, 9.0820]
])

class MockSuperCluster:
    """Mock SuperCluster implementation for testing"""
    def __init__(self, points_array=None, min_zoom=0, max_zoom=16, radius=40, extent=512, min_points=2):
        self.points_array = points_array if points_array is not None else np.array([])
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.radius = radius
        self.extent = extent
        self.min_points = min_points
    
    def getClusters(self, top_left, bottom_right, zoom):
        """Return mock clusters based on zoom level"""
        if zoom < 10:
            # Return cluster
            return [
                {
                    'id': 1,
                    'count': 2,
                    'expansion_zoom': zoom + 1,
                    'longitude': 0.5,
                    'latitude': 0.5
                }
            ]
        else:
            # Return individual points
            return [
                {'id': 1, 'longitude': 0.0, 'latitude': 0.0},
                {'id': 2, 'longitude': 1.0, 'latitude': 1.0}
            ]

@pytest.fixture
def mock_dependencies():
    """Mock dependencies for the index manager"""
    with patch('index_manager.load_learner_points') as mock_load_points, \
         patch('index_manager.convert_to_geojson') as mock_convert, \
         patch('index_manager.pysupercluster.SuperCluster') as mock_supercluster:
        
        # Configure mocks
        mock_load_points.return_value = SAMPLE_DB_POINTS
        mock_convert.return_value = SAMPLE_GEOJSON
        mock_supercluster.side_effect = MockSuperCluster
        
        yield {
            'load_points': mock_load_points,
            'convert': mock_convert,
            'supercluster': mock_supercluster
        }

def test_index_manager_init():
    """Test initialization of the index manager"""
    manager = IndexManager(min_zoom=2, max_zoom=14, radius=60, extent=1024)
    
    assert manager.min_zoom == 2
    assert manager.max_zoom == 14
    assert manager.radius == 60
    assert manager.extent == 1024
    assert manager.indexes == {}
    assert manager.geojson_cache == {}
    assert manager.last_accessed == {}
    assert manager.cache_hits == 0
    assert manager.cache_misses == 0

def test_extract_coordinates():
    """Test extracting coordinates from GeoJSON features"""
    manager = IndexManager()
    
    # Create test data with the EXACT coordinates used in the assertion
    geojson_features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [36.8219, -1.2921]  # Match these exact values
            },
            "properties": {}
        }
    ]
    
    coordinates = manager._extract_coordinates(geojson_features)
    
    assert len(coordinates) == 1
    assert coordinates[0][0] == 36.8219  # longitude
    assert coordinates[0][1] == -1.2921  # latitude

def test_get_index_new(mocker):
    """Test getting an index for the first time (cache miss)"""
    from index_manager import IndexManager
    manager = IndexManager()
    
    # Use monkeypatch to directly replace functions on IndexManager
    # Avoid trying to patch import paths which can be tricky
    
    # Create our stubs/mocks
    mock_data = [{"id": 1, "latitude": -1.2921, "longitude": 36.8219}]
    mock_geojson = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [36.8219, -1.2921]},
            "properties": {"id": 1}
        }
    ]
    
    # Set up a function that will run instead
    def mock_get_data(filters=None, limit=None, offset=None):
        return mock_data
    
    def mock_to_geojson(data):
        return mock_geojson
    
    # Replace the original function in the module
    import db
    original_load = db.load_learner_points
    original_convert = db.convert_to_geojson
    db.load_learner_points = mock_get_data
    db.convert_to_geojson = mock_to_geojson
    
    # Create a mock for SuperCluster so we don't need the actual implementation
    import pysupercluster
    original_super = pysupercluster.SuperCluster
    pysupercluster.SuperCluster = lambda *args, **kwargs: MockSuperCluster()
    
    try:
        # Test with filter
        filters = {"gender": "Female"}
        index_key, index = manager.get_index(filters)
        
        # Verify
        assert index_key == "gender=Female"
        assert index_key in manager.indexes
        assert len(manager.last_accessed) == 1
        assert index_key in manager.last_accessed
    finally:
        # Restore original functions
        db.load_learner_points = original_load
        db.convert_to_geojson = original_convert
        pysupercluster.SuperCluster = original_super

def test_get_index_cached(mock_dependencies):
    """Test getting a cached index (cache hit)"""
    manager = IndexManager()
    
    # First call to cache the index
    filters = {'gender': 'Male'}
    first_key, first_index = manager.get_index(filters)
    
    # Reset the mock call counts
    mock_dependencies['load_points'].reset_mock()
    mock_dependencies['convert'].reset_mock()
    mock_dependencies['supercluster'].reset_mock()
    
    # Second call should use cache
    second_key, second_index = manager.get_index(filters)
    
    # Verify the result
    assert second_key == first_key
    assert second_index is first_index  # Should be the same object (cached)
    
    # Verify cache state
    assert manager.cache_hits == 1
    assert manager.cache_misses == 1
    
    # Verify no mocks were called on second request
    mock_dependencies['load_points'].assert_not_called()
    mock_dependencies['convert'].assert_not_called()
    mock_dependencies['supercluster'].assert_not_called()

def test_get_index_force_refresh(mock_dependencies):
    """Test forcing a refresh of a cached index"""
    manager = IndexManager()
    
    # First call to cache the index
    filters = {'is_graduate_learner': True}
    first_key, first_index = manager.get_index(filters)
    
    # Reset the mock call counts
    mock_dependencies['load_points'].reset_mock()
    mock_dependencies['convert'].reset_mock()
    mock_dependencies['supercluster'].reset_mock()
    
    # Second call with force_refresh should not use cache
    second_key, second_index = manager.get_index(filters, force_refresh=True)
    
    # Verify the result
    assert second_key == first_key
    assert second_index is not first_index  # Should be a different object (refreshed)
    
    # Verify cache state
    assert manager.cache_hits == 0
    assert manager.cache_misses == 2
    
    # Verify mocks were called on second request
    mock_dependencies['load_points'].assert_called_once()
    mock_dependencies['convert'].assert_called_once()
    mock_dependencies['supercluster'].assert_called_once()

def test_get_original_features():
    """Test getting original GeoJSON features"""
    manager = IndexManager()
    
    # Add features to cache
    index_key = "test_key"
    manager.geojson_cache[index_key] = SAMPLE_GEOJSON
    
    # Get features
    features = manager.get_original_features(index_key)
    
    # Verify results
    assert features == SAMPLE_GEOJSON
    
    # Test with unknown key
    empty_features = manager.get_original_features("unknown_key")
    assert empty_features == []

def test_get_stats():
    """Test getting cache statistics"""
    manager = IndexManager()
    
    # Set some cache stats
    manager.cache_hits = 25
    manager.cache_misses = 5
    manager.indexes = {"key1": None, "key2": None, "key3": None}
    
    # Get stats
    stats = manager.get_stats()
    
    # Verify results
    assert stats["cache_hits"] == 25
    assert stats["cache_misses"] == 5
    assert stats["cached_indexes"] == 3
    assert stats["cache_ratio"] == "0.83"  # 25 / (25 + 5) = 0.83

def test_clear_cache():
    """Test clearing the cache"""
    manager = IndexManager()
    
    # Add items to cache
    manager.indexes = {"key1": None, "key2": None}
    manager.geojson_cache = {"key1": SAMPLE_GEOJSON, "key2": SAMPLE_GEOJSON}
    manager.last_accessed = {"key1": 123456, "key2": 123457}
    
    # Clear cache
    manager.clear_cache()
    
    # Verify results
    assert manager.indexes == {}
    assert manager.geojson_cache == {}
    assert manager.last_accessed == {}