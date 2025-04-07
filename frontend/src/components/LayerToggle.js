import React from 'react';

const LayerToggle = ({ activeLayers, onToggleLayer }) => {
  // Define the two exclusive layer options
  const layerOptions = [
    { id: 'all-points', name: 'All Points' },
    { id: 'featured-points', name: 'Featured Only' }
  ];

  const handleSelect = (layerId) => {
    onToggleLayer(layerId);
  };

  return (
    <div className="layer-toggle">
      <h3>Map Layers</h3>
      <div className="layer-toggle-buttons">
        {layerOptions.map((layer) => (
          <button
            key={layer.id}
            className={`layer-btn ${activeLayers.includes(layer.id) ? 'active' : ''}`}
            onClick={() => handleSelect(layer.id)}
          >
            {layer.name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default LayerToggle; 