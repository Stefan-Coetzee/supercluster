import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from typing import Dict, List, Any

# Add parent directory to path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import (
    execute_query,
    load_learner_points,
    convert_to_geojson,
    generate_filter_key
)

# Sample test data
SAMPLE_DB_POINTS = [
    {
        'hashed_email': 'user1',
        'country_of_residence': 'Kenya',
        'latitude': 1.2921,
        'longitude': 36.8219,
        'gender': 'female',
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
        'gender': 'male',
        'is_graduate_learner': 1,
        'is_wage_employed': 1,
        'is_running_a_venture': 0,
        'is_featured': 1,
        'is_featured_video': 0
    }
]

@pytest.fixture
def mock_db_connection():
    """Create a mock database connection"""
    with patch('db.get_connection') as mock_conn:
        # Create mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = SAMPLE_DB_POINTS
        
        # Set up connection to return mock cursor
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_conn

@patch('db.get_connection')
def test_execute_query(mock_get_connection):
    """Test the execute_query function"""
    # Set up mock
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = SAMPLE_DB_POINTS
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_connection
    
    # Execute function
    result = execute_query("SELECT * FROM test_table")
    
    # Verify results
    assert result == SAMPLE_DB_POINTS
    mock_cursor.execute.assert_called_once()
    mock_connection.close.assert_called_once()

@patch('db.execute_query')
def test_load_learner_points_no_filters(mock_execute_query):
    """Test loading learner points without filters"""
    # Set up mock
    mock_execute_query.return_value = SAMPLE_DB_POINTS
    
    # Call function
    result = load_learner_points(limit=10, offset=0)
    
    # Verify results
    assert result == SAMPLE_DB_POINTS
    mock_execute_query.assert_called_once()
    
    # Check that query includes LIMIT and OFFSET
    args = mock_execute_query.call_args[0]
    assert "LIMIT" in args[0]
    assert (10, 0) == args[1]

@patch('db.execute_query')
def test_load_learner_points_with_filters(mock_execute_query):
    """Test loading learner points with filters"""
    # Set up mock
    mock_execute_query.return_value = [SAMPLE_DB_POINTS[0]]  # Only return first item
    
    # Create filters
    filters = {
        'gender': 'female',
        'is_graduate_learner': True
    }
    
    # Call function
    result = load_learner_points(filters=filters)
    
    # Verify results
    assert result == [SAMPLE_DB_POINTS[0]]
    mock_execute_query.assert_called_once()
    
    # Check that query includes filters
    args = mock_execute_query.call_args[0]
    assert "gender = %s" in args[0]
    assert "is_graduate_learner = %s" in args[0]
    assert ('female', 1) == args[1]

def test_convert_to_geojson():
    """Test converting database points to GeoJSON format"""
    # Call function
    geojson_features = convert_to_geojson(SAMPLE_DB_POINTS)
    
    # Verify results
    assert len(geojson_features) == 2
    
    # Check first feature
    assert geojson_features[0]['type'] == 'Feature'
    assert geojson_features[0]['geometry']['type'] == 'Point'
    assert geojson_features[0]['geometry']['coordinates'] == [36.8219, 1.2921]
    assert geojson_features[0]['properties']['id'] == 'user1'
    assert geojson_features[0]['properties']['country'] == 'Kenya'
    assert geojson_features[0]['properties']['gender'] == 'female'
    assert geojson_features[0]['properties']['is_graduate'] == True
    assert geojson_features[0]['properties']['is_employed'] == False
    assert geojson_features[0]['properties']['is_entrepreneur'] == True
    
    # Check second feature
    assert geojson_features[1]['geometry']['coordinates'] == [8.6753, 9.0820]
    assert geojson_features[1]['properties']['country'] == 'Nigeria'
    assert geojson_features[1]['properties']['gender'] == 'male'

def test_convert_to_geojson_missing_coordinates():
    """Test converting point with missing coordinates"""
    invalid_point = {
        'hashed_email': 'user3',
        'country_of_residence': 'Ghana',
        # Missing latitude and longitude
        'gender': 'male'
    }
    
    # Call function
    geojson_features = convert_to_geojson([invalid_point])
    
    # Verify no features are generated for invalid points
    assert len(geojson_features) == 0

def test_generate_filter_key():
    """Test generating a filter key for caching"""
    # Test with no filters
    assert generate_filter_key({}) == "all"
    
    # Test with single filter
    assert generate_filter_key({'gender': 'male'}) == "gender=male"
    
    # Test with multiple filters
    filters = {
        'gender': 'female',
        'is_graduate_learner': True,
        'country_of_residence': 'Kenya'
    }
    expected_key = "country_of_residence=Kenya_gender=female_is_graduate_learner=1"
    assert generate_filter_key(filters) == expected_key
    
    # Test with boolean filters
    bool_filters = {
        'is_graduate_learner': True,
        'is_wage_employed': False
    }
    expected_bool_key = "is_graduate_learner=1_is_wage_employed=0"
    assert generate_filter_key(bool_filters) == expected_bool_key