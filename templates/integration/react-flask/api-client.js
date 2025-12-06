import axios from 'axios';

// {{API_BASE_URL}}
const API_BASE_URL = 'http://localhost:5000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// {{CUSTOM_INTERCEPTORS}}

// {{CUSTOM_API_FUNCTIONS}}

// Example API functions:
// export const getItems = async () => {
//   const response = await apiClient.get('/api/items');
//   return response.data;
// };

// export const createItem = async (item) => {
//   const response = await apiClient.post('/api/items', item);
//   return response.data;
// };

export default apiClient;

