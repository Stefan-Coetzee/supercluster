# SuperCluster FastAPI Service with Database Integration

A FastAPI implementation of geospatial clustering with MySQL database integration, following the schema of the original [Mapbox Supercluster](https://github.com/mapbox/supercluster) JavaScript library.

## Features

- Load geospatial data directly from MySQL database
- Convert database records to GeoJSON format for clustering
- Filter data by various criteria (gender, country, employment status, etc.)
- Cache supercluster indexes for each filter combination for faster responses
- Dynamically build and manage indexes based on filter combinations
- Full compatibility with the original Supercluster API

## Setup

1. Clone this repository and the pysupercluster dependency:
```bash
git clone https://github.com/wemap/pysupercluster.git
```

2. Create a virtual environment and install dependencies using uv:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
cd pysupercluster && uv pip install -e . && cd ..
```

3. Configure database connection:
```bash
cp .env.sample .env
# Edit .env with your database credentials
```

## Running the API

Start the FastAPI server:
```bash
./start_server.sh
```

The API will be available at: http://localhost:8000

API documentation is automatically available at: http://localhost:8000/docs

## Database Integration

The service connects to a MySQL database and loads data from the `impact_learners_profile` table. The database schema is designed to store information about learners with geographical coordinates, allowing the service to create dynamic clustering based on various filters.

### Database Schema

The primary table used is `impact_learners_profile` with the following key fields:
- `hashed_email`: Unique identifier for each learner
- `country_of_residence`: Country where the learner resides
- `meta_ui_lat` and `meta_ui_lng`: Coordinates for visualization
- Various boolean flags for filtering:
  - `is_graduate_learner`: Whether the learner has graduated
  - `is_wage_employed`: Whether the learner is employed
  - `is_running_a_venture`: Whether the learner is running a business
  - `is_featured`: Whether the learner is featured
  - `is_featured_video`: Whether the learner has a featured video

## API Endpoints

The API provides the following main endpoints:

- `GET /` - Root endpoint with API information
- `POST /api/buildIndex` - Build and cache an index with optional filters
- `POST /api/getClusters` - Get clusters for a specific bounding box and zoom level
- `GET /api/stats` - Get cache statistics
- `POST /api/clearCache` - Clear the index cache
- `GET /api/availableFilters` - Get information about available filters

## Example Usage

Build an index with no filters:
```bash
curl -X POST http://localhost:8000/api/buildIndex \
  -H "Content-Type: application/json" \
  -d '{}'
```

Build an index with gender filter:
```bash
curl -X POST http://localhost:8000/api/buildIndex \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "gender": "Female",
      "is_graduate_learner": true
    }
  }'
```

Get clusters:
```bash
curl -X POST http://localhost:8000/api/getClusters \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [-180, -85, 180, 85],
    "zoom": 4,
    "indexKey": "gender=Female_is_graduate_learner=1"
  }'
```

## Performance Considerations

The service implements several optimizations to handle large datasets:

1. **Caching**: Supercluster indexes are cached by filter combination
2. **Lazy Loading**: Indexes are created only when needed
3. **GeoJSON Caching**: Original features are cached alongside indexes to preserve properties
4. **Efficient DB Queries**: Queries include only necessary fields and include filters

## Options

The clustering options match the original Supercluster library:

| Option     | Default | Description                                                       |
| ---------- | ------- | ----------------------------------------------------------------- |
| minZoom    | 0       | Minimum zoom level at which clusters are generated.               |
| maxZoom    | 16      | Maximum zoom level at which clusters are generated.               |
| radius     | 40      | Cluster radius, in pixels.                                        |
| extent     | 512     | (Tiles) Tile extent. Radius is calculated relative to this value. |

## Testing

Run the included test script to verify the API is working correctly:
```bash
./run_test.sh 