import axios from 'axios';

const API_BASE_URL = '/api';

export const superclusterAPI = {
  // Get clusters for a specific bounding box and zoom level
  getClusters: async (bbox, zoom, filters = {}) => {
    console.log(`API Request: getClusters at ${new Date().toLocaleTimeString()} - zoom: ${zoom}, bbox: [${bbox.join(', ')}]`);
    console.log(`Filters:`, filters);
    
    try {
      const startTime = performance.now();
      
      // Unpack bbox into individual coordinates
      const [west, south, east, north] = bbox;
      
      // Build query parameters
      const params = {
        west,
        south,
        east,
        north,
        zoom,
        ...filters  // Spread filter parameters
      };
      
      const response = await axios.get(`${API_BASE_URL}/getClusters`, { params });
      
      const endTime = performance.now();
      console.log(`API Response received in ${(endTime - startTime).toFixed(0)}ms`);
      return response.data;
    } catch (error) {
      console.error('Error getting clusters:', error);
      throw error;
    }
  },

  // Get available filters
  getAvailableFilters: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/availableFilters`);
      return response.data;
    } catch (error) {
      console.error('Error getting available filters:', error);
      throw error;
    }
  },

  // Get cache statistics
  getStats: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error getting stats:', error);
      throw error;
    }
  },

  // Clear the supercluster index cache
  clearCache: async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/clearCache`);
      return response.data;
    } catch (error) {
      console.error('Error clearing cache:', error);
      throw error;
    }
  }
};

export default superclusterAPI; 