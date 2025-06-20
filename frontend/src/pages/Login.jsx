import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSignInAlt, faSpinner, faExclamationTriangle, faUserPlus } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../contexts/AuthContext';
import '../styles/auth.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Check for message from registration and redirect if already authenticated
  useEffect(() => {
    if (location.state?.message) {
      console.log(location.state.message);
    }
    
    // If already authenticated, redirect to home
    if (isAuthenticated) {
      navigate('/');
    }
  }, [location, isAuthenticated, navigate]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      console.log("Attempting login with:", formData.username);
      const result = await login({
        username: formData.username,
        password: formData.password,
        remember_me: formData.rememberMe
      });
      
      if (result.success) {
        // Redirect to home or intended page
        const from = location.state?.from?.pathname || '/';
        navigate(from);
      } else {
        setError(result.error || 'Login failed. Please try again.');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Login Card */}
        <div className="auth-card mb-4">
          <div className="auth-header">
            <h2>
              <FontAwesomeIcon icon={faSignInAlt} className="me-2" />
              Login
            </h2>
            <p>Sign in to access your documents</p>
          </div>
          
          {error && (
            <div className="alert alert-danger d-flex align-items-center" role="alert">
              <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
              <div>{error}</div>
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="username" className="form-label">Username or Email</label>
              <input
                type="text"
                className="form-control"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>
            
            <div className="mb-3">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                className="form-control"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>
            
            <div className="mb-3 form-check">
              <input
                type="checkbox"
                className="form-check-input"
                id="rememberMe"
                name="rememberMe"
                checked={formData.rememberMe}
                onChange={handleChange}
                disabled={loading}
              />
              <label className="form-check-label" htmlFor="rememberMe">
                Remember me
              </label>
            </div>
            
            <div className="d-grid">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <FontAwesomeIcon icon={faSpinner} spin className="me-2" />
                    Logging in...
                  </>
                ) : (
                  'Login'
                )}
              </button>
            </div>
          </form>
          
          <div className="mt-4 text-center">
            <p>
              Don't have an account? <Link to="/register">Register</Link>
            </p>
          </div>
        </div>
        
        {/* Get Started Card */}
        <div className="get-started-card">
          <div className="card bg-primary text-white border-0 shadow-lg">
            <div className="card-body p-4 text-center">
              <h2 className="mb-3">Ready to Get Started?</h2>
              <p className="mb-4">
                Begin building your knowledge base today and unlock the power of your PDF documents.
              </p>
              <Link to="/register" className="btn btn-light btn-lg px-4">
                <FontAwesomeIcon icon={faUserPlus} className="me-2" />
                Create Your Account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
