import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { usePermissions } from '../contexts/PermissionsContext';

/**
 * A wrapper component that redirects to the login page
 * if the user is not authenticated or doesn't have the required permission
 */
const ProtectedRoute = ({ children, requiredPermission = null }) => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { permissions, loading: permissionsLoading } = usePermissions();

  if (authLoading || permissionsLoading) {
    // Show loading state
    return <div className="loading">Loading...</div>;
  }

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  // Check permissions if required
  if (requiredPermission) {
    const hasPermission = Array.isArray(requiredPermission)
      ? requiredPermission.some(perm => permissions[perm])
      : permissions[requiredPermission];

    if (!hasPermission) {
      // Redirect to home if not authorized
      return <Navigate to="/" replace />;
    }
  }

  // Render children if authenticated and authorized
  return children;
};

export default ProtectedRoute;
