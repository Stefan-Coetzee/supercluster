import sys
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import time
import logging
import gc
import psutil
import traceback

# Add the pysupercluster directory to the path so we can import it
sys.path.append(os.path.join(os.path.dirname(__file__), "pysupercluster"))
import pysupercluster

from db import load_learner_points, convert_to_geojson, generate_filter_key

# Configure logging
logger = logging.getLogger(__name__)

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024  # Convert to MB

class IndexManager:
    """
    Manager for creating and caching supercluster indexes based on filter combinations
    """
    def __init__(self, min_zoom=0, max_zoom=16, radius=40, extent=512):
        """
        Initialize the index manager
        
        Args:
            min_zoom: Minimum zoom level for clustering
            max_zoom: Maximum zoom level for clustering
            radius: Cluster radius in pixels
            extent: Tile extent in pixels
        """
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.radius = radius
        self.extent = extent
        
        # Cache for indexes based on filter combinations
        self.indexes = {}
        
        # Cache for GeoJSON data
        self.geojson_cache = {}
        
        # Track when indexes were last accessed
        self.last_accessed = {}
        
        # Stats
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Memory usage tracking
        self.memory_usage = []
        initial_memory = get_memory_usage()
        self.memory_usage.append({"timestamp": time.time(), "memory_mb": initial_memory, "event": "init"})
        logger.info(f"IndexManager initialized. Initial memory usage: {initial_memory:.2f} MB")
    
    def get_index(self, filters: Optional[Dict[str, Any]] = None, force_refresh: bool = False):
        # Generate key for caching
        index_key = generate_filter_key(filters)
        
        # Check cache first
        if index_key in self.indexes and not force_refresh:
            logger.debug(f"Cache hit for {index_key}")
            return index_key, self.indexes[index_key]
        
        # If all data is already loaded and we need a filtered subset
        if self.geojson_cache.get("all") and filters:
            # Filter the in-memory GeoJSON
            logger.debug(f"Filtering in-memory data for {index_key}")
            filtered_geojson = self._filter_geojson(self.geojson_cache["all"], filters)
            
            # Create new index from filtered data
            points_array = self._extract_coordinates(filtered_geojson)
            index = self._create_supercluster_index(points_array)
            
            # Cache results
            self.indexes[index_key] = index
            self.geojson_cache[index_key] = filtered_geojson
            
            return index_key, index
        
        # Cache miss - need to create a new index
        logger.info(f"Cache miss for index key: {index_key}. Creating new index...")
        self.cache_misses += 1
        
        # Record pre-load memory
        pre_memory = get_memory_usage()
        self.memory_usage.append({"timestamp": time.time(), "memory_mb": pre_memory, "event": f"pre_load_{index_key}"})
        logger.debug(f"Memory before loading data: {pre_memory:.2f} MB")
        
        try:
            # Load filtered data from database
            start_time = time.time()
            db_points = load_learner_points(filters=filters)
            db_time = time.time() - start_time
            logger.info(f"Loaded {len(db_points)} points from database in {db_time:.2f} seconds")
            
            # Record post-db load memory
            post_db_memory = get_memory_usage()
            self.memory_usage.append({"timestamp": time.time(), "memory_mb": post_db_memory, "event": f"post_db_load_{index_key}"})
            logger.debug(f"Memory after DB load: {post_db_memory:.2f} MB (increase: {post_db_memory - pre_memory:.2f} MB)")
            
            # Convert to GeoJSON
            start_time = time.time()
            geojson_features = convert_to_geojson(db_points)
            self.geojson_cache[index_key] = geojson_features
            geojson_time = time.time() - start_time
            logger.info(f"Converted to {len(geojson_features)} GeoJSON features in {geojson_time:.2f} seconds")
            
            # Record post-geojson memory
            post_geojson_memory = get_memory_usage()
            self.memory_usage.append({"timestamp": time.time(), "memory_mb": post_geojson_memory, "event": f"post_geojson_{index_key}"})
            logger.debug(f"Memory after GeoJSON conversion: {post_geojson_memory:.2f} MB (increase: {post_geojson_memory - post_db_memory:.2f} MB)")
            
            # Free up some memory
            del db_points
            gc.collect()
            
            # Extract coordinates for supercluster
            start_time = time.time()
            points_array = self._extract_coordinates(geojson_features)
            extract_time = time.time() - start_time
            logger.info(f"Extracted coordinates in {extract_time:.2f} seconds")
            
            # Create supercluster index
            start_time = time.time()
            index = self._create_supercluster_index(points_array)
            index_time = time.time() - start_time
            logger.info(f"Created SuperCluster index in {index_time:.2f} seconds")
            
            # Record post-index memory
            post_index_memory = get_memory_usage()
            self.memory_usage.append({"timestamp": time.time(), "memory_mb": post_index_memory, "event": f"post_index_{index_key}"})
            logger.debug(f"Memory after index creation: {post_index_memory:.2f} MB (increase: {post_index_memory - post_geojson_memory:.2f} MB)")
            
            # Cache the index
            self.indexes[index_key] = index
            self.last_accessed[index_key] = time.time()
            
            return index_key, index
            
        except Exception as e:
            error_message = f"Error creating index for key {index_key}: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            raise Exception(error_message)
    
    def _extract_coordinates(self, geojson_features: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract coordinates from GeoJSON features for supercluster
        
        Args:
            geojson_features: List of GeoJSON Feature objects
            
        Returns:
            Numpy array of coordinates in the format expected by pysupercluster
        """
        start_time = time.time()
        points = []
        for feature in geojson_features:
            coords = feature["geometry"]["coordinates"]
            points.append((coords[0], coords[1]))  # (longitude, latitude)
        
        points_array = np.array(points)
        extract_time = time.time() - start_time
        logger.debug(f"Extracted {len(points)} coordinates into numpy array in {extract_time:.4f} seconds")
        
        return points_array
    
    def _create_supercluster_index(self, points_array: np.ndarray):
        """
        Create a supercluster index from a numpy array of points
        
        Args:
            points_array: Numpy array of points in format [(longitude, latitude), ...]
            
        Returns:
            SuperCluster index
        """
        if len(points_array) == 0:
            logger.warning("Creating index with empty points array")
            
        start_time = time.time()
        index = pysupercluster.SuperCluster(
            points_array,
            min_zoom=self.min_zoom,
            max_zoom=self.max_zoom,
            radius=self.radius,
            extent=self.extent
        )
        index_time = time.time() - start_time
        logger.info(f"Created SuperCluster index with {len(points_array)} points in {index_time:.2f} seconds")
        
        return index
    
    def get_original_features(self, index_key: str) -> List[Dict[str, Any]]:
        """
        Get the original GeoJSON features for an index key
        
        Args:
            index_key: The filter key for the index
            
        Returns:
            List of original GeoJSON features
        """
        if index_key in self.geojson_cache:
            logger.debug(f"Returning {len(self.geojson_cache[index_key])} cached GeoJSON features for key: {index_key}")
            return self.geojson_cache[index_key]
        logger.warning(f"No cached GeoJSON features found for key: {index_key}")
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_memory = get_memory_usage()
        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cached_indexes": len(self.indexes),
            "cache_ratio": f"{self.cache_hits/(self.cache_hits + self.cache_misses):.2f}" if (self.cache_hits + self.cache_misses) > 0 else "N/A",
            "current_memory_mb": f"{current_memory:.2f}",
            "memory_history": self.memory_usage
        }
        logger.debug(f"Current memory usage: {current_memory:.2f} MB")
        return stats
    
    def clear_cache(self) -> None:
        """Clear all cached indexes"""
        pre_clear_memory = get_memory_usage()
        
        self.indexes = {}
        self.geojson_cache = {}
        self.last_accessed = {}
        
        # Force garbage collection
        gc.collect()
        
        post_clear_memory = get_memory_usage()
        memory_freed = pre_clear_memory - post_clear_memory
        
        self.memory_usage.append({
            "timestamp": time.time(), 
            "memory_mb": post_clear_memory, 
            "event": "cache_clear",
            "memory_freed_mb": memory_freed
        })
        
        logger.info(f"Cleared index cache. Memory freed: {memory_freed:.2f} MB")

    def _filter_geojson(self, geojson_features, filters):
        """Filter GeoJSON features based on filter criteria"""
        if not filters:
            return geojson_features
            
        filtered = []
        for feature in geojson_features:
            properties = feature["properties"]
            include = True
            
            for key, value in filters.items():
                if key == "gender" or key == "country_of_residence":
                    if properties.get(key) != value:
                        include = False
                        break
                elif key in ["is_graduate_learner", "is_wage_employed", 
                             "is_running_a_venture", "is_featured", "is_featured_video"]:
                    if bool(properties.get(key)) != bool(value):
                        include = False
                        break
            
            if include:
                filtered.append(feature)
                
        logger.info(f"Filtered {len(geojson_features)} features to {len(filtered)}")
        return filtered

# Global index manager instance
index_manager = IndexManager() 