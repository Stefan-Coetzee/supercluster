/**
 * Shared constants for field mappings and filter definitions
 */

// Mapping between database field names and GeoJSON property names
export const FIELD_MAPPING = {
    // Database field name -> GeoJSON property name
    'is_graduate_learner': 'is_graduate',
    'is_wage_employed': 'is_employed',
    'is_running_a_venture': 'is_entrepreneur',
    'is_featured': 'is_featured',
    'is_featured_video': 'has_video',
    'country_of_residence': 'country',
    'gender': 'gender'
};

// Reverse mapping for convenience
export const REVERSE_FIELD_MAPPING = Object.entries(FIELD_MAPPING).reduce(
    (acc, [k, v]) => ({ ...acc, [v]: k }),
    {}
);

// Filter types
export const FILTER_TYPES = {
    string_filters: ['gender', 'country_of_residence'],
    boolean_filters: ['is_graduate_learner', 'is_wage_employed', 
                     'is_running_a_venture', 'is_featured', 'is_featured_video']
};

// Filter display names (for UI)
export const FILTER_DISPLAY_NAMES = {
    'is_graduate_learner': 'Graduate',
    'is_wage_employed': 'Employed',
    'is_running_a_venture': 'Entrepreneur',
    'is_featured': 'Featured',
    'is_featured_video': 'Has Video',
    'country_of_residence': 'Country',
    'gender': 'Gender'
};

// Cluster visualization settings
export const CLUSTER_SETTINGS = {
    small: {
        maxPoints: 20,
        color: '#002b56', // Navy
        radius: 20
    },
    medium: {
        maxPoints: 100,
        color: '#002b56', // Navy
        radius: 25
    },
    large: {
        color: '#002b56', // Naby
        radius: 30
    },
    stroke: {
        width: 2,
        color: '#fff',
        opacity: 0.5
    }
};

// Layer definitions for map visualization
export const LAYER_DEFINITIONS = {
    'graduate-points': {
        filter_field: 'is_graduate_learner',
        color: '#4caf50', // Green for graduates
        radius: 6
    },
    'featured-points': {
        filter_field: 'is_featured',
        color: '#ff9800', // Orange for featured
        radius: 6
    },
    'entrepreneur-points': {
        filter_field: 'is_running_a_venture',
        color: '#9c27b0', // Purple for entrepreneurs
        radius: 6
    },
    'unclustered-points': {
        color: '#11b4da', // Light blue for regular points
        radius: 6
    }
}; 