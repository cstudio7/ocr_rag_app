import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFileAlt, 
  faSearch, 
  faUpload, 
  faDatabase,
  faSignInAlt,
  faUserPlus,
  faSignOutAlt,
  faUsers,
  faUser,
  faUserCog
} from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../contexts/AuthContext';
import { usePermissions } from '../contexts/PermissionsContext';
import RoleBasedAccess from './RoleBasedAccess';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const { permissions } = usePermissions();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center" to="/">
          <FontAwesomeIcon icon={faFileAlt} className="me-2" />
          <span>PDF Knowledge Base</span>
        </Link>
        
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <div className="collapse navbar-collapse" id="navbarNav">
          {isAuthenticated ? (
            <>
              {/* Authenticated navigation links */}
              <ul className="navbar-nav me-auto">
                <li className="nav-item">
                  <Link className="nav-link" to="/">
                    <FontAwesomeIcon icon={faFileAlt} className="me-1" />
                    Home
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" to="/search">
                    <FontAwesomeIcon icon={faSearch} className="me-1" />
                    Search
                  </Link>
                </li>
                
                <RoleBasedAccess requiredPermission="can_upload">
                  <li className="nav-item">
                    <Link className="nav-link" to="/upload">
                      <FontAwesomeIcon icon={faUpload} className="me-1" />
                      Upload
                    </Link>
                  </li>
                </RoleBasedAccess>
                
                <RoleBasedAccess requiredPermission="can_manage">
                  <li className="nav-item">
                    <Link className="nav-link" to="/documents">
                      <FontAwesomeIcon icon={faDatabase} className="me-1" />
                      Documents
                    </Link>
                  </li>
                </RoleBasedAccess>
                
                <RoleBasedAccess requiredPermission="can_manage_users">
                  <li className="nav-item">
                    <Link className="nav-link" to="/users">
                      <FontAwesomeIcon icon={faUsers} className="me-1" />
                      Users
                    </Link>
                  </li>
                </RoleBasedAccess>
              </ul>
              
              {/* User dropdown */}
              <ul className="navbar-nav">
                <li className="nav-item dropdown">
                  <a className="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <FontAwesomeIcon icon={faUser} className="me-1" />
                    {user?.first_name || user?.username} 
                    <span className="ms-1 badge bg-light text-dark">
                      {user?.role || 'User'}
                    </span>
                  </a>
                  <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                    <li>
                      <Link className="dropdown-item" to="/profile">
                        <FontAwesomeIcon icon={faUserCog} className="me-2" />
                        Profile
                      </Link>
                    </li>
                    <li><hr className="dropdown-divider" /></li>
                    <li>
                      <button className="dropdown-item" onClick={handleLogout}>
                        <FontAwesomeIcon icon={faSignOutAlt} className="me-2" />
                        Logout
                      </button>
                    </li>
                  </ul>
                </li>
              </ul>
            </>
          ) : (
            /* Unauthenticated navigation links */
            <ul className="navbar-nav ms-auto">
              <li className="nav-item">
                <Link className="nav-link" to="/login">
                  <FontAwesomeIcon icon={faSignInAlt} className="me-1" />
                  Login
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/register">
                  <FontAwesomeIcon icon={faUserPlus} className="me-1" />
                  Register
                </Link>
              </li>
            </ul>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
