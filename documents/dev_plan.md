# Development Plan: Scalable Mapbox Implementation

## Overview

This document outlines the implementation plan for a scalable Mapbox application that can efficiently handle approximately 2 million records. The application will use a multi-tiered approach to data visualization based on zoom levels:

1. **High Zoom (Choropleth)**: Country-level aggregated metrics from `impact_metrics`
2. **Mid Zoom (Clusters)**: Server-side clustered data from `impact_learners_profile`
3. **Low Zoom (Individual Points)**: Individual learner data with detailed profiles

## Architecture

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  impact_metrics │     │impact_learners_p│     │  Other Tables   │
│  (Aggregated)   │     │    rofile       │     │   (Details)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Layer (Next.js)                        │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐ │
│ │  /api/metrics   │ │  /api/clusters  │ │  /api/learner/[id]  │ │
│ │  (Choropleth)   │ │ (SuperCluster)  │ │  (Detail Profiles)  │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Mapbox Client                              │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐ │
│ │ Country Layer   │ │  Cluster Layer  │ │  Individual Points  │ │
│ │  (zoom 0-4)     │ │  (zoom 5-9)     │ │    (zoom 10+)       │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### 1. Backend API Development

#### 1.1 API Routes

Create the following API endpoints:

1. **`/api/metrics`**: Returns country-level metrics
   - Pulls data from `impact_metrics` table
   - Parameters: `metric_name`, `year` (optional)
   - Returns: GeoJSON with country polygons and associated metrics

2. **`/api/clusters`**:  Returns clustered data
   - Parameters: `bbox` (bounding box), `zoom`, `metric` (optional)
   - Uses SuperCluster to generate clusters from `impact_learners_profile`
   - Returns: GeoJSON with clusters and point counts

3. **`/api/learners`**: Returns individual learner points
   - Parameters: `bbox` (bounding box), `limit`, `offset`
   - Returns: GeoJSON with learner points within the viewport

4. **`/api/learner/[id]`**: Returns detailed profile for a specific learner
   - Parameters: `id` (learner's hashed_email)
   - Returns: Detailed profile information

#### 1.2 Data Models & Utils

Create the following utility modules:

1. **`lib/db.ts`**: Database connection utilities (simulated for now)
2. **`lib/supercluster.ts`**: Server-side clustering implementation
3. **`lib/geo-utils.ts`**: Utilities for GeoJSON manipulation 
4. **`lib/mock-data.ts`**: Mock data generator for development

### 2. Frontend Implementation

#### 2.1 Map Component Refactoring

Modify the existing map implementation to support multi-tiered visualization:

1. **`components/map/MapContainer.tsx`**: Main map container component
2. **`components/map/layers/ChoroplethLayer.tsx`**: Country-level visualization
3. **`components/map/layers/ClusterLayer.tsx`**: Cluster visualization
4. **`components/map/layers/PointLayer.tsx`**: Individual point visualization
5. **`components/map/InfoPanel.tsx`**: Updated info panel to display context-aware information

#### 2.2 State Management

Implement state management for the map:

1. **`lib/hooks/useMapData.ts`**: Custom hook to fetch and manage map data
2. **`lib/hooks/useMapZoom.ts`**: Handle zoom-level state and data loading
3. **`lib/hooks/useMapSelection.ts`**: Handle selection state for countries, clusters, and points

### 3. Data Simulation & Mocking

For initial development, create mock implementations:

1. **`lib/mocks/metrics.ts`**: Simulated country metrics data
2. **`lib/mocks/learners.ts`**: Simulated learner data
3. **`lib/mocks/clusters.ts`**: Pre-computed clusters at different zoom levels

### 4. Implementation Phases

#### Phase 1: Setup & Choropleth Layer

1. Create API route structure with mock data
2. Implement country-level choropleth layer
3. Test with mock metrics data
4. Implement InfoPanel for country-level data

#### Phase 2: Clustering Implementation

1. Implement SuperCluster on the server-side
2. Create clustering API endpoint
3. Implement cluster layer in the map
4. Add interaction for clusters (click to zoom)

#### Phase 3: Individual Points & Details

1. Implement points API endpoint
2. Create point layer for high-zoom levels
3. Implement detail view for individual learners
4. Connect infoPanel to display point details

#### Phase 4: Optimization & Refinement

1. Implement bounding box filtering for efficiency
2. Add caching for frequently requested data
3. Optimize clustering parameters
4. Implement progressive loading for points

## Data Model Changes

### GeoJSON Structure for Countries (Choropleth)

```typescript
// /api/metrics response
{
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "Polygon",
        coordinates: [/* country polygon */]
      },
      properties: {
        country_name: "Kenya",
        region_name: "East Africa",
        metric_name: "graduates",
        metric_value: 5000,
        year: 2023,
        // Additional metrics for tooltips/info display
        gender_distribution: { male: 60, female: 40 },
        placement_rate: 78
      }
    }
    // Additional country features
  ]
}
```

### GeoJSON Structure for Clusters

```typescript
// /api/clusters response
{
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [longitude, latitude]
      },
      properties: {
        cluster: true,
        cluster_id: 123,
        point_count: 456,
        // Expanded properties for info display
        region_name: "East Africa",
        countries: ["Kenya", "Uganda", "Tanzania"],
        metrics: {
          graduates: 3500,
          employed: 2800
        }
      }
    },
    // Additional cluster or individual point features
  ]
}
```

### GeoJSON Structure for Individual Points

```typescript
// /api/learners response (high zoom)
{
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [longitude, latitude]
      },
      properties: {
        id: "hashed_email_1",
        full_name: "John Doe",
        profile_photo_url: "https://example.com/photo.jpg",
        country_of_residence: "Kenya",
        city_of_residence: "Nairobi",
        gender: "Male",
        is_graduate_learner: 1,
        is_placed: 1
        // Limited properties for marker display
      }
    }
    // Additional learner points
  ]
}
```

## Technical Considerations

### Performance Optimization

1. **Server-side clustering**: Use SuperCluster on the server to pre-compute clusters
2. **Viewport filtering**: Only fetch data within the current map viewport
3. **Progressive loading**: Load data in chunks as the user pans/zooms
4. **Caching**: Implement client and server caching for commonly requested data
5. **Vector tiles**: Consider using vector tiles for very large datasets

### Mapbox Configuration

1. **Layer management**: Control layer visibility based on zoom level
2. **Custom styling**: Style clusters by size and composition
3. **Event handling**: Implement custom handlers for clicks, hovers
4. **3D effects**: Consider 3D extrusion for choropleth for visual impact

## Mock Implementation Details

For initial development, we'll create mock implementations that simulate API responses:

```typescript
// Example mock metrics API
export async function GET(request: Request) {
  // Parse query parameters
  const { searchParams } = new URL(request.url);
  const metric = searchParams.get('metric') || 'graduates';
  
  // Fetch country GeoJSON
  const countriesGeoJSON = await fetch(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
  ).then(res => res.json());
  
  // Add mock metrics to country features
  const enrichedFeatures = countriesGeoJSON.features.map(feature => {
    // Only add metrics to countries we have data for
    if (COUNTRIES_WITH_DATA.includes(feature.properties.name)) {
      feature.properties.metric_value = Math.floor(Math.random() * 10000);
      feature.properties.metric_name = metric;
      feature.properties.year = 2023;
    }
    return feature;
  }).filter(feature => COUNTRIES_WITH_DATA.includes(feature.properties.name));
  
  return Response.json({
    type: "FeatureCollection",
    features: enrichedFeatures
  });
}
```

## Next Steps

1. Begin implementation of API routes with mock data
2. Refactor map component to support multi-tier visualization
3. Implement server-side clustering with SuperCluster
4. Develop UI for layer controls and info panel
5. Test with progressively larger datasets to ensure performance 