import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faEnvelope, faKey, faSave, faSpinner } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../contexts/AuthContext';

const Profile = () => {
  const { user } = useAuth();
  
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [passwordVisible, setPasswordVisible] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });
    
    // Password validation
    if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
      setMessage({ type: 'danger', text: 'New passwords do not match' });
      setLoading(false);
      return;
    }
    
    // For demo purposes, just simulate an API call
    setTimeout(() => {
      setMessage({ 
        type: 'success', 
        text: 'Profile updated successfully!' 
      });
      setLoading(false);
      
      // Clear password fields
      setFormData(prev => ({
        ...prev,
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }));
    }, 1000);
    
    // In a real app, you would call your API here
    // try {
    //   const response = await fetch('/api/update-profile', {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify(formData),
    //     credentials: 'include'
    //   });
    //   
    //   if (!response.ok) {
    //     const errorData = await response.json();
    //     throw new Error(errorData.error || 'Failed to update profile');
    //   }
    //   
    //   setMessage({ type: 'success', text: 'Profile updated successfully!' });
    // } catch (error) {
    //   setMessage({ type: 'danger', text: error.message });
    // } finally {
    //   setLoading(false);
    // }
  };
  
  const togglePasswordSection = () => {
    setPasswordVisible(!passwordVisible);
  };
  
  return (
    <div className="row justify-content-center">
      <div className="col-md-8 col-lg-6">
        <div className="card shadow">
          <div className="card-body p-4">
            <h2 className="card-title mb-4">
              <FontAwesomeIcon icon={faUser} className="me-2" />
              User Profile
            </h2>
            
            {message.text && (
              <div className={`alert alert-${message.type}`} role="alert">
                {message.text}
              </div>
            )}
            
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label htmlFor="name" className="form-label">
                  <FontAwesomeIcon icon={faUser} className="me-2" />
                  Full Name
                </label>
                <input
                  type="text"
                  className="form-control"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="mb-3">
                <label htmlFor="email" className="form-label">
                  <FontAwesomeIcon icon={faEnvelope} className="me-2" />
                  Email Address
                </label>
                <input
                  type="email"
                  className="form-control"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="mb-4">
                <button 
                  type="button" 
                  className="btn btn-outline-secondary btn-sm"
                  onClick={togglePasswordSection}
                >
                  <FontAwesomeIcon icon={faKey} className="me-2" />
                  {passwordVisible ? 'Hide Password Change' : 'Change Password'}
                </button>
              </div>
              
              {passwordVisible && (
                <div className="password-section border rounded p-3 mb-4 bg-light">
                  <div className="mb-3">
                    <label htmlFor="currentPassword" className="form-label">Current Password</label>
                    <input
                      type="password"
                      className="form-control"
                      id="currentPassword"
                      name="currentPassword"
                      value={formData.currentPassword}
                      onChange={handleChange}
                    />
                  </div>
                  
                  <div className="mb-3">
                    <label htmlFor="newPassword" className="form-label">New Password</label>
                    <input
                      type="password"
                      className="form-control"
                      id="newPassword"
                      name="newPassword"
                      value={formData.newPassword}
                      onChange={handleChange}
                    />
                  </div>
                  
                  <div className="mb-3">
                    <label htmlFor="confirmPassword" className="form-label">Confirm New Password</label>
                    <input
                      type="password"
                      className="form-control"
                      id="confirmPassword"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                    />
                  </div>
                </div>
              )}
              
              <div className="d-grid">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <FontAwesomeIcon icon={faSpinner} spin className="me-2" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={faSave} className="me-2" />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;