import pymysql
import os
import logging
import time
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set default data limit (for preloading)
DEFAULT_DATA_LIMIT = 1000 # Limit to 10k rows instead of all 1.4M

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', 'localhost'),
    'user': os.getenv('DATABASE_USER', 'root'),
    'password': os.getenv('DATABASE_PASSWORD', ''),
    'database': os.getenv('DATABASE_NAME', ''),
    'port': int(os.getenv('DATABASE_PORT', '3306')),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_connection():
    """Get a database connection"""
    logger.debug(f"Establishing database connection to {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def execute_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """Execute a database query and return the results"""
    start_time = time.time()
    connection = None
    
    try:
        logger.debug(f"Executing query: {query}")
        logger.debug(f"Query params: {params}")
        
        connection = get_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            
            query_time = time.time() - start_time
            logger.debug(f"Query executed in {query_time:.4f} seconds, returned {len(result)} rows")
            
            return result
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise
    finally:
        if connection:
            connection.close()
            logger.debug("Database connection closed")

def load_learner_points(limit: Optional[int] = None, offset: int = 0, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Load learner points from the database with optional filtering
    
    Args:
        limit: Maximum number of points to return
        offset: Offset for pagination
        filters: Dictionary of filter key-value pairs
        
    Returns:
        List of learner point dictionaries
    """
    # Use default limit if not specified
    if limit is None:
        limit = DEFAULT_DATA_LIMIT
        logger.info(f"Using default limit of {DEFAULT_DATA_LIMIT} rows")
    
    logger.info(f"Loading learner points with filters: {filters}")
    logger.debug(f"Query parameters - limit: {limit}, offset: {offset}")
    
    # Start with base query
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
            meta_ui_lat IS NOT NULL
            AND meta_ui_lng IS NOT NULL
    """
    
    params = []
    
    # Apply filters if provided
    if filters:
        for key, value in filters.items():
            if key in ['gender', 'country_of_residence']:
                query += f" AND {key} = %s"
                params.append(value)
                logger.debug(f"Added filter: {key} = {value}")
            elif key in ['is_graduate_learner', 'is_wage_employed', 'is_running_a_venture', 
                         'is_featured', 'is_featured_video']:
                query += f" AND {key} = %s"
                params.append(1 if value else 0)
                logger.debug(f"Added filter: {key} = {1 if value else 0}")
    
    # Add limit and offset
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    # Execute query
    start_time = time.time()
    results = execute_query(query, tuple(params))
    query_time = time.time() - start_time
    
    logger.info(f"Loaded {len(results)} learner points in {query_time:.4f} seconds")
    return results

def convert_to_geojson(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert database points to GeoJSON format
    
    Args:
        points: List of learner points from the database
        
    Returns:
        List of GeoJSON Feature objects
    """
    features = []
    
    for point in points:
        # Skip points without valid coordinates
        if not point.get('latitude') or not point.get('longitude'):
            continue
            
        # Create GeoJSON Feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(point['longitude']), float(point['latitude'])]
            },
            "properties": {
                "id": point.get('hashed_email', ''),
                "country": point.get('country_of_residence', ''),
                "gender": point.get('gender', ''),
                "is_graduate": bool(point.get('is_graduate_learner', 0)),
                "is_employed": bool(point.get('is_wage_employed', 0)),
                "is_entrepreneur": bool(point.get('is_running_a_venture', 0)),
                "is_featured": bool(point.get('is_featured', 0)),
                "has_video": bool(point.get('is_featured_video', 0))
            }
        }
        
        features.append(feature)
    
    return features

def generate_filter_key(filters: Dict[str, Any]) -> str:
    """
    Generate a unique key for a set of filters
    
    Args:
        filters: Dictionary of filter key-value pairs
        
    Returns:
        Unique string key for the filter combination
    """
    if not filters:
        return "all"
        
    parts = []
    for key in sorted(filters.keys()):
        value = filters[key]
        if isinstance(value, bool):
            value = 1 if value else 0
        parts.append(f"{key}={value}")
    
    return "_".join(parts) 