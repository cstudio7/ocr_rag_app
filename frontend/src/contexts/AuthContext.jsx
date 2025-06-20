import React, { createContext, useContext, useState, useEffect } from 'react';
import { getAuthStatus, login as apiLogin, logout as apiLogout } from '../api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on component mount
  useEffect(() => {
    const checkAuth = async () => {
      console.log('Checking authentication status...');
      try {
        // Use the API function to check auth status
        const response = await getAuthStatus();
        const data = response.data;
        
        if (data.authenticated) {
          console.log('User authenticated via API:', data.user);
          setUser(data.user);
          setIsAuthenticated(true);
        } else {
          console.log('Not authenticated according to API');
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error('Auth check error:', error);
        // Check localStorage as fallback
        const storedAuth = localStorage.getItem('isAuthenticated');
        const storedUser = localStorage.getItem('user');
        
        if (storedAuth === 'true' && storedUser) {
          console.log('User authenticated via localStorage (after error)');
          setIsAuthenticated(true);
          setUser(JSON.parse(storedUser));
        } else {
          console.log('No authentication found (after error)');
          setIsAuthenticated(false);
          setUser(null);
        }
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const login = async (credentials) => {
    try {
      console.log('Attempting login with credentials:', credentials);
      const response = await apiLogin(credentials);
      const data = response.data;
      
      console.log('Login response:', data);
      
      if (data.message === "Login successful" && data.user) {
        // Store auth state
        setIsAuthenticated(true);
        setUser(data.user);
        
        // Save to localStorage as fallback
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('user', JSON.stringify(data.user));
        
        return { success: true };
      } else {
        return { success: false, error: data.error || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed. Please try again.' 
      };
    }
  };

  const logout = async () => {
    try {
      // Call logout API
      await apiLogout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state regardless of API success
      setIsAuthenticated(false);
      setUser(null);
      localStorage.removeItem('isAuthenticated');
      localStorage.removeItem('user');
    }
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
