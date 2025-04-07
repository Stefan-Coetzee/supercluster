import React, { useState } from 'react';
import './styles/index.css';
import Map from './components/Map';
import LayerToggle from './components/LayerToggle';
import FilterControls from './components/FilterControls';

function App() {
  // Simplified layer selection - just one active layer at a time
  const [activeLayers, setActiveLayers] = useState(['all-points']);
  
  const [filters, setFilters] = useState({});
  const [controlsOpen, setControlsOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Toggle a layer (exclusively)
  const handleToggleLayer = (layerId) => {
    // If the same layer is clicked, do nothing (prevent having no layers)
    if (activeLayers[0] === layerId) {
      return;
    }
    
    // Set only the selected layer as active
    setActiveLayers([layerId]);
  };

  // Apply filters
  const handleApplyFilters = (newFilters) => {
    setIsLoading(true);
    setFilters(newFilters);
    
    // Loading state will be managed by the Map component
    setTimeout(() => setIsLoading(false), 500);
  };

  // Toggle controls panel
  const toggleControls = () => {
    setControlsOpen(prev => !prev);
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Supercluster Map</h1>
        <button 
          className="toggle-controls-btn"
          onClick={toggleControls}
        >
          {controlsOpen ? 'Hide Controls' : 'Show Controls'}
        </button>
      </header>
      
      <div className="content-container">
        <Map 
          activeLayers={activeLayers} 
          filters={filters}
        />
        
        {controlsOpen && (
          <div className="map-controls">
            <LayerToggle 
              activeLayers={activeLayers} 
              onToggleLayer={handleToggleLayer} 
            />
            
            <FilterControls 
              onApplyFilters={handleApplyFilters}
              isLoading={isLoading}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App; 