import axios from 'axios';

// Create an axios instance with the correct base URL
const api = axios.create({
  baseURL: 'http://localhost:5000',  // Adjust this to your backend URL
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true  // Important for maintaining session cookies
});

// Add response interceptor to handle errors
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Auth API functions
export const getAuthStatus = () => api.get('/api/auth/status');
export const login = (credentials) => api.post('/api/auth/login', credentials);
export const logout = () => api.post('/api/auth/logout');
export const register = (userData) => api.post('/api/auth/register', userData);

// PDF API functions
export const uploadPdf = (formData, onUploadProgress) => 
  api.post('/api/upload', formData, { 
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress
  });

// Search API functions
export const searchDocuments = (queryData) => api.post('/api/search', queryData);
export const getSearchSuggestions = (query) => api.post('/api/suggestions', { query });
export const getDocumentStats = () => api.get('/api/documents/stats');

export default api;
