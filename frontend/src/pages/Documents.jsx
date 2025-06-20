import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFileAlt, faTrash, faSpinner, faExclamationTriangle, 
  faFolder, faFolderPlus, faHome, faSearch, faFilter, 
  faPlus, faDownload, faEdit, faSyncAlt, faTimes, faCheck,
  faWrench
} from '@fortawesome/free-solid-svg-icons';
import { Link } from 'react-router-dom';
import api from '../api';
import DebugInfo from '../components/DebugInfo';

// Use a simple alert function if toast is not available
const showNotification = (message, type = 'info') => {
  if (window.toast) {
    window.toast[type](message);
  } else {
    alert(message);
  }
};

const Documents = () => {
  // Document states
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteInProgress, setDeleteInProgress] = useState({});
  
  // Folder states
  const [folders, setFolders] = useState([]);
  const [currentFolder, setCurrentFolder] = useState('all');
  const [newFolderName, setNewFolderName] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  useEffect(() => {
    fetchDocuments();
    fetchFolders();
  }, [currentFolder]);

  const fetchFolders = async () => {
    try {
      const response = await api.get('/api/folders');
      setFolders(response.data.folders || []);
    } catch (err) {
      console.error('Error fetching folders:', err);
      setError('Failed to load folders. Please try again later.');
    }
  };

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      
      // Build query parameters
      let url = '/api/documents';
      const params = new URLSearchParams();
      
      if (currentFolder !== 'all') {
        params.append('folder', currentFolder);
      }
      
      if (dateFilter !== 'all') {
        params.append('date_filter', dateFilter);
      }
      
      if (sortBy) {
        params.append('sort_by', sortBy);
      }
      
      // Add a timestamp to prevent caching
      params.append('_t', Date.now());
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await api.get(url);
      console.log('API response:', response.data);
      
      // Handle different response formats
      if (response.data.documents) {
        // Check if documents are in array format [doc_id, count] or object format {doc_id, ...}
        const isArrayFormat = Array.isArray(response.data.documents[0]);
        
        if (isArrayFormat) {
          // Convert array format to object format
          const formattedDocs = response.data.documents.map(doc => {
            // If doc is [doc_id, count]
            const docId = doc[0];
            const chunkCount = doc[1];
            
            return {
              doc_id: docId,
              chunk_count: chunkCount,
              upload_date: new Date().toISOString(),
              folder: 'uncategorized' // Default folder
            };
          });
          
          setDocuments(formattedDocs);
        } else {
          // Already in object format
          setDocuments(response.data.documents || []);
        }
        
        // Update folder counts if provided
        if (response.data.folder_counts) {
          setFolders(prevFolders => {
            return prevFolders.map(folder => ({
              ...folder,
              document_count: response.data.folder_counts[folder.id] || 0
            }));
          });
        }
      } else {
        setDocuments([]);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      setError('Folder name cannot be empty');
      return;
    }
    
    try {
      const response = await api.post('/api/folders', { name: newFolderName });
      setFolders([...folders, response.data.folder]);
      setNewFolderName('');
      setIsCreatingFolder(false);
    } catch (err) {
      console.error('Error creating folder:', err);
      setError('Failed to create folder. Please try again.');
    }
  };

  const handleDelete = async (documentId) => {
    if (window.confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      try {
        setDeleteInProgress(prev => ({ ...prev, [documentId]: true }));
        await api.post('/api/delete-document', { doc_id: documentId });
        setDocuments(documents.filter(doc => doc.doc_id !== documentId));
      } catch (err) {
        console.error('Error deleting document:', err);
        alert('Failed to delete document. Please try again.');
      } finally {
        setDeleteInProgress(prev => ({ ...prev, [documentId]: false }));
      }
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setDateFilter('all');
    setSortBy('newest');
  };

  const handleDownload = async (documentId) => {
    try {
      window.open(`/api/download-document/${documentId}`, '_blank');
    } catch (err) {
      console.error('Error downloading document:', err);
      alert('Failed to download document. Please try again.');
    }
  };

  // Add this function to refresh both documents and folders after operations
  const refreshData = async () => {
    await fetchFolders();
    await fetchDocuments();
  };

  const handleMoveToFolder = async (docId, folderId) => {
    try {
      setLoading(true);
      console.log(`Moving document ${docId} to folder ${folderId}`);
      
      // Call API to move document
      const response = await api.post('/api/documents/move', {
        doc_id: docId,
        folder_id: folderId
      });
      
      if (response.data.success) {
        // Update local state immediately
        setDocuments(prevDocs => 
          prevDocs.map(doc => 
            doc.doc_id === docId 
              ? { ...doc, folder: folderId } 
              : doc
          )
        );
        
        // Show success message
        showNotification('Document moved successfully', 'success');
        
        // Refresh documents to get updated data
        fetchDocuments();
      } else {
        throw new Error(response.data.error || 'Failed to move document');
      }
    } catch (err) {
      console.error('Error moving document:', err);
      showNotification('Failed to move document. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add this function to force a complete refresh
  const forceRefresh = async () => {
    setLoading(true);
    try {
      // Clear any cached data
      setDocuments([]);
      setFolders([]);
      
      // Fetch fresh data
      await fetchFolders();
      await fetchDocuments();
    } catch (err) {
      console.error('Error refreshing data:', err);
      setError('Failed to refresh data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Add this function to help debug the folder issue
  const debugFolderIssue = async () => {
    try {
      console.log("Debugging folder issue...");
      
      // Get the documents.json file directly
      const response = await api.get('/api/debug/documents-json');
      console.log("Documents.json content:", response.data);
      
      // Check if the file has the correct folder information
      const hasCorrectFolders = response.data.documents.some(doc => doc.folder !== "uncategorized");
      console.log("Has correct folders:", hasCorrectFolders);
      
      // Show the result
      showNotification(`Documents.json has ${hasCorrectFolders ? 'correct' : 'incorrect'} folder information`, 'info');
    } catch (err) {
      console.error("Error debugging folder issue:", err);
      showNotification("Error debugging folder issue", 'error');
    }
  };

  // Add this function to reset document folders
  const resetDocumentFolders = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/reset-document-folders');
      
      if (response.data.success) {
        showNotification('Document folders reset successfully', 'success');
        // Refresh data
        await fetchFolders();
        await fetchDocuments();
      } else {
        throw new Error(response.data.error || 'Failed to reset document folders');
      }
    } catch (err) {
      console.error('Error resetting document folders:', err);
      showNotification('Failed to reset document folders. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Function to directly assign documents to folders
  const assignDocumentsToFolders = async () => {
    try {
      setLoading(true);
      
      // Create assignments based on document naming patterns
      const assignments = documents.map(doc => {
        const docId = doc.doc_id;
        let folderId = "uncategorized";
        
        // Python documents
        if (docId.startsWith("Python_")) {
          const pythonFolder = folders.find(f => f.name === "Python");
          if (pythonFolder) folderId = pythonFolder.id;
        }
        // Software documents
        else if (docId.startsWith("Software_") || docId === "Sofatware_Unit-3") {
          const softwareFolder = folders.find(f => f.name === "Software");
          if (softwareFolder) folderId = softwareFolder.id;
        }
        // Big data documents
        else if (docId.includes("Big_Data") || docId.includes("BIG_DATA")) {
          const bigDataFolder = folders.find(f => f.name === "Big data");
          if (bigDataFolder) folderId = bigDataFolder.id;
        }
        // Cloud Computing documents
        else if (docId.toLowerCase().includes("cloud")) {
          const cloudFolder = folders.find(f => f.name === "Cloud Computing");
          if (cloudFolder) folderId = cloudFolder.id;
        }
        // Official documents
        else if (docId.includes("OFFICIAL") || docId === "Digital_Notes_DA") {
          const officialFolder = folders.find(f => f.name === "Official");
          if (officialFolder) folderId = officialFolder.id;
        }
        
        return { doc_id: docId, folder_id: folderId };
      });
      
      console.log("Assigning documents to folders:", assignments);
      
      // Send the assignments to the backend
      const response = await api.post('/api/documents/assign-folders', {
        assignments: assignments
      });
      
      if (response.data.success) {
        showNotification(response.data.message, 'success');
        // Refresh data
        await fetchFolders();
        await fetchDocuments();
      } else {
        throw new Error(response.data.error || 'Failed to assign document folders');
      }
    } catch (err) {
      console.error('Error assigning document folders:', err);
      showNotification('Failed to assign document folders. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add this function to fix document folders
  const fixDocumentFolders = async () => {
    try {
      setLoading(true);
      
      // Call the fix endpoint
      const response = await api.post('/api/fix-document-folders');
      
      if (response.data.success) {
        showNotification(response.data.message, 'success');
        
        // Refresh data
        await fetchFolders();
        await fetchDocuments();
      } else {
        throw new Error(response.data.error || 'Failed to fix document folders');
      }
    } catch (err) {
      console.error('Error fixing document folders:', err);
      showNotification('Failed to fix document folders. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add this function to fix all document folders
  const fixAllDocumentFolders = async () => {
    try {
      setLoading(true);
      showNotification('Fixing document folders...', 'info');
      
      // Call the fix endpoint
      const response = await api.post('/api/fix-document-folders');
      
      if (response.data.success) {
        showNotification(response.data.message, 'success');
        
        // Refresh data
        await fetchFolders();
        await fetchDocuments();
      } else {
        throw new Error(response.data.error || 'Failed to fix document folders');
      }
    } catch (err) {
      console.error('Error fixing document folders:', err);
      showNotification('Failed to fix document folders. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add this function to recover documents
  const recoverDocuments = async () => {
    try {
      setLoading(true);
      showNotification('Attempting to recover documents...', 'info');
      
      const response = await api.post('/api/recover-documents');
      
      if (response.data.success) {
        showNotification(response.data.message, 'success');
        console.log('Documents to recover:', response.data.recovered_documents);
        
        // Refresh data
        await forceRefresh();
      } else {
        throw new Error(response.data.error || 'Failed to recover documents');
      }
    } catch (err) {
      console.error('Error recovering documents:', err);
      showNotification('Failed to recover documents. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add this function to check if documents exist in ChromaDB
  const checkDocumentsExist = async () => {
    try {
      setLoading(true);
      showNotification('Checking documents in database...', 'info');
      
      const response = await api.get('/api/debug/check-documents');
      
      if (response.data.status === 'ok') {
        showNotification(`Found ${response.data.document_count} documents (${response.data.chunk_count} chunks)`, 'success');
        console.log('Sample documents:', response.data.sample_documents);
        
        // If documents exist but aren't showing, force a refresh
        if (response.data.document_count > 0 && documents.length === 0) {
          await forceRefresh();
        }
      } else {
        showNotification('No documents found in database', 'error');
      }
    } catch (err) {
      console.error('Error checking documents:', err);
      showNotification('Failed to check documents', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Filter documents based on search term and current folder
  const filteredDocuments = documents.filter(doc => {
    // First filter by folder if not showing all
    if (currentFolder !== 'all' && doc.folder !== currentFolder) {
      return false;
    }
    
    // Then filter by search term
    return doc.doc_id && doc.doc_id.toLowerCase().includes(searchTerm.toLowerCase());
  });

  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Helper function to get folder name from folder ID
  const getFolderName = (folderId) => {
    if (!folderId) return 'Uncategorized';
    
    const folder = folders.find(f => f.id === folderId);
    return folder ? folder.name : 'Uncategorized';
  };

  // Add this function to update document folder badges
  const updateDocumentFolderBadges = () => {
    // Get all document folder badges
    const folderBadges = document.querySelectorAll('.badge.bg-info.text-dark');
    
    // Update each badge with the correct folder name
    folderBadges.forEach(badge => {
      const docRow = badge.closest('tr');
      if (!docRow) return;
      
      // Get document ID from the row
      const docIdElement = docRow.querySelector('.fw-bold');
      if (!docIdElement) return;
      
      const docId = docIdElement.textContent;
      
      // Find document in our state
      const doc = documents.find(d => d.doc_id === docId);
      if (!doc) return;
      
      // Update badge text with folder name
      const folderName = getFolderName(doc.folder);
      badge.innerHTML = `<i class="fas fa-folder me-1"></i> ${folderName}`;
    });
  };

  // Calculate folder counts
  const calculateFolderCounts = () => {
    const counts = {};
    
    // Initialize counts for all folders
    folders.forEach(folder => {
      counts[folder.id] = 0;
    });
    
    // Count documents per folder
    documents.forEach(doc => {
      const folderId = doc.folder || 'uncategorized';
      if (counts[folderId] !== undefined) {
        counts[folderId]++;
      } else {
        counts[folderId] = 1;
      }
    });
    
    // Update folder objects with counts
    return folders.map(folder => ({
      ...folder,
      document_count: counts[folder.id] || 0
    }));
  };

  // Use this in useEffect
  useEffect(() => {
    if (documents.length > 0 && folders.length > 0) {
      const foldersWithCounts = calculateFolderCounts();
      setFolders(foldersWithCounts);
    }
  }, [documents]);

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <FontAwesomeIcon icon={faSpinner} spin size="3x" className="text-primary mb-3" />
        <h3>Loading documents...</h3>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">
      <div className="row">
        <div className="col-md-3">
          <div className="card shadow-sm mb-4">
            <div className="card-header bg-light d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faFolder} className="me-2" />
                Folders
              </h5>
              <div>
                <button 
                  className="btn btn-sm btn-outline-secondary me-2" 
                  onClick={forceRefresh}
                  title="Refresh folders"
                >
                  <FontAwesomeIcon icon={faSyncAlt} />
                </button>
                <button 
                  className="btn btn-sm btn-primary" 
                  onClick={() => setIsCreatingFolder(true)}
                  title="Create new folder"
                >
                  <FontAwesomeIcon icon={faFolderPlus} />
                </button>
              </div>
            </div>
            <div className="list-group list-group-flush">
              <button 
                className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${currentFolder === 'all' ? 'active' : ''}`}
                onClick={() => setCurrentFolder('all')}
              >
                <div>
                  <FontAwesomeIcon icon={faHome} className="me-2" />
                  All Documents
                </div>
                <span className="badge bg-primary rounded-pill">
                  {documents.length}
                </span>
              </button>
              
              {folders.map(folder => (
                <button 
                  key={folder.id || `folder-${folder.name}`}
                  className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${currentFolder === folder.id ? 'active' : ''}`}
                  onClick={() => setCurrentFolder(folder.id)}
                >
                  <div>
                    <FontAwesomeIcon icon={faFolder} className="me-2" />
                    {folder.name}
                  </div>
                  <span className="badge bg-primary rounded-pill">
                    {folder.document_count || documents.filter(doc => doc.folder === folder.id).length}
                  </span>
                </button>
              ))}
              
              {isCreatingFolder && (
                <div className="list-group-item">
                  <div className="d-flex">
                    <input
                      type="text"
                      className="form-control form-control-sm me-2"
                      placeholder="New folder name"
                      value={newFolderName}
                      onChange={(e) => setNewFolderName(e.target.value)}
                      autoFocus
                    />
                    <button 
                      className="btn btn-sm btn-success me-1"
                      onClick={handleCreateFolder}
                    >
                      <FontAwesomeIcon icon={faCheck} />
                    </button>
                    <button 
                      className="btn btn-sm btn-secondary"
                      onClick={() => {
                        setIsCreatingFolder(false);
                        setNewFolderName('');
                      }}
                    >
                      <FontAwesomeIcon icon={faTimes} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="col-md-9">
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
          
          <div className="card shadow-sm mb-4">
            <div className="card-header bg-light">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faFilter} className="me-2" />
                Search & Filter
              </h5>
            </div>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-4">
                  <label className="form-label">Document Name</label>
                  <div className="input-group">
                    <span className="input-group-text">
                      <FontAwesomeIcon icon={faSearch} />
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search by document name..."
                      value={searchTerm}
                      onChange={handleSearch}
                    />
                  </div>
                </div>
                
                <div className="col-md-3">
                  <label className="form-label">Upload Date</label>
                  <select 
                    className="form-select"
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                  >
                    <option value="all">All dates</option>
                    <option value="today">Today</option>
                    <option value="week">This week</option>
                    <option value="month">This month</option>
                    <option value="year">This year</option>
                  </select>
                </div>
                
                <div className="col-md-3">
                  <label className="form-label">Sort By</label>
                  <select 
                    className="form-select"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                  >
                    <option value="newest">Newest first</option>
                    <option value="oldest">Oldest first</option>
                    <option value="name_asc">Name (A-Z)</option>
                    <option value="name_desc">Name (Z-A)</option>
                    <option value="size_asc">Size (smallest first)</option>
                    <option value="size_desc">Size (largest first)</option>
                  </select>
                </div>
                
                <div className="col-md-2 d-flex align-items-end">
                  <button 
                    className="btn btn-outline-secondary w-100"
                    onClick={handleClearFilters}
                  >
                    <FontAwesomeIcon icon={faTimes} className="me-2" />
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-5 card shadow-sm">
              <FontAwesomeIcon icon={faFileAlt} size="3x" className="text-muted mb-3" />
              <h3>No Documents Found</h3>
              <p className="text-muted">
                {searchTerm ? `No documents matching "${searchTerm}"` : "You haven't uploaded any documents yet."}
              </p>
              <div className="mt-3">
                <Link to="/upload" className="btn btn-primary">
                  <FontAwesomeIcon icon={faPlus} className="me-2" />
                  Upload New Document
                </Link>
              </div>
            </div>
          ) : (
            <div className="card shadow-sm">
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th></th>
                      <th>Document Name</th>
                      <th>Upload Date</th>
                      <th>Updated</th>
                      <th>Size</th>
                      <th>Pages</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDocuments.map(doc => (
                      <tr key={doc.doc_id || `doc-${Math.random()}`}>
                        <td className="text-center">
                          <div className="pdf-icon">
                            <FontAwesomeIcon icon={faFileAlt} className="text-danger fs-4" />
                          </div>
                        </td>
                        <td>
                          <div className="fw-bold">{doc.doc_id}</div>
                          <div className="badge bg-info text-dark">
                            <FontAwesomeIcon icon={faFolder} className="me-1" />
                            {getFolderName(doc.folder)}
                          </div>
                        </td>
                        <td>{new Date(doc.upload_date || Date.now()).toLocaleDateString()}</td>
                        <td>{new Date(doc.updated_date || doc.upload_date || Date.now()).toLocaleDateString()}</td>
                        <td>{formatFileSize(doc.size)}</td>
                        <td>{doc.page_count || doc.chunk_count || '—'}</td>
                        <td>
                          <div className="btn-group">
                            <button 
                              className="btn btn-sm btn-outline-primary"
                              onClick={() => handleDownload(doc.doc_id)}
                              title="Download"
                            >
                              <FontAwesomeIcon icon={faDownload} />
                            </button>
                            
                            <div className="btn-group">
                              <button 
                                className="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                data-bs-toggle="dropdown"
                                title="Move to folder"
                              >
                                <FontAwesomeIcon icon={faFolder} />
                              </button>
                              <ul className="dropdown-menu">
                                {folders.map(folder => (
                                  <li key={`move-${doc.doc_id}-to-${folder.id || folder.name}`}>
                                    <button 
                                      className="dropdown-item"
                                      onClick={() => handleMoveToFolder(doc.doc_id, folder.id)}
                                    >
                                      <FontAwesomeIcon icon={faFolder} className="me-2" />
                                      {folder.name}
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            </div>
                            
                            <button 
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => handleDelete(doc.doc_id)}
                              disabled={deleteInProgress[doc.doc_id]}
                              title="Delete"
                            >
                              {deleteInProgress[doc.doc_id] ? (
                                <FontAwesomeIcon icon={faSpinner} spin />
                              ) : (
                                <FontAwesomeIcon icon={faTrash} />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
      <DebugInfo 
        currentFolder={currentFolder}
        folders={folders}
        documents={documents}
        onDebugFolderIssue={debugFolderIssue}
        onAssignFolders={assignDocumentsToFolders}
        onResetFolders={resetDocumentFolders}
        onCheckDocuments={checkDocumentsExist}
        onRecoverDocuments={recoverDocuments}
      />
      <div className="d-flex justify-content-center mt-3">
        <button 
          className="btn btn-sm btn-success me-2"
          onClick={fixDocumentFolders}
        >
          Fix Document Folders
        </button>
        <button 
          className="btn btn-primary"
          onClick={fixAllDocumentFolders}
        >
          <FontAwesomeIcon icon={faWrench} className="me-2" />
          Fix Document Folders
        </button>
        <button 
          className="btn btn-sm btn-danger me-2"
          onClick={recoverDocuments}
        >
          Recover Documents
        </button>
      </div>
    </div>
  );
};

export default Documents;
// Make sure there's nothing after this line
