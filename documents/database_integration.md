# Database Integration

## Overview

This document outlines the database structure and integration approach for the map visualization application. The application primarily uses a MySQL database to store and retrieve learner data and associated metrics. We need to efficiently query this data to power both the choropleth visualization and the Supercluster-based point/cluster visualization.

## Database Schema

The application relies on several MySQL tables, with `impact_learners_profile` being the primary source of geospatial data. Below are the key tables and their purposes:

### Primary Tables

#### `impact_learners_profile`

Contains detailed information about individual learners, including geographical coordinates:

Key fields:
- `hashed_email`: Unique identifier for each learner
- `full_name`: Learner's name
- `profile_photo_url`: URL to the learner's profile photo
- `gender`: Learner's gender
- `country_of_residence`: Country where the learner resides
- `city_of_residence`: City where the learner resides
- `country_of_residence_latitude` and `country_of_residence_longitude`: Country-level coordinates
- `city_of_residence_latitude` and `city_of_residence_longitude`: City-level coordinates
- `meta_ui_lat` and `meta_ui_lng`: UI-specific coordinates (used for visualization)
- Status flags:
  - `is_learning_data`: Whether the learner is currently learning
  - `is_graduate_learner`: Whether the learner has graduated
  - `is_running_a_venture`: Whether the learner is running a business
  - `is_a_freelancer`: Whether the learner is working as a freelancer
  - `is_wage_employed`: Whether the learner is employed
  - `is_featured`: Whether the learner is featured
  - `is_featured_video`: Whether the learner has a featured video

#### `impact_metrics`

Contains aggregated metrics that can be used for choropleth visualization and filtering:

Key fields:
- `year`: Year of the metric
- `metric`: Name of the metric
- `metric_value`: Value of the metric
- `gender`: Gender breakdown (if applicable)
- `dimension`: Additional dimension for the metric

#### Supporting Tables

- `impact_placement_overview_by_country`: Contains country-level placement data
- `impact_outreach_feed`: Contains outreach narratives
- `impact_jobs_feed`: Contains job-related information
- `startups`: Contains information about startups founded by learners

## Data Query Patterns

### Point Data for Supercluster

The main query for retrieving point data:

```sql
SELECT
  hashed_email,
  country_of_residence, 
  round(meta_ui_lat, 5) as city_of_residence_latitude,
  round(meta_ui_lng, 5) as city_of_residence_longitude
FROM
  impact_learners_profile
LIMIT ?
```

For a more complete dataset with properties for filtering:

```sql
SELECT
  hashed_email,
  full_name,
  country_of_residence,
  round(meta_ui_lat, 5) as city_of_residence_latitude,
  round(meta_ui_lng, 5) as city_of_residence_longitude,
  gender,
  is_graduate_learner,
  is_learning_data,
  is_wage_employed,
  is_running_a_venture,
  is_featured,
  is_featured_video,
  youtube_id
FROM
  impact_learners_profile
WHERE
  has_data = 1
  AND meta_ui_lat IS NOT NULL
  AND meta_ui_lng IS NOT NULL
LIMIT ? OFFSET ?
```

### Choropleth Data

For country-level aggregate data to power the choropleth layer:

```sql
SELECT
  country_of_residence,
  COUNT(*) AS total_learners,
  SUM(CASE WHEN is_learning_data = 1 THEN 1 ELSE 0 END) AS learners_learning,
  SUM(CASE WHEN is_graduate_learner = 1 THEN 1 ELSE 0 END) AS learners_graduated,
  SUM(CASE WHEN is_learning_data = 1 AND has_data = 1 THEN 1 ELSE 0 END) AS learners_learning_with_data
FROM
  impact_learners_profile
GROUP BY
  country_of_residence
ORDER BY
  total_learners DESC;
```

### Detailed Learner Data

When a user clicks on an individual point, we need to fetch more detailed information:

```sql
SELECT
  hashed_email,
  full_name,
  profile_photo_url,
  bio,
  gender,
  country_of_residence,
  city_of_residence,
  education_level_of_study,
  education_field_of_study,
  testimonial,
  placement_details,
  employment_details,
  is_learning_data,
  is_graduate_learner,
  is_wage_employed,
  is_running_a_venture,
  is_featured,
  youtube_id
FROM
  impact_learners_profile
WHERE
  hashed_email = ?
```

## Database Integration Implementation

### Connection Management

We'll use the `serverless-mysql` package to establish and manage connections to the MySQL database:

```typescript
// lib/db/mysql.ts
import mysql from 'serverless-mysql';

const db = mysql({
  config: {
    host: process.env.MYSQL_HOST,
    port: parseInt(process.env.MYSQL_PORT || '3306'),
    database: process.env.MYSQL_DATABASE,
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD
  }
});

// Helper for running a query and closing the connection
export async function query<T>(
  q: string, 
  values: any[] = []
): Promise<T> {
  try {
    const results = await db.query<T>(q, values);
    await db.end();
    return results;
  } catch (error) {
    throw error;
  }
}
```

### Data Loader Implementation

The DataLoader service will wrap database queries with caching and error handling:

```typescript
// lib/data/dataLoader.ts
import { query } from '@/lib/db/mysql';
import { LearnerPoint, CountryMetric, LearnerDetail } from '@/types';

// In-memory cache
const cache: Record<string, { data: any; expires: number }> = {};

export class DataLoader {
  async loadLearnerPoints(limit: number = 1000, offset: number = 0): Promise<LearnerPoint[]> {
    const cacheKey = `learnerPoints:${limit}:${offset}`;
    
    // Check cache first
    const cached = this.getCachedData<LearnerPoint[]>(cacheKey);
    if (cached) return cached;
    
    // Query database
    const points = await query<LearnerPoint[]>(
      `SELECT
        hashed_email,
        country_of_residence,
        round(meta_ui_lat, 5) as city_of_residence_latitude,
        round(meta_ui_lng, 5) as city_of_residence_longitude,
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
      LIMIT ? OFFSET ?`,
      [limit, offset]
    );
    
    // Cache results
    this.setCachedData(cacheKey, points, 60 * 5); // 5 minute cache
    
    return points;
  }
  
  async loadCountryMetrics(): Promise<CountryMetric[]> {
    const cacheKey = 'countryMetrics';
    
    // Check cache first
    const cached = this.getCachedData<CountryMetric[]>(cacheKey);
    if (cached) return cached;
    
    // Query database
    const metrics = await query<CountryMetric[]>(
      `SELECT
        country_of_residence,
        COUNT(*) AS total_learners,
        SUM(CASE WHEN is_learning_data = 1 THEN 1 ELSE 0 END) AS learners_learning,
        SUM(CASE WHEN is_graduate_learner = 1 THEN 1 ELSE 0 END) AS learners_graduated,
        SUM(CASE WHEN is_learning_data = 1 AND has_data = 1 THEN 1 ELSE 0 END) AS learners_learning_with_data
      FROM
        impact_learners_profile
      GROUP BY
        country_of_residence
      ORDER BY
        total_learners DESC`
    );
    
    // Cache results
    this.setCachedData(cacheKey, metrics, 60 * 30); // 30 minute cache
    
    return metrics;
  }
  
  async loadLearnerDetails(id: string): Promise<LearnerDetail | null> {
    const cacheKey = `learnerDetail:${id}`;
    
    // Check cache first
    const cached = this.getCachedData<LearnerDetail>(cacheKey);
    if (cached) return cached;
    
    // Query database
    const [learner] = await query<LearnerDetail[]>(
      `SELECT
        hashed_email,
        full_name,
        profile_photo_url,
        bio,
        gender,
        country_of_residence,
        city_of_residence,
        education_level_of_study,
        education_field_of_study,
        testimonial,
        placement_details,
        employment_details,
        is_learning_data,
        is_graduate_learner,
        is_wage_employed,
        is_running_a_venture,
        is_featured,
        youtube_id
      FROM
        impact_learners_profile
      WHERE
        hashed_email = ?`,
      [id]
    );
    
    if (!learner) return null;
    
    // Cache results
    this.setCachedData(cacheKey, learner, 60 * 60); // 1 hour cache
    
    return learner;
  }
  
  // Cache methods
  getCachedData<T>(key: string): T | null {
    const item = cache[key];
    
    if (!item) return null;
    
    // Check if expired
    if (item.expires < Date.now()) {
      delete cache[key];
      return null;
    }
    
    return item.data as T;
  }
  
  setCachedData<T>(key: string, data: T, ttlSeconds: number = 300): void {
    cache[key] = {
      data,
      expires: Date.now() + (ttlSeconds * 1000)
    };
  }
}
```

## Performance Considerations

### Pagination and Chunking

For the approximately 2 million data points, we'll implement pagination and chunking:

1. Initial load will fetch a smaller subset (e.g., 50,000 points) for immediate visualization
2. Additional data can be loaded in chunks based on viewport and zoom level
3. When filters are applied, we'll fetch pre-filtered chunks

### Indexing

The database should maintain indexes on frequently queried fields:

- `hashed_email` (primary lookups)
- `country_of_residence` (for choropleth and filtering)
- `gender` (for filtering)
- Status flags (`is_graduate_learner`, `is_wage_employed`, etc.) for filtering

### Caching Strategy

We'll implement a multi-layer caching strategy:

1. **Database Cache**: Frequent queries should be cached at the database level
2. **API Cache**: Common API responses cached for appropriate durations
3. **Client Cache**: Browser caching for static assets and reusable data

## Error Handling

The data loader will implement robust error handling:

1. Retry logic for transient database errors
2. Fallback to cached data when database queries fail
3. Graceful degradation when certain data is unavailable

## Future Enhancements

1. **Redis Cache**: For production, replace in-memory cache with Redis
2. **Query Optimization**: Implement more complex filtering directly in SQL
3. **Sharding**: If needed, implement sharding for the data based on geographical regions
4. **Real-time Updates**: Implement WebSocket connections for real-time data updates 