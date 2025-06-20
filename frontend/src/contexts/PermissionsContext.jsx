import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '../api';

// Create context
const PermissionsContext = createContext();

// Provider component
export const PermissionsProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [permissions, setPermissions] = useState({
    can_view: false,
    can_edit: false,
    can_upload: false,
    can_manage: false,
    can_manage_users: false,
    is_admin: false
  });
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch permissions when auth state changes
  useEffect(() => {
    const fetchPermissions = async () => {
      if (!isAuthenticated) {
        setPermissions({
          can_view: false,
          can_edit: false,
          can_upload: false,
          can_manage: false,
          can_manage_users: false,
          is_admin: false
        });
        setRole(null);
        setLoading(false);
        return;
      }

      try {
        const response = await api.get('/api/auth/permissions');
        setPermissions(response.data.permissions);
        setRole(response.data.role);
      } catch (error) {
        console.error('Error fetching permissions:', error);
        // Set default permissions based on user role from auth context
        if (user) {
          const isAdmin = user.is_admin || user.role === 'admin';
          const isEditor = user.role === 'editor';
          
          setPermissions({
            can_view: true,
            can_edit: isAdmin || isEditor,
            can_upload: isAdmin || isEditor,
            can_manage: isAdmin || isEditor,
            can_manage_users: isAdmin,
            is_admin: isAdmin
          });
          setRole(user.role || 'viewer');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPermissions();
  }, [isAuthenticated, user]);

  return (
    <PermissionsContext.Provider value={{ permissions, role, loading }}>
      {children}
    </PermissionsContext.Provider>
  );
};

// Custom hook to use the permissions context
export const usePermissions = () => {
  const context = useContext(PermissionsContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionsProvider');
  }
  return context;
};