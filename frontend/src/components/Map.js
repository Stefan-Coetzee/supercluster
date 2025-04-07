import React, { useRef, useEffect, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import superclusterAPI from '../api/superclusterAPI';
import { LAYER_DEFINITIONS, CLUSTER_SETTINGS } from '../constants';

// Advanced request manager that combines throttling and debouncing
const createRequestManager = () => {
  let timeout = null;
  let lastExecuted = 0;
  
  return (fn, options = {}) => {
    const { 
      throttleMs = 1000,   // Minimum time between executions during continuous interactions
      debounceMs = 500     // Wait time after last interaction
    } = options;
    
    return (...args) => {
      const now = Date.now();
      const remaining = lastExecuted + throttleMs - now;
      
      // Clear any existing timeout
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
      }

      // If we've waited long enough, execute immediately
      if (remaining <= 0) {
        lastExecuted = now;
        fn(...args);
      } else {
        // Otherwise, wait for the debounce period after interactions stop
        timeout = setTimeout(() => {
          lastExecuted = Date.now();
          fn(...args);
        }, debounceMs);
      }
    };
  };
};

// Get Mapbox token from .env file
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_ACCESS_TOKEN;

const Map = ({ activeLayers, filters }) => {
  // Create a request manager instance
  const requestManager = useRef(createRequestManager());
  
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [loading, setLoading] = useState(false);
  const [lng, setLng] = useState(0);
  const [lat, setLat] = useState(20);
  const [zoom, setZoom] = useState(1);
  const [showZoomNotice, setShowZoomNotice] = useState(true);
  const [isMapIdle, setIsMapIdle] = useState(true); // Track if map is not being interacted with
  const [lastFetchTime, setLastFetchTime] = useState(null);
  const [requestCount, setRequestCount] = useState(0);

  // Initial map setup
  useEffect(() => {
    if (map.current) return; // Map already initialized

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [lng, lat],
      zoom: zoom
    });

    // Wait for both map and style to load before adding layers
    map.current.on('style.load', () => {
      console.log('Map style loaded');
      
      // Add source for clusters with empty data initially
      if (!map.current.getSource('clusters')) {
        map.current.addSource('clusters', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: []
          },
          cluster: false // We handle clustering on the server
        });
      }

      // Layer for clusters (circles)
      if (!map.current.getLayer('clusters-circles')) {
        map.current.addLayer({
          id: 'clusters-circles',
          type: 'circle',
          source: 'clusters',
          filter: ['has', 'cluster'],
          paint: {
            'circle-color': [
              'step',
              ['get', 'point_count'],
              CLUSTER_SETTINGS.small.color,
              CLUSTER_SETTINGS.small.maxPoints,
              CLUSTER_SETTINGS.medium.color,
              CLUSTER_SETTINGS.medium.maxPoints,
              CLUSTER_SETTINGS.large.color
            ],
            'circle-radius': [
              'step',
              ['get', 'point_count'],
              CLUSTER_SETTINGS.small.radius,
              CLUSTER_SETTINGS.small.maxPoints,
              CLUSTER_SETTINGS.medium.radius,
              CLUSTER_SETTINGS.medium.maxPoints,
              CLUSTER_SETTINGS.large.radius
            ],
            'circle-opacity': 0.8,
            'circle-stroke-width': CLUSTER_SETTINGS.stroke.width,
            'circle-stroke-color': CLUSTER_SETTINGS.stroke.color,
            'circle-stroke-opacity': CLUSTER_SETTINGS.stroke.opacity
          }
        });
      }

      // Layer for cluster counts
      if (!map.current.getLayer('cluster-counts')) {
        map.current.addLayer({
          id: 'cluster-counts',
          type: 'symbol',
          source: 'clusters',
          filter: ['has', 'cluster'],
          layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 12
          },
          paint: {
            'text-color': '#ffffff'
          }
        });
      }

      // Layer for individual points
      if (!map.current.getLayer('unclustered-points')) {
        map.current.addLayer({
          id: 'unclustered-points',
          type: 'circle',
          source: 'clusters',
          filter: ['!', ['has', 'cluster']],
          paint: {
            'circle-color': LAYER_DEFINITIONS['unclustered-points'].color,
            'circle-radius': LAYER_DEFINITIONS['unclustered-points'].radius,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
          }
        });
      }

      // Layer for graduate points (separate visualization)
      if (!map.current.getLayer('graduate-points')) {
        map.current.addLayer({
          id: 'graduate-points',
          type: 'circle',
          source: 'clusters',
          filter: ['all', 
            ['!', ['has', 'cluster']], 
            ['==', ['get', LAYER_DEFINITIONS['graduate-points'].filter_field], 1]
          ],
          paint: {
            'circle-color': LAYER_DEFINITIONS['graduate-points'].color,
            'circle-radius': LAYER_DEFINITIONS['graduate-points'].radius,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
          }
        });
      }

      // Layer for featured points (separate visualization)
      if (!map.current.getLayer('featured-points')) {
        map.current.addLayer({
          id: 'featured-points',
          type: 'circle',
          source: 'clusters',
          filter: ['all', 
            ['!', ['has', 'cluster']], 
            ['==', ['get', LAYER_DEFINITIONS['featured-points'].filter_field], 1]
          ],
          paint: {
            'circle-color': LAYER_DEFINITIONS['featured-points'].color,
            'circle-radius': LAYER_DEFINITIONS['featured-points'].radius,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
          }
        });
      }

      // Layer for entrepreneurs (separate visualization)
      if (!map.current.getLayer('entrepreneur-points')) {
        map.current.addLayer({
          id: 'entrepreneur-points',
          type: 'circle',
          source: 'clusters',
          filter: ['all', 
            ['!', ['has', 'cluster']], 
            ['==', ['get', LAYER_DEFINITIONS['entrepreneur-points'].filter_field], 1]
          ],
          paint: {
            'circle-color': LAYER_DEFINITIONS['entrepreneur-points'].color,
            'circle-radius': LAYER_DEFINITIONS['entrepreneur-points'].radius,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
          }
        });
      }

      // Add popup on click (for unclustered points)
      map.current.on('click', 'unclustered-points', (e) => {
        if (!e.features || e.features.length === 0) return;
        
        const feature = e.features[0];
        const coordinates = feature.geometry.coordinates.slice();
        const properties = feature.properties;
        
        // Create HTML content for popup
        const popupContent = `
          <h3>${properties.full_name || 'Anonymous'}</h3>
          <p><strong>Country:</strong> ${properties.country || 'Unknown'}</p>
          <p><strong>Gender:</strong> ${properties.gender || 'Unknown'}</p>
          <p><strong>Graduate:</strong> ${properties.is_graduate_learner === 1 ? 'Yes' : 'No'}</p>
          <p><strong>Employed:</strong> ${properties.is_wage_employed === 1 ? 'Yes' : 'No'}</p>
          <p><strong>Entrepreneur:</strong> ${properties.is_running_a_venture === 1 ? 'Yes' : 'No'}</p>
          ${properties.is_featured === 1 ? '<p><strong>⭐ Featured</strong></p>' : ''}
        `;
        
        // Ensure that if the map is zoomed out such that multiple
        // copies of the feature are visible, the popup appears
        // over the copy being pointed to.
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
          coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }
        
        new mapboxgl.Popup()
          .setLngLat(coordinates)
          .setHTML(popupContent)
          .addTo(map.current);
      });
      
      // Click on a cluster to zoom in
      map.current.on('click', 'clusters-circles', (e) => {
        if (!e.features || e.features.length === 0) return;
        
        const feature = e.features[0];
        // Get expansion zoom if available, otherwise zoom in by 2 levels
        const expansionZoom = feature.properties.expansion_zoom || (map.current.getZoom() + 2);
        
        map.current.easeTo({
          center: feature.geometry.coordinates,
          zoom: expansionZoom
        });
      });

      // Change cursor to pointer when hovering over clusters or points
      map.current.on('mouseenter', 'clusters-circles', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });
      
      map.current.on('mouseleave', 'clusters-circles', () => {
        map.current.getCanvas().style.cursor = '';
      });
      
      map.current.on('mouseenter', 'unclustered-points', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });
      
      map.current.on('mouseleave', 'unclustered-points', () => {
        map.current.getCanvas().style.cursor = '';
      });

      // Initial data fetch after layers are added
      if (map.current && map.current.loaded() && zoom >= 2) {
        managedFetchClusters();
      }
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-left');
    
    // Add fullscreen control
    map.current.addControl(new mapboxgl.FullscreenControl());

    // Add scale
    map.current.addControl(new mapboxgl.ScaleControl({ maxWidth: 200, unit: 'metric' }));

    // Timers ref for cleanup
    const timers = {
      idle: null
    };

    // Event handlers for map movement
    map.current.on('move', () => {
      setLng(parseFloat(map.current.getCenter().lng.toFixed(4)));
      setLat(parseFloat(map.current.getCenter().lat.toFixed(4)));
      setZoom(parseFloat(map.current.getZoom().toFixed(2)));
      setIsMapIdle(false); // Map is moving, not idle
    });

    // Event handlers for map idle state - cancel any pending idle timer first
    const handleInteractionStart = () => {
      setIsMapIdle(false);
      if (timers.idle) {
        clearTimeout(timers.idle);
      }
    };

    // Set the map to idle after interaction ends and delay
    const handleInteractionEnd = () => {
      if (timers.idle) {
        clearTimeout(timers.idle);
      }
      timers.idle = setTimeout(() => {
        setIsMapIdle(true);
      }, 500); // A longer delay to ensure user has really stopped interacting
    };

    // Add interaction event listeners
    map.current.on('mousedown', handleInteractionStart);
    map.current.on('touchstart', handleInteractionStart);
    map.current.on('mouseup', handleInteractionEnd);
    map.current.on('touchend', handleInteractionEnd);
    map.current.on('movestart', handleInteractionStart);
    map.current.on('moveend', handleInteractionEnd);
    map.current.on('dragstart', handleInteractionStart);
    map.current.on('dragend', handleInteractionEnd);
    map.current.on('zoomstart', handleInteractionStart);
    map.current.on('zoomend', handleInteractionEnd);
    map.current.on('pitchstart', handleInteractionStart);
    map.current.on('pitchend', handleInteractionEnd);
    map.current.on('rotatestart', handleInteractionStart);
    map.current.on('rotateend', handleInteractionEnd);

    // Clean up function
    return () => {
      if (timers.idle) {
        clearTimeout(timers.idle);
      }
      
      if (map.current) {
        // Remove event listeners
        map.current.off('mousedown', handleInteractionStart);
        map.current.off('touchstart', handleInteractionStart);
        map.current.off('mouseup', handleInteractionEnd);
        map.current.off('touchend', handleInteractionEnd);
        map.current.off('movestart', handleInteractionStart);
        map.current.off('moveend', handleInteractionEnd);
        map.current.off('dragstart', handleInteractionStart);
        map.current.off('dragend', handleInteractionEnd);
        map.current.off('zoomstart', handleInteractionStart);
        map.current.off('zoomend', handleInteractionEnd);
        map.current.off('pitchstart', handleInteractionStart);
        map.current.off('pitchend', handleInteractionEnd);
        map.current.off('rotatestart', handleInteractionStart);
        map.current.off('rotateend', handleInteractionEnd);
      }
    };
  }, [lng, lat, zoom]);

  // Update layers visibility based on active layers
  useEffect(() => {
    if (!map.current || !map.current.loaded()) return;

    // Core cluster layers are always visible
    const clusterLayers = [
      'clusters-circles',
      'cluster-counts'
    ];
    
    // Point layers that can be toggled
    const pointLayers = [
      'unclustered-points',
      'featured-points',
      'graduate-points',
      'entrepreneur-points'
    ];
    
    // First, make all cluster layers visible
    clusterLayers.forEach(layerId => {
      map.current.setLayoutProperty(layerId, 'visibility', 'visible');
    });
    
    // Then handle the specific point layers based on active selection
    pointLayers.forEach(layerId => {
      // By default, hide all point layers
      let visibility = 'none';
      
      // If 'all-points' is active, show only the unclustered-points layer
      if (activeLayers.includes('all-points') && layerId === 'unclustered-points') {
        visibility = 'visible';
      }
      // If 'featured-points' is active, show only the featured-points layer
      else if (activeLayers.includes('featured-points') && layerId === 'featured-points') {
        visibility = 'visible';
      }
      
      map.current.setLayoutProperty(layerId, 'visibility', visibility);
    });
  }, [activeLayers]);

  // Fetch clusters when filters change or map moves - memoized with useCallback
  const fetchClusters = useCallback(async () => {
    if (!map.current || !map.current.loaded()) return;
    
    const currentZoom = Math.round(map.current.getZoom());
    
    // For very low zoom levels, limit data fetching to prevent crashes
    if (currentZoom < 2) {
      setShowZoomNotice(true);
      return;
    } else {
      setShowZoomNotice(false);
    }
    
    // Update fetch metrics
    setLoading(true);
    setLastFetchTime(new Date().toLocaleTimeString());
    setRequestCount(prev => prev + 1);

    try {
      const bounds = map.current.getBounds();
      const bbox = [
        bounds.getWest(),  
        bounds.getSouth(),
        bounds.getEast(),  
        bounds.getNorth() 
      ];
      
      // Single API call with filters
      const clustersResponse = await superclusterAPI.getClusters(
        bbox,
        currentZoom,
        filters
      );
      
      // Enhanced cluster data logging
      const clusters = clustersResponse.features.filter(f => f.properties.cluster);
      const points = clustersResponse.features.filter(f => !f.properties.cluster);
      
      console.log('Clusters Data:', {
        total: clustersResponse.features.length,
        clusterCount: clusters.length,
        pointCount: points.length,
        sampleCluster: clusters[0] ? {
          properties: clusters[0].properties,
          geometry: clusters[0].geometry
        } : null,
        samplePoint: points[0] ? {
          properties: points[0].properties,
          geometry: points[0].geometry
        } : null
      });
      
      // Update the GeoJSON source with new data
      if (map.current.getSource('clusters')) {
        map.current.getSource('clusters').setData({
          type: 'FeatureCollection',
          features: clustersResponse.features
        });
      }

      // Debug: Log layer visibility
      if (map.current) {
        console.log('Layer Visibility:', {
          'clusters-circles': map.current.getLayoutProperty('clusters-circles', 'visibility'),
          'cluster-counts': map.current.getLayoutProperty('cluster-counts', 'visibility'),
          'unclustered-points': map.current.getLayoutProperty('unclustered-points', 'visibility')
        });
      }
    } catch (error) {
      console.error('Error fetching clusters:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Create a managed version of fetchClusters using our request manager
  const managedFetchClusters = useCallback(() => {
    requestManager.current(fetchClusters, {
      throttleMs: 2000,  // At most one request every 2 seconds during continuous interaction
      debounceMs: 800    // Wait 800ms after interaction stops before fetching
    })();
  }, [fetchClusters]);

  // Fetch data when the map becomes idle after movement
  useEffect(() => {
    if (isMapIdle && map.current && map.current.loaded() && zoom >= 2) {
      managedFetchClusters();
    }
  }, [isMapIdle, zoom, managedFetchClusters]);

  // Fetch data when filters change, but only if map is ready
  useEffect(() => {
    if (map.current && map.current.loaded() && zoom >= 2) {
      managedFetchClusters();
    }
  }, [filters, managedFetchClusters, zoom]);

  return (
    <div className="map-wrapper">
      <div ref={mapContainer} className="map-container" style={{ width: '100%', height: '100%' }} />
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
      {showZoomNotice && (
        <div className="zoom-notice">
          Please zoom in to see data points
        </div>
      )}
      <div className="map-info">
        <span>Longitude: {lng}° | Latitude: {lat}° | Zoom: {zoom}</span>
        {lastFetchTime && (
          <span className="fetch-info"> | Last fetch: {lastFetchTime} | API Calls: {requestCount}</span>
        )}
      </div>
    </div>
  );
};

export default Map; 