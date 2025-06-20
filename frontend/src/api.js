import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: '/', // Uses the proxy set up in vite.config.js
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies/sessions
});

// Add a request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized errors (token expired, etc.)
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login if not already there
      localStorage.removeItem('authToken');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
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

export const searchDocuments = (query) => api.get(`/api/search?q=${encodeURIComponent(query)}`);
export const getDocuments = () => api.get('/api/documents');
export const getDocumentDetails = (id) => api.get(`/api/documents/${id}`);

export default api;
