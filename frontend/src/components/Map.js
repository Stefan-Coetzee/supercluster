import React, { useRef, useEffect, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import superclusterAPI from '../api/superclusterAPI';

// Simple debounce function
const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      func.apply(null, args);
    }, delay);
  };
};

// Get Mapbox token from .env file
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_ACCESS_TOKEN || 'pk.eyJ1Ijoic2NvZXR6ZWUiLCJhIjoiY202N3RnZzZzMDgzZTJyczg4d3Z2NDhubiJ9.htvS1yoTXD2iSzSEz5Z5Fw';

const Map = ({ activeLayers, filters }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [loading, setLoading] = useState(false);
  const [lng, setLng] = useState(0);
  const [lat, setLat] = useState(20);
  const [zoom, setZoom] = useState(1);
  const [showZoomNotice, setShowZoomNotice] = useState(true);

  // Initial map setup
  useEffect(() => {
    if (map.current) return; // Map already initialized

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [lng, lat],
      zoom: zoom
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-left');
    
    // Add fullscreen control
    map.current.addControl(new mapboxgl.FullscreenControl());

    // Add scale
    map.current.addControl(new mapboxgl.ScaleControl({ maxWidth: 200, unit: 'metric' }));

    // Event handlers
    map.current.on('move', () => {
      setLng(parseFloat(map.current.getCenter().lng.toFixed(4)));
      setLat(parseFloat(map.current.getCenter().lat.toFixed(4)));
      setZoom(parseFloat(map.current.getZoom().toFixed(2)));
    });

    // Initial load
    map.current.on('load', () => {
      // Add source for clusters with empty data initially
      map.current.addSource('clusters', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: []
        },
        cluster: false // We handle clustering on the server
      });

      // Layer for clusters (circles)
      map.current.addLayer({
        id: 'clusters-circles',
        type: 'circle',
        source: 'clusters',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6', // 0-20 points
            20,
            '#f1f075', // 20-100 points
            100,
            '#f28cb1' // 100+ points
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            20, // Base size
            20,
            25, // 20-100 points
            100,
            30 // 100+ points
          ],
          'circle-opacity': 0.8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
          'circle-stroke-opacity': 0.5
        }
      });

      // Layer for cluster counts
      map.current.addLayer({
        id: 'cluster-counts',
        type: 'symbol',
        source: 'clusters',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 12
        },
        paint: {
          'text-color': '#ffffff'
        }
      });

      // Layer for individual points
      map.current.addLayer({
        id: 'unclustered-points',
        type: 'circle',
        source: 'clusters',
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': '#11b4da',
          'circle-radius': 6,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff'
        }
      });

      // Layer for graduate points (separate visualization)
      map.current.addLayer({
        id: 'graduate-points',
        type: 'circle',
        source: 'clusters',
        filter: ['all', 
          ['!', ['has', 'point_count']], 
          ['==', ['get', 'is_graduate_learner'], true]
        ],
        paint: {
          'circle-color': '#4caf50', // Green for graduates
          'circle-radius': 6,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff'
        }
      });

      // Layer for featured points (separate visualization)
      map.current.addLayer({
        id: 'featured-points',
        type: 'circle',
        source: 'clusters',
        filter: ['all', 
          ['!', ['has', 'point_count']], 
          ['==', ['get', 'is_featured'], true]
        ],
        paint: {
          'circle-color': '#ff9800', // Orange for featured
          'circle-radius': 6,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff'
        }
      });

      // Layer for entrepreneurs (separate visualization)
      map.current.addLayer({
        id: 'entrepreneur-points',
        type: 'circle',
        source: 'clusters',
        filter: ['all', 
          ['!', ['has', 'point_count']], 
          ['==', ['get', 'is_running_a_venture'], true]
        ],
        paint: {
          'circle-color': '#9c27b0', // Purple for entrepreneurs
          'circle-radius': 6,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff'
        }
      });

      // Add popup on click (for unclustered points)
      map.current.on('click', 'unclustered-points', (e) => {
        if (!e.features || e.features.length === 0) return;
        
        const feature = e.features[0];
        const coordinates = feature.geometry.coordinates.slice();
        const properties = feature.properties;
        
        // Create HTML content for popup
        const popupContent = `
          <h3>${properties.full_name || 'Anonymous'}</h3>
          <p><strong>Country:</strong> ${properties.country_of_residence || 'Unknown'}</p>
          <p><strong>Gender:</strong> ${properties.gender || 'Unknown'}</p>
          <p><strong>Graduate:</strong> ${properties.is_graduate_learner ? 'Yes' : 'No'}</p>
          <p><strong>Employed:</strong> ${properties.is_wage_employed ? 'Yes' : 'No'}</p>
          <p><strong>Entrepreneur:</strong> ${properties.is_running_a_venture ? 'Yes' : 'No'}</p>
          ${properties.is_featured ? '<p><strong>⭐ Featured</strong></p>' : ''}
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

      // Initial data fetch - this will be handled by the useEffect for filters
    });

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
    
    setLoading(true);
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
      
      // Update the GeoJSON source with new data
      if (map.current.getSource('clusters')) {
        map.current.getSource('clusters').setData({
          type: 'FeatureCollection',
          features: clustersResponse.features
        });
      }
    } catch (error) {
      console.error('Error fetching clusters:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, setLoading]);

  // Initial data loading after map is initialized
  useEffect(() => {
    if (map.current && map.current.loaded()) {
      fetchClusters();
    }
  }, [fetchClusters]);

  // Create memoized fetchClusters function to avoid dependency issues
  const fetchClustersRef = useRef(fetchClusters);
  useEffect(() => {
    fetchClustersRef.current = fetchClusters;
  }, [fetchClusters]);

  // Create a debounced version of fetchClusters
  const debouncedFetchClusters = useCallback(
    debounce(() => {
      fetchClusters();
    }, 300),
    [fetchClusters]
  );

  // Re-fetch when map moves
  useEffect(() => {
    if (!map.current) return;
    
    const onMoveEnd = () => {
      debouncedFetchClusters();
    };
    
    map.current.on('moveend', onMoveEnd);
    
    return () => {
      if (map.current) {
        map.current.off('moveend', onMoveEnd);
      }
    };
  }, [debouncedFetchClusters]);

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
      </div>
    </div>
  );
};

export default Map; 