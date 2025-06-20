import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faUser, faUsers, faUserPlus, faEdit, 
  faTrash, faSpinner, faExclamationTriangle,
  faCheck, faTimes, faUserShield
} from '@fortawesome/free-solid-svg-icons';
import api from '../api';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'viewer'
  });
  
  // Fetch users on component mount
  useEffect(() => {
    fetchUsers();
  }, []);
  
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/users');
      setUsers(response.data.users || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError('Failed to load users. Please try again later.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await api.post('/api/users', formData);
      setUsers(prev => [...prev, response.data.user]);
      setIsCreatingUser(false);
      setFormData({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: 'viewer'
      });
      setError(null);
    } catch (err) {
      console.error('Error creating user:', err);
      setError(err.response?.data?.error || 'Failed to create user. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await api.put(`/api/users/${editingUser}`, formData);
      setUsers(prev => prev.map(user => 
        user.id === editingUser ? response.data.user : user
      ));
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: 'viewer'
      });
      setError(null);
    } catch (err) {
      console.error('Error updating user:', err);
      setError(err.response?.data?.error || 'Failed to update user. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }
    
    try {
      setLoading(true);
      await api.delete(`/api/users/${userId}`);
      setUsers(prev => prev.filter(user => user.id !== userId));
      setError(null);
    } catch (err) {
      console.error('Error deleting user:', err);
      setError(err.response?.data?.error || 'Failed to delete user. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const startEditingUser = (user) => {
    setEditingUser(user.id);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',  // Don't set password when editing
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      role: user.role || 'viewer'
    });
  };
  
  if (loading && users.length === 0) {
    return (
      <div className="container py-5 text-center">
        <FontAwesomeIcon icon={faSpinner} spin size="3x" className="text-primary mb-3" />
        <h3>Loading users...</h3>
      </div>
    );
  }
  
  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>
          <FontAwesomeIcon icon={faUsers} className="me-2" />
          User Management
        </h1>
        <button 
          className="btn btn-primary" 
          onClick={() => setIsCreatingUser(true)}
          disabled={isCreatingUser}
        >
          <FontAwesomeIcon icon={faUserPlus} className="me-2" />
          Add User
        </button>
      </div>
      
      {error && (
        <div className="alert alert-danger d-flex align-items-center mb-4">
          <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
          <div>{error}</div>
          <button 
            type="button" 
            className="btn-close ms-auto" 
            onClick={() => setError(null)}
            aria-label="Close"
          ></button>
        </div>
      )}
      
      {isCreatingUser && (
        <div className="card mb-4">
          <div className="card-header bg-primary text-white">
            <h5 className="mb-0">
              <FontAwesomeIcon icon={faUserPlus} className="me-2" />
              Create New User
            </h5>
          </div>
          <div className="card-body">
            <form onSubmit={handleCreateUser}>
              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label">Username</label>
                  <input
                    type="text"
                    className="form-control"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className="form-control"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Password</label>
                  <input
                    type="password"
                    className="form-control"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Role</label>
                  <select
                    className="form-select"
                    name="role"
                    value={formData.role}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="viewer">Viewer</option>
                    <option value="editor">Editor</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div className="col-md-6">
                  <label className="form-label">First Name</label>
                  <input
                    type="text"
                    className="form-control"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Last Name</label>
                  <input
                    type="text"
                    className="form-control"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-12 d-flex justify-content-end">
                  <button
                    type="button"
                    className="btn btn-secondary me-2"
                    onClick={() => {
                      setIsCreatingUser(false);
                      setFormData({
                        username: '',
                        email: '',
                        password: '',
                        first_name: '',
                        last_name: '',
                        role: 'viewer'
                      });
                    }}
                  >
                    <FontAwesomeIcon icon={faTimes} className="me-2" />
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? (
                      <FontAwesomeIcon icon={faSpinner} spin className="me-2" />
                    ) : (
                      <FontAwesomeIcon icon={faCheck} className="me-2" />
                    )}
                    Create User
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
      
      <div className="card">
        <div className="table-responsive">
          <table className="table table-hover mb-0">
            <thead className="table-light">
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Name</th>
                <th>Role</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-4">
                    <FontAwesomeIcon icon={faUser} className="me-2" />
                    No users found
                  </td>
                </tr>
              ) : (
                users.map(user => (
                  <tr key={user.id}>
                    <td>
                      <div className="d-flex align-items-center">
                        <FontAwesomeIcon 
                          icon={user.is_admin ? faUserShield : faUser} 
                          className={`me-2 ${user.is_admin ? 'text-danger' : 'text-primary'}`} 
                        />
                        {user.username}
                      </div>
                    </td>
                    <td>{user.email}</td>
                    <td>{user.first_name} {user.last_name}</td>
                    <td>
                      <span className={`badge ${
                        user.role === 'admin' ? 'bg-danger' : 
                        user.role === 'editor' ? 'bg-success' : 
                        'bg-info'
                      }`}>
                        {user.role || 'viewer'}
                      </span>
                    </td>
                    <td>{user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
                    <td>
                      <div className="btn-group">
                        <button 
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => startEditingUser(user)}
                        >
                          <FontAwesomeIcon icon={faEdit} />
                        </button>
                        <button 
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => handleDeleteUser(user.id)}
                        >
                          <FontAwesomeIcon icon={faTrash} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {editingUser && (
        <div className="modal fade show" style={{ display: 'block' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header bg-primary text-white">
                <h5 className="modal-title">Edit User</h5>
                <button 
                  type="button" 
                  className="btn-close btn-close-white" 
                  onClick={() => setEditingUser(null)}
                ></button>
              </div>
              <div className="modal-body">
                <form onSubmit={handleUpdateUser}>
                  <div className="mb-3">
                    <label className="form-label">Username</label>
                    <input
                      type="text"
                      className="form-control"
                      name="username"
                      value={formData.username}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Email</label>
                    <input
                      type="email"
                      className="form-control"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Password (leave blank to keep current)</label>
                    <input
                      type="password"
                      className="form-control"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Role</label>
                    <select
                      className="form-select"
                      name="role"
                      value={formData.role}
                      onChange={handleInputChange}
                      required
                    >
                      <option value="viewer">Viewer</option>
                      <option value="editor">Editor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">First Name</label>
                      <input
                        type="text"
                        className="form-control"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleInputChange}
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Last Name</label>
                      <input
                        type="text"
                        className="form-control"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleInputChange}
                      />
                    </div>
                  </div>
                  <div className="d-flex justify-content-end">
                    <button
                      type="button"
                      className="btn btn-secondary me-2"
                      onClick={() => setEditingUser(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      {loading ? (
                        <FontAwesomeIcon icon={faSpinner} spin className="me-2" />
                      ) : (
                        <FontAwesomeIcon icon={faCheck} className="me-2" />
                      )}
                      Update User
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <div className="modal-backdrop fade show"></div>
        </div>
      )}
    </div>
  );
};

export default Users;
