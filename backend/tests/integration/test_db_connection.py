#!/usr/bin/env python3
"""
Integration test for database connection
Tests retrieving and validating data from impact_learners_profile table
"""
import sys
import os
import json
from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor
import pytest

# Add parent directory to path to import the modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables from .env.local file in the project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env.local')
load_dotenv(env_path)

def get_db_connection():
    """
    Establish a connection to the database using environment variables
    """
    # Determine if SSL should be used based on environment variable
    use_ssl = os.getenv('DATABASE_SSL', 'true').lower() == 'true'
    ssl_config = None
    if use_ssl:
        ssl_config = {'ca': None}  # Use system default CA certificates
    
    return pymysql.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        user=os.getenv('DATABASE_USER', 'root'),
        password=os.getenv('DATABASE_PASSWORD', ''),
        database=os.getenv('DATABASE_NAME', ''),
        port=int(os.getenv('DATABASE_PORT', '3306')),
        charset='utf8mb4',
        cursorclass=DictCursor,
        ssl=ssl_config
    )

@pytest.fixture
def db_connection():
    """Fixture to provide a database connection for tests"""
    connection = get_db_connection()
    yield connection
    connection.close()

def test_database_connection(db_connection):
    """Test that we can connect to the database"""
    # Simply test that the connection is established
    assert db_connection.open, "Database connection should be open"

def test_retrieve_learner_data(db_connection):
    """Test retrieving data from impact_learners_profile table"""
    with db_connection.cursor() as cursor:
        # Query to retrieve 10 rows from impact_learners_profile with valid coordinates
        query = """
            SELECT 
                hashed_email,
                full_name,
                country_of_residence,
                round(meta_ui_lat, 5) as latitude,
                round(meta_ui_lng, 5) as longitude,
                gender,
                is_graduate_learner,
                is_wage_employed,
                is_running_a_venture,
                is_featured,
                is_featured_video
            FROM
                impact_learners_profile
            WHERE
                has_data = 1
                AND meta_ui_lat IS NOT NULL
                AND meta_ui_lng IS NOT NULL
            LIMIT 10
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Assertions to validate the data
        assert len(results) > 0, "Should retrieve at least one row"
        assert len(results) <= 10, "Should not retrieve more than 10 rows"
        
        # Verify structure of the returned data
        for row in results:
            assert 'hashed_email' in row, "Each row should have a hashed_email"
            assert 'latitude' in row, "Each row should have latitude"
            assert 'longitude' in row, "Each row should have longitude"
            
            # Validate coordinate data
            assert isinstance(row['latitude'], float), "Latitude should be a float"
            assert isinstance(row['longitude'], float), "Longitude should be a float"
            assert -90 <= row['latitude'] <= 90, "Latitude should be between -90 and 90"
            assert -180 <= row['longitude'] <= 180, "Longitude should be between -180 and 180"
            
            # Check that boolean fields are of correct type (could be 0/1 integers in MySQL)
            if row['is_graduate_learner'] is not None:
                assert row['is_graduate_learner'] in (0, 1), "is_graduate_learner should be 0 or 1"
            
            if row['is_featured'] is not None:
                assert row['is_featured'] in (0, 1), "is_featured should be 0 or 1"

def test_data_formatting(db_connection):
    """Test data formatting functions by validating a sample row"""
    with db_connection.cursor() as cursor:
        query = """
            SELECT 
                hashed_email,
                full_name,
                country_of_residence,
                round(meta_ui_lat, 5) as latitude,
                round(meta_ui_lng, 5) as longitude
            FROM
                impact_learners_profile
            WHERE
                has_data = 1
                AND meta_ui_lat IS NOT NULL
                AND meta_ui_lng IS NOT NULL
            LIMIT 1
        """
        
        cursor.execute(query)
        row = cursor.fetchone()
        
        # Test that we can format data correctly
        assert row is not None, "Should retrieve at least one row"
        
        # Create a GeoJSON-like point to test formatting
        point = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row['longitude'], row['latitude']]
            },
            "properties": {
                "hashed_email": row['hashed_email'],
                "full_name": row['full_name'],
                "country_of_residence": row['country_of_residence']
            }
        }
        
        # Verify the structure of our test point
        assert point["type"] == "Feature", "Should be a GeoJSON Feature"
        assert point["geometry"]["type"] == "Point", "Should be a Point geometry"
        assert len(point["geometry"]["coordinates"]) == 2, "Should have longitude and latitude"
        assert point["properties"]["hashed_email"] == row['hashed_email'], "Should match source data"

if __name__ == "__main__":
    test_database_connection() 