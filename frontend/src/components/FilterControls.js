import React, { useState, useEffect } from 'react';

const FilterControls = ({ onApplyFilters, isLoading }) => {
  // Single active filter (like a radio button)
  const [activeFilter, setActiveFilter] = useState(null);

  // Apply the active filter
  useEffect(() => {
    let filterObject = {};
    
    // Build filter object based on active filter
    if (activeFilter === 'gender_female') {
      filterObject = { gender: 'Female' };
    } else if (activeFilter === 'is_graduate_learner') {
      filterObject = { is_graduate_learner: true };
    } else if (activeFilter === 'is_wage_employed') {
      filterObject = { is_wage_employed: true };
    } else if (activeFilter === 'is_running_a_venture') {
      filterObject = { is_running_a_venture: true };
    }
    
    onApplyFilters(filterObject);
  }, [activeFilter, onApplyFilters]);

  // Toggle function now works like a radio button
  const toggleFilter = (filterName) => {
    // If this filter is already active, deactivate it
    if (activeFilter === filterName) {
      setActiveFilter(null);
    } else {
      // Otherwise set it as the only active filter
      setActiveFilter(filterName);
    }
  };

  // Reset function
  const handleReset = () => {
    setActiveFilter(null);
  };

  return (
    <div className="filter-controls">
      <h3>Data Filters</h3>
      <div className="filter-buttons">
        <button 
          type="button" 
          className={`filter-btn ${activeFilter === 'gender_female' ? 'active' : ''}`}
          onClick={() => toggleFilter('gender_female')}
          disabled={isLoading}
        >
          Female Only
        </button>
        
        <button 
          type="button" 
          className={`filter-btn ${activeFilter === 'is_graduate_learner' ? 'active' : ''}`}
          onClick={() => toggleFilter('is_graduate_learner')}
          disabled={isLoading}
        >
          Graduates
        </button>
        
        <button 
          type="button" 
          className={`filter-btn ${activeFilter === 'is_wage_employed' ? 'active' : ''}`}
          onClick={() => toggleFilter('is_wage_employed')}
          disabled={isLoading}
        >
          Employed
        </button>
        
        <button 
          type="button" 
          className={`filter-btn ${activeFilter === 'is_running_a_venture' ? 'active' : ''}`}
          onClick={() => toggleFilter('is_running_a_venture')}
          disabled={isLoading}
        >
          Entrepreneurs
        </button>
        
        <button 
          type="button" 
          onClick={handleReset} 
          disabled={isLoading}
          className="reset-btn"
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
};

export default FilterControls; 