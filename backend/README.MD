
# SuperCluster Backend

A FastAPI implementation of geospatial clustering with database integration. This backend handles efficient spatial data retrieval, clustering, and filtering for visualization on maps.

## System Overview

The backend follows this data flow:
1. Loads geospatial point data from the database
2. Converts data to GeoJSON format and caches it in memory
3. Creates filtered spatial indexes using SuperCluster
4. Serves clustered data via API endpoints based on viewport and zoom level

## Core Components

### Index Manager

The `IndexManager` class is the heart of the system, responsible for:
- Loading data from the database
- Converting to GeoJSON format
- Creating and caching SuperCluster indexes based on filter combinations
- Memory management and garbage collection

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Database    │ ──> │ GeoJSON Cache│ ──> │ SuperCluster    │
│ (Raw Points)│     │              │     │ Indexes (by     │
└─────────────┘     └──────────────┘     │ filter key)     │
                                         └─────────────────┘
```

The system loads all data at startup (no filter key = "all") and keeps this in memory for fast filtering operations. Filtered subsets are created on demand and cached for repeated use.

### FastAPI Endpoints

Main endpoints:
- `/api/getClusters` - Get clustered points for a bounding box and zoom level
- `/api/stats` - Get memory usage and cache statistics
- `/api/clearCache` - Clear the index cache
- `/api/availableFilters` - Get information about available filters

## Data Flow

1. **Startup**: The system preloads all data:
   ```
   DB Query → SQL Results → GeoJSON Conversion → SuperCluster Index Creation
   ```

2. **Request Handling**:
   ```
   Client Request with filters → Filter key generation → 
   Cache lookup → (If miss) Filter data → Create index → 
   Get clusters for viewport → Return GeoJSON features
   ```

3. **Memory Management**:
   - Original SQL data is deleted after GeoJSON conversion
   - Garbage collection is triggered to free memory
   - GeoJSON data is kept for fast filtering

## API Endpoints and Schema

### GET /api/getClusters

Get clusters for a specific bounding box and zoom level with optional filters.

**Parameters**:
- `west`, `south`, `east`, `north`: Bounding box coordinates (float)
- `zoom`: Zoom level (int)
- Filter parameters:
  - `gender`: Filter by gender (string)
  - `country_of_residence`: Filter by country (string)
  - `is_graduate_learner`: Filter by graduate status (boolean)
  - `is_wage_employed`: Filter by employment status (boolean)
  - `is_running_a_venture`: Filter by entrepreneurship status (boolean)
  - `is_featured`: Filter by featured status (boolean)
  - `is_featured_video`: Filter by featured video status (boolean)

**Response**:
```json
{
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "cluster": true,  // For clusters
        "cluster_id": "string",
        "point_count": 123,
        "point_count_abbreviated": 123,
        "expansion_zoom": 10
        // OR individual point properties for non-clusters
      }
    }
  ]
}
```

### GET /api/stats

Get memory usage and cache statistics.

**Response**:
```json
{
  "cache_hits": 10,
  "cache_misses": 5,
  "cached_indexes": 3,
  "cache_ratio": "0.67",
  "current_memory_mb": "1234.56",
  "memory_history": [...],
  "object_memory": {
    "geojson_cache_size_mb": 1000.0,
    "indexes_size_mb": 200.0,
    "geojson_entries": {
      "all": {
        "size_mb": 1000.0,
        "feature_count": 1000000
      }
    }
  }
}
```

### POST /api/clearCache

Clear the index cache.

**Response**:
```json
{
  "status": "success",
  "message": "Cache cleared successfully"
}
```

### GET /api/availableFilters

Get information about available filters.

**Response**:
```json
{
  "genders": ["male", "female", "other", "unknown"],
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
```

## Configuration Options

### SuperCluster Options

The SuperCluster algorithm accepts these parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| min_zoom | Minimum zoom level at which clusters are generated | 0 |
| max_zoom | Maximum zoom level at which clusters are generated | 16 |
| radius | Cluster radius in pixels | 40 |
| extent | Tile extent in pixels (radius is calculated relative to this value) | 512 |

In non-technical terms:
- **min_zoom/max_zoom**: Control when points start grouping together (low zoom) and when they appear individually (high zoom)
- **radius**: How close points need to be to form a cluster (larger radius = more grouping)
- **extent**: Technical parameter that affects how the map is divided into tiles

## Memory Usage

The current implementation requires approximately 2GB of RAM to load and cache the full dataset. Memory usage breaks down as:
- ~1.4GB for GeoJSON cache
- ~0.6GB for SuperCluster indexes and runtime overhead

## TODO: GeoPandas Integration

Future work should focus on reducing memory usage by implementing GeoPandas:

1. **Replace GeoJSON with GeoPandas DataFrame**:
   ```python
   import geopandas as gpd
   from shapely.geometry import Point
   
   def convert_to_geodataframe(points):
       geometries = [Point(p['longitude'], p['latitude']) for p in points]
       return gpd.GeoDataFrame(points, geometry=geometries)
   ```

2. **Benefits expected**:
   - 40-60% memory reduction (estimated 800MB vs current 2GB)
   - Faster spatial operations using rtree spatial indexing
   - More efficient filtering using DataFrame operations
   - Type optimization with categoricals for string columns

3. **Implementation steps**:
   - Update IndexManager to store GeoDataFrames instead of GeoJSON
   - Modify filtering logic to use GeoPandas operations
   - Update conversion to SuperCluster format
   - Test with large datasets to verify memory improvements

4. **Memory optimization techniques**:
   - Convert string columns to categorical data type
   - Use efficient dtypes (int8, float32) where appropriate
   - Implement chunked processing for very large datasets

This optimization should improve both memory efficiency and query performance, making the backend more scalable for larger datasets.