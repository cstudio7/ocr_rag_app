import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faDatabase, faTrash, faEye, faDownload, faSearch, 
  faExclamationTriangle, faFolder, faFolderPlus, faHome,
  faArrowRight, faEdit, faCheck, faTimes
} from '@fortawesome/free-solid-svg-icons';
import { Link } from 'react-router-dom';

const Manage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [deleteInProgress, setDeleteInProgress] = useState(false);
  
  // Folder management states
  const [folders, setFolders] = useState([]);
  const [currentFolder, setCurrentFolder] = useState('all');
  const [newFolderName, setNewFolderName] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [movingDocuments, setMovingDocuments] = useState(false);
  const [targetFolder, setTargetFolder] = useState('');
  const [editingFolder, setEditingFolder] = useState(null);
  const [editFolderName, setEditFolderName] = useState('');

  useEffect(() => {
    fetchDocuments();
    fetchFolders();
  }, []);

  const fetchFolders = async () => {
    try {
      const response = await fetch('/api/folders');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch folders: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      setFolders(data.folders || []);
    } catch (err) {
      console.error('Error fetching folders:', err);
      setError(`Failed to load folders: ${err.message}`);
    }
  };

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const url = currentFolder === 'all' 
        ? '/api/documents' 
        : `/api/documents?folder=${encodeURIComponent(currentFolder)}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.documents) {
        // Transform the data to match our component's expected format
        const formattedDocs = data.documents.map(doc => ({
          id: doc.doc_id || doc[0],
          title: doc.doc_id || doc[0],
          filename: doc.doc_id || doc[0],
          uploadDate: doc.upload_date || new Date().toISOString().split('T')[0],
          size: doc.size || Math.round((Math.random() * 5 + 1) * 10) / 10,
          pages: doc.chunk_count || doc[1] || Math.floor(Math.random() * 100 + 10),
          folder: doc.folder || 'Uncategorized'
        }));
        
        setDocuments(formattedDocs);
      } else {
        setDocuments([]);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError(err.message);
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
      const response = await fetch('/api/folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newFolderName })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create folder: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      setFolders([...folders, data.folder]);
      setNewFolderName('');
      setIsCreatingFolder(false);
    } catch (err) {
      console.error('Error creating folder:', err);
      setError(`Failed to create folder: ${err.message}`);
    }
  };

  const handleEditFolder = async (folderId) => {
    if (!editFolderName.trim()) {
      setError('Folder name cannot be empty');
      return;
    }
    
    try {
      const response = await fetch(`/api/folders/${folderId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: editFolderName })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update folder: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      setFolders(folders.map(folder => 
        folder.id === folderId ? { ...folder, name: editFolderName } : folder
      ));
      setEditingFolder(null);
      setEditFolderName('');
    } catch (err) {
      console.error('Error updating folder:', err);
      setError(`Failed to update folder: ${err.message}`);
    }
  };

  const handleDeleteFolder = async (folderId) => {
    if (!window.confirm('Are you sure you want to delete this folder? Documents in this folder will be moved to Uncategorized.')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/folders/${folderId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete folder: ${response.status} ${response.statusText}`);
      }
      
      setFolders(folders.filter(folder => folder.id !== folderId));
      if (currentFolder === folderId) {
        setCurrentFolder('all');
        fetchDocuments();
      }
    } catch (err) {
      console.error('Error deleting folder:', err);
      setError(`Failed to delete folder: ${err.message}`);
    }
  };

  const handleMoveDocuments = async () => {
    if (!targetFolder || selectedDocuments.length === 0) {
      return;
    }
    
    setMovingDocuments(true);
    
    try {
      const response = await fetch('/api/move-documents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          document_ids: selectedDocuments,
          folder_id: targetFolder
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to move documents: ${response.status} ${response.statusText}`);
      }
      
      // Refresh documents
      fetchDocuments();
      setSelectedDocuments([]);
      setTargetFolder('');
    } catch (err) {
      console.error('Error moving documents:', err);
      setError(`Failed to move documents: ${err.message}`);
    } finally {
      setMovingDocuments(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const filteredDocuments = documents.filter(doc => 
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelectDocument = (id) => {
    setSelectedDocuments(prev => {
      if (prev.includes(id)) {
        return prev.filter(docId => docId !== id);
      } else {
        return [...prev, id];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedDocuments.length === filteredDocuments.length) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(filteredDocuments.map(doc => doc.id));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedDocuments.length === 0) return;
    
    if (window.confirm(`Are you sure you want to delete ${selectedDocuments.length} document(s)? This action cannot be undone.`)) {
      setDeleteInProgress(true);
      
      try {
        // Delete documents one by one to handle potential errors better
        for (const docId of selectedDocuments) {
          await deleteDocument(docId);
        }
        
        // Refresh the document list
        fetchDocuments();
        setSelectedDocuments([]);
      } catch (err) {
        console.error('Error deleting documents:', err);
        setError(`Failed to delete some documents: ${err.message}`);
      } finally {
        setDeleteInProgress(false);
      }
    }
  };
  
  const deleteDocument = async (docId) => {
    const response = await fetch('/api/delete-document', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ doc_id: docId })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete document ${docId}: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  };
  
  const handleViewDocument = (docId) => {
    // Open document in a new tab or navigate to a view page
    window.open(`/view/${docId}`, '_blank');
  };
  
  const handleDownloadDocument = async (docId) => {
    try {
      const response = await fetch(`/api/download-document/${docId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to download document: ${response.status} ${response.statusText}`);
      }
      
      // Create a blob from the response
      const blob = await response.blob();
      
      // Create a download link and trigger it
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${docId}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading document:', err);
      alert(`Failed to download document: ${err.message}`);
    }
  };

  return (
    <div className="manage-page">
      <div className="card shadow mb-4">
        <div className="card-body p-4">
          <h2 className="mb-4">
            <FontAwesomeIcon icon={faDatabase} className="me-2" />
            Manage Documents
          </h2>
          
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
          
          {/* Folder Navigation */}
          <div className="row mb-4">
            <div className="col-md-3">
              <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">Folders</h5>
                  <button 
                    className="btn btn-sm btn-primary" 
                    onClick={() => setIsCreatingFolder(true)}
                    title="Create new folder"
                  >
                    <FontAwesomeIcon icon={faFolderPlus} />
                  </button>
                </div>
                <div className="list-group list-group-flush">
                  <button 
                    className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${currentFolder === 'all' ? 'active' : ''}`}
                    onClick={() => {
                      setCurrentFolder('all');
                      fetchDocuments();
                    }}
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
                    <div 
                      key={folder.id}
                      className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${currentFolder === folder.id ? 'active' : ''}`}
                    >
                      {editingFolder === folder.id ? (
                        <div className="d-flex w-100">
                          <input
                            type="text"
                            className="form-control form-control-sm me-2"
                            value={editFolderName}
                            onChange={(e) => setEditFolderName(e.target.value)}
                            autoFocus
                          />
                          <button 
                            className="btn btn-sm btn-success me-1"
                            onClick={() => handleEditFolder(folder.id)}
                          >
                            <FontAwesomeIcon icon={faCheck} />
                          </button>
                          <button 
                            className="btn btn-sm btn-secondary"
                            onClick={() => {
                              setEditingFolder(null);
                              setEditFolderName('');
                            }}
                          >
                            <FontAwesomeIcon icon={faTimes} />
                          </button>
                        </div>
                      ) : (
                        <>
                          <div 
                            className="folder-name"
                            onClick={() => {
                              setCurrentFolder(folder.id);
                              fetchDocuments();
                            }}
                          >
                            <FontAwesomeIcon icon={faFolder} className="me-2" />
                            {folder.name}
                          </div>
                          <div>
                            <span className="badge bg-primary rounded-pill me-2">
                              {documents.filter(doc => doc.folder === folder.id).length}
                            </span>
                            <button 
                              className="btn btn-sm btn-outline-secondary me-1"
                              onClick={() => {
                                setEditingFolder(folder.id);
                                setEditFolderName(folder.name);
                              }}
                              title="Edit folder"
                            >
                              <FontAwesomeIcon icon={faEdit} />
                            </button>
                            <button 
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => handleDeleteFolder(folder.id)}
                              title="Delete folder"
                            >
                              <FontAwesomeIcon icon={faTrash} />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
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
              <div className="d-flex justify-content-between align-items-center mb-4">
                <div className="input-group" style={{ maxWidth: '400px' }}>
                  <span className="input-group-text">
                    <FontAwesomeIcon icon={faSearch} />
                  </span>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={handleSearch}
                  />
                </div>
                
                <div className="d-flex gap-2">
                  {selectedDocuments.length > 0 && (
                    <>
                      <div className="dropdown">
                        <button 
                          className="btn btn-outline-primary dropdown-toggle" 
                          type="button" 
                          id="moveToFolderDropdown" 
                          data-bs-toggle="dropdown" 
                          aria-expanded="false"
                          disabled={movingDocuments}
                        >
                          {movingDocuments ? (
                            <>
                              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                              Moving...
                            </>
                          ) : (
                            <>
                              <FontAwesomeIcon icon={faArrowRight} className="me-2" />
                              Move to Folder
                            </>
                          )}
                        </button>
                        <ul className="dropdown-menu" aria-labelledby="moveToFolderDropdown">
                          {folders.map(folder => (
                            <li key={folder.id}>
                              <button 
                                className="dropdown-item" 
                                onClick={() => {
                                  setTargetFolder(folder.id);
                                  handleMoveDocuments();
                                }}
                              >
                                <FontAwesomeIcon icon={faFolder} className="me-2" />
                                {folder.name}
                              </button>
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <button
                        className="btn btn-danger"
                        onClick={handleDeleteSelected}
                        disabled={deleteInProgress}
                      >
                        {deleteInProgress ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Deleting...
                          </>
                        ) : (
                          <>
                            <FontAwesomeIcon icon={faTrash} className="me-2" />
                            Delete Selected ({selectedDocuments.length})
                          </>
                        )}
                      </button>
                    </>
                  )}
                  
                  <Link to="/upload" className="btn btn-primary">
                    <FontAwesomeIcon icon={faDownload} className="me-2" />
                    Upload New
                  </Link>
                </div>
              </div>
              
              {loading ? (
                <div className="text-center my-5">
                  <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className="mt-3">Loading documents...</p>
                </div>
              ) : (
                <>
                  {filteredDocuments.length === 0 ? (
                    <div className="alert alert-info">
                      {searchTerm ? `No documents matching "${searchTerm}"` : 'No documents found'}
                    </div>
                  ) : (
                    <div className="table-responsive">
                      <table className="table table-hover">
                        <thead className="table-light">
                          <tr>
                            <th>
                              <div className="form-check">
                                <input
                                  className="form-check-input"
                                  type="checkbox"
                                  checked={selectedDocuments.length === filteredDocuments.length && filteredDocuments.length > 0}
                                  onChange={handleSelectAll}
                                />
                              </div>
                            </th>
                            <th>Title</th>
                            <th>Filename</th>
                            <th>Folder</th>
                            <th>Upload Date</th>
                            <th>Size</th>
                            <th>Pages/Chunks</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredDocuments.map(doc => (
                            <tr key={doc.id}>
                              <td>
                                <div className="form-check">
                                  <input
                                    className="form-check-input"
                                    type="checkbox"
                                    checked={selectedDocuments.includes(doc.id)}
                                    onChange={() => handleSelectDocument(doc.id)}
                                  />
                                </div>
                              </td>
                              <td>{doc.title}</td>
                              <td>{doc.filename}</td>
                              <td>
                                <span className="badge bg-info text-dark">
                                  <FontAwesomeIcon icon={faFolder} className="me-1" />
                                  {folders.find(f => f.id
