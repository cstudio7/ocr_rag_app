import React from 'react';
import { usePermissions } from '../contexts/PermissionsContext';

/**
 * Component that conditionally renders children based on user permissions
 * 
 * @param {Object} props
 * @param {string|string[]} props.requiredPermission - The permission(s) required to view the children
 * @param {React.ReactNode} props.children - The content to render if user has permission
 * @param {React.ReactNode} props.fallback - Optional content to render if user doesn't have permission
 */
const RoleBasedAccess = ({ requiredPermission, children, fallback = null }) => {
  const { permissions, loading } = usePermissions();
  
  if (loading) {
    return null; // Don't render anything while loading
  }
  
  // Check if user has the required permission
  const hasPermission = () => {
    if (Array.isArray(requiredPermission)) {
      return requiredPermission.some(perm => permissions[perm]);
    }
    return permissions[requiredPermission];
  };
  
  return hasPermission() ? children : fallback;
};

export default RoleBasedAccess;