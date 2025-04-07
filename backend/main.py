#FastAPI implementation of supercluster

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Tuple, Dict, Optional, Any, Union
import numpy as np
import sys
import os
import logging
import time
from fastapi.middleware.cors import CORSMiddleware
import traceback

# Add the pysupercluster directory to the path so we can import it
sys.path.append(os.path.join(os.path.dirname(__file__), "pysupercluster"))
import pysupercluster

# Use relative imports for local modules
from index_manager import index_manager
from db import convert_to_geojson, generate_filter_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SuperCluster API",
    description="A FastAPI implementation of geospatial clustering with database integration",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preload data at startup
@app.on_event("startup")
async def startup_event():
    """Preload ALL data at startup and keep in memory"""
    logger.info("Starting application, preloading all data...")
    try:
        start_time = time.time()
        # Force loading all data without filtering
        index_key, _ = index_manager.get_index({})
        elapsed = time.time() - start_time
        logger.info(f"Preloaded all data with key: {index_key} in {elapsed:.2f} seconds")
        
        # Log memory usage
        memory_stats = index_manager.get_stats()
        logger.info(f"Memory usage after preload: {memory_stats['current_memory_mb']} MB")
    except Exception as e:
        logger.error(f"Error during preloading: {str(e)}")
        logger.error(traceback.format_exc())

class GeoPoint(BaseModel):
    """GeoJSON-compatible point representation"""
    type: str = Field("Feature", description="GeoJSON type")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON Point geometry")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Point properties")
    id: Optional[Union[int, str]] = Field(None, description="Optional Feature ID")

class FilterOptions(BaseModel):
    """Filter options for the data"""
    gender: Optional[str] = Field(None, description="Filter by gender")
    country_of_residence: Optional[str] = Field(None, description="Filter by country")
    is_graduate_learner: Optional[bool] = Field(None, description="Filter by graduate status")
    is_wage_employed: Optional[bool] = Field(None, description="Filter by employment status")
    is_running_a_venture: Optional[bool] = Field(None, description="Filter by entrepreneurship status")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")
    is_featured_video: Optional[bool] = Field(None, description="Filter by featured video status")

class ClusterOptions(BaseModel):
    """Options for creating a supercluster index"""
    minZoom: int = Field(0, description="Minimum zoom level at which clusters are generated")
    maxZoom: int = Field(16, description="Maximum zoom level at which clusters are generated")
    minPoints: int = Field(10, description="Minimum number of points to form a cluster")
    radius: int = Field(40, description="Cluster radius, in pixels")
    extent: int = Field(512, description="Tile extent. Radius is calculated relative to this value")
    nodeSize: int = Field(64, description="Size of the KD-tree leaf node. Affects performance")
    log: bool = Field(False, description="Whether timing info should be logged")
    generateId: bool = Field(False, description="Whether to generate ids for input features in vector tiles")

class BBox(BaseModel):
    """Bounding box [westLng, southLat, eastLng, northLat]"""
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="Bounding box [westLng, southLat, eastLng, northLat]")
    zoom: int = Field(..., description="Zoom level")

class ClusterRequest(BaseModel):
    """Combined request model for getting clusters"""
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="Bounding box [westLng, southLat, eastLng, northLat]")
    zoom: int = Field(..., description="Zoom level")
    filters: Optional[FilterOptions] = Field(None, description="Optional filter criteria")

class ClusterResponse(BaseModel):
    """Response containing GeoJSON features for clusters and points"""
    features: List[Dict[str, Any]] = Field(..., description="List of GeoJSON features")

class TileRequest(BaseModel):
    """Request for a tile at specific coordinates"""
    z: int = Field(..., description="Zoom level")
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")

class ClusterIdRequest(BaseModel):
    """Request for a specific cluster by ID"""
    clusterId: str = Field(..., description="Cluster ID")

class ClusterLeavesRequest(BaseModel):
    """Request for the leaves of a cluster"""
    clusterId: str = Field(..., description="Cluster ID") 
    limit: int = Field(10, description="Number of points to return")
    offset: int = Field(0, description="Number of points to skip")

# In-memory storage for supercluster indexes
supercluster_indexes = {}

def convert_to_geojson_point(point, idx):
    """Convert a (longitude, latitude) tuple to a GeoJSON Point feature"""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [point[0], point[1]]
        },
        "properties": {},
        "id": idx
    }

def extract_points_from_geojson(features):
    """Extract (longitude, latitude) points from GeoJSON features"""
    points = []
    for feature in features:
        # Handle both Pydantic model and dictionary
        if hasattr(feature, 'model_dump'):
            feature_dict = feature.model_dump()
        elif hasattr(feature, 'dict'):
            # For backward compatibility with older Pydantic
            feature_dict = feature.dict()
        else:
            feature_dict = feature
            
        if feature_dict["geometry"]["type"] == "Point":
            coords = feature_dict["geometry"]["coordinates"]
            points.append((coords[0], coords[1]))  # (longitude, latitude)
    return np.array(points)

@app.post("/api/load/{index_id}", response_model=Dict[str, Any])
async def load_points(index_id: str, features: List[Dict[str, Any]], options: ClusterOptions = None):
    """Load an array of GeoJSON Feature objects with Point geometry"""
    if options is None:
        options = ClusterOptions()
    
    # Extract points from GeoJSON features
    points_array = extract_points_from_geojson(features)
    
    try:
        # Create the supercluster index
        index = pysupercluster.SuperCluster(
            points_array,
            min_zoom=options.minZoom,
            max_zoom=options.maxZoom,
            radius=options.radius,
            extent=options.extent
        )
        
        # Store the index for future use
        supercluster_indexes[index_id] = {
            "index": index,
            "features": features,  # Store original features to preserve properties
            "options": options.model_dump() if hasattr(options, 'model_dump') else (
                options.dict() if hasattr(options, 'dict') else options
            )
        }
        
        return {"status": "success", "indexId": index_id, "numPoints": len(features)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating index: {str(e)}")

@app.post("/api/getClusters", response_model=ClusterResponse)
async def get_clusters(request: ClusterRequest):
    """
    Get clusters for a specific bounding box and zoom level with optional filters
    """
    start_time = time.time()
    
    # Convert filters to dict, removing None values
    filter_dict = {}
    if request.filters:
        if hasattr(request.filters, 'model_dump'):
            filter_dict = {k: v for k, v in request.filters.model_dump().items() if v is not None}
        else:
            # For backward compatibility
            filter_dict = {k: v for k, v in request.filters.dict().items() if v is not None}
    
    try:
        # Get or create filtered index (now uses in-memory filtering)
        index_key, index = index_manager.get_index(filter_dict)
        
        bbox = request.bbox
        zoom = request.zoom
        
        # Convert bbox from [westLng, southLat, eastLng, northLat] to format expected by pysupercluster
        top_left = (bbox[0], bbox[3])  # (west, north)
        bottom_right = (bbox[2], bbox[1])  # (east, south)
        
        # Time the cluster generation
        cluster_start = time.time()
        clusters = index.getClusters(top_left=top_left, bottom_right=bottom_right, zoom=zoom)
        cluster_time = time.time() - cluster_start
        logger.info(f"Generated clusters in {cluster_time:.4f} seconds")
        
        # Convert to GeoJSON format
        geojson_features = []
        original_features = index_manager.get_original_features(index_key)
        
        for cluster in clusters:
            if 'count' in cluster and cluster['count'] > 1:
                # This is a cluster
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [cluster['longitude'], cluster['latitude']]
                    },
                    "properties": {
                        "cluster": True,
                        "cluster_id": str(cluster['id']),
                        "point_count": cluster['count'],
                        "point_count_abbreviated": cluster['count'],
                        "expansion_zoom": cluster['expansion_zoom'] if cluster['expansion_zoom'] is not None else None
                    }
                }
                geojson_features.append(feature)
            else:
                # This is a single point
                # Find the original feature to preserve properties
                original_idx = cluster['id']
                
                if original_idx < len(original_features):
                    # Use the original feature with all its properties
                    geojson_features.append(original_features[original_idx])
                else:
                    # Fallback if we can't find the original
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [cluster['longitude'], cluster['latitude']]
                        },
                        "properties": {
                            "id": str(cluster['id'])
                        }
                    }
                    geojson_features.append(feature)
        
        elapsed = time.time() - start_time
        logger.info(f"Total getClusters request time: {elapsed:.4f} seconds")
        
        return ClusterResponse(features=geojson_features)
    except Exception as e:
        logger.error(f"Error getting clusters: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting clusters: {str(e)}")

@app.post("/api/getClusterExpansionZoom/{index_id}", response_model=Dict[str, Any])
async def get_cluster_expansion_zoom(index_id: str, request: ClusterIdRequest):
    """Get the zoom level at which a cluster expands"""
    if index_id not in supercluster_indexes:
        raise HTTPException(status_code=404, detail=f"Index with ID {index_id} not found")
    
    try:
        # In pysupercluster, the expansion_zoom is already calculated when getClusters is called
        # We can find the cluster and return its expansion_zoom
        cluster_id = int(request.clusterId)
        
        # This is a simplified implementation as pysupercluster doesn't have this method directly
        # We would need to implement logic to find a specific cluster by ID
        # For now, return a mock response
        return {
            "expansion_zoom": 10  # Mock value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cluster expansion zoom: {str(e)}")

@app.post("/api/getChildren/{index_id}", response_model=ClusterResponse)
async def get_children(index_id: str, request: ClusterIdRequest):
    """Get the children of a cluster"""
    if index_id not in supercluster_indexes:
        raise HTTPException(status_code=404, detail=f"Index with ID {index_id} not found")
    
    # This would require additional implementation in pysupercluster
    # For now, return an empty response
    return ClusterResponse(features=[])

@app.post("/api/getLeaves/{index_id}", response_model=ClusterResponse)
async def get_leaves(index_id: str, request: ClusterLeavesRequest):
    """Get the points of a cluster with pagination"""
    if index_id not in supercluster_indexes:
        raise HTTPException(status_code=404, detail=f"Index with ID {index_id} not found")
    
    # This would require additional implementation in pysupercluster
    # For now, return an empty response
    return ClusterResponse(features=[])

@app.delete("/api/delete/{index_id}")
async def delete_index(index_id: str):
    """Delete a SuperCluster index"""
    if index_id not in supercluster_indexes:
        raise HTTPException(status_code=404, detail=f"Index with ID {index_id} not found")
    
    try:
        del supercluster_indexes[index_id]
        return {"status": "success", "message": f"Index {index_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting index: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SuperCluster API with Database Integration",
        "version": "0.1.0",
        "description": "FastAPI implementation of geospatial point clustering with database integration"
    }

@app.get("/api/stats")
async def get_stats():
    """Get supercluster cache statistics"""
    return index_manager.get_stats()

@app.post("/api/clearCache")
async def clear_cache():
    """Clear the supercluster index cache"""
    index_manager.clear_cache()
    return {"status": "success", "message": "Cache cleared successfully"}

@app.get("/api/availableFilters")
async def get_available_filters():
    """Get information about available filters"""
    return {
        "genders": ["male", "female", "other", "unknown"],  # Example values
        "filters": {
            "gender": "Filter by gender (e.g., Male, Female)",
            "country_of_residence": "Filter by country name",
            "is_graduate_learner": "Filter to only include graduates (true/false)",
            "is_wage_employed": "Filter to only include employed learners (true/false)",
            "is_running_a_venture": "Filter to only include entrepreneurs (true/false)",
            "is_featured": "Filter to only include featured learners (true/false)",
            "is_featured_video": "Filter to only include learners with featured videos (true/false)"
        }
    }

