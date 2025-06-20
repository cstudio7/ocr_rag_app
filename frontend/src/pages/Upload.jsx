import React, { useState, useCallback, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFileUpload, faSpinner, faCheckCircle, faExclamationTriangle, 
  faFilePdf, faFolder, faFolderPlus, faTimes, faCheck 
} from '@fortawesome/free-solid-svg-icons';
import { uploadPdf } from '../api';
import api from '../api';

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [error, setError] = useState('');
  const [processingLogs, setProcessingLogs] = useState([]);
  const [eventSource, setEventSource] = useState(null);
  
  // Folder states
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  useEffect(() => {
    fetchFolders();
  }, []);

  const fetchFolders = async () => {
    try {
      const response = await api.get('/api/folders');
      setFolders(response.data.folders || []);
      // Set default folder to 'uncategorized' if it exists
      const uncategorized = response.data.folders.find(f => f.name.toLowerCase() === 'uncategorized');
      if (uncategorized) {
        setSelectedFolder(uncategorized.id);
      }
    } catch (err) {
      console.error('Error fetching folders:', err);
      setError('Failed to load folders. Please refresh the page.');
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      setError('Folder name cannot be empty');
      return;
    }
    
    try {
      const response = await api.post('/api/folders', { name: newFolderName });
      const newFolder = response.data.folder;
      setFolders([...folders, newFolder]);
      setSelectedFolder(newFolder.id);
      setNewFolderName('');
      setIsCreatingFolder(false);
      setError('');
    } catch (err) {
      console.error('Error creating folder:', err);
      setError(err.response?.data?.error || 'Failed to create folder. Please try again.');
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files).filter(
      file => file.type === 'application/pdf'
    );
    
    if (selectedFiles.length === 0 && e.target.files.length > 0) {
      setError('Please select only PDF files.');
      return;
    }
    
    setFiles(selectedFiles);
    setError('');
    setUploadComplete(false);
    setProcessingLogs([]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    );
    
    if (droppedFiles.length === 0) {
      setError('Please drop only PDF files.');
      return;
    }
    
    setFiles(droppedFiles);
    setError('');
    setUploadComplete(false);
    setProcessingLogs([]);
  };

  const removeFile = (index) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select at least one PDF file to upload.');
      return;
    }
    
    setUploading(true);
    setUploadProgress(0);
    setError('');
    setProcessingLogs([]);
    
    // Create FormData object
    const formData = new FormData();
    files.forEach(file => {
      formData.append('pdfs', file);
    });
    
    // Add folder information if selected
    if (selectedFolder) {
      formData.append('folder_id', selectedFolder);
    }
    
    try {
      // Upload files
      const response = await uploadPdf(formData, (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(percentCompleted);
      });
      
      console.log('Upload response:', response);
      
      // Start listening for progress updates via SSE
      if (eventSource) {
        eventSource.close();
      }
      
      const newEventSource = new EventSource('/api/progress');
      setEventSource(newEventSource);
      
      newEventSource.onmessage = (event) => {
        setProcessingLogs(prev => [...prev, event.data]);
      };
      
      newEventSource.onerror = () => {
        newEventSource.close();
        setEventSource(null);
        setUploading(false);
        setUploadComplete(true);
      };
      
    } catch (err) {
      console.error('Error uploading files:', err);
      setError(err.response?.data?.error || 'An error occurred during upload');
      setUploading(false);
    }
  };

  // Clean up event source on component unmount
  React.useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return (
    <div className="upload-page">
      <div className="card shadow mb-4">
        <div className="card-body p-4">
          <h2 className="mb-4">
            <FontAwesomeIcon icon={faFileUpload} className="me-2" />
            Upload Documents
          </h2>
          
          {error && (
            <div className="alert alert-danger" role="alert">
              <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
              {error}
            </div>
          )}
          
          {uploadComplete && (
            <div className="alert alert-success" role="alert">
              <FontAwesomeIcon icon={faCheckCircle} className="me-2" />
              Files uploaded successfully! Your documents are now indexed and ready for search.
            </div>
          )}
          
          <div 
            className="upload-area p-5 mb-4 border rounded text-center"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            style={{ 
              backgroundColor: '#f8f9fa',
              borderStyle: 'dashed',
              cursor: 'pointer'
            }}
          >
            <FontAwesomeIcon icon={faFileUpload} size="3x" className="text-primary mb-3" />
            <h4>Drag & Drop PDF Files Here</h4>
            <p className="text-muted">or</p>
            <input
              type="file"
              id="fileInput"
              multiple
              accept=".pdf"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <label htmlFor="fileInput" className="btn btn-primary">
              Browse Files
            </label>
          </div>
          
          {files.length > 0 && (
            <div className="selected-files mb-4">
              <h5>Selected Files ({files.length})</h5>
              <ul className="list-group">
                {files.map((file, index) => (
                  <li key={index} className="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                      <FontAwesomeIcon icon={faFilePdf} className="text-danger me-2" />
                      <span className="me-2">{file.name}</span>
                      <small className="text-muted">({formatFileSize(file.size)})</small>
                    </div>
                    <button 
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                    >
                      &times;
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Folder Selection */}
          <div className="mb-4">
            <h5>
              <FontAwesomeIcon icon={faFolder} className="me-2" />
              Select Destination Folder
            </h5>
            
            <div className="row align-items-end">
              <div className="col">
                <select 
                  className="form-select"
                  value={selectedFolder}
                  onChange={(e) => setSelectedFolder(e.target.value)}
                  disabled={uploading || isCreatingFolder}
                >
                  <option value="">-- Select Folder --</option>
                  {folders.map(folder => (
                    <option key={folder.id} value={folder.id}>
                      {folder.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="col-auto">
                <button 
                  className="btn btn-outline-primary"
                  onClick={() => setIsCreatingFolder(true)}
                  disabled={uploading || isCreatingFolder}
                >
                  <FontAwesomeIcon icon={faFolderPlus} className="me-2" />
                  Create New Folder
                </button>
              </div>
            </div>
            
            {isCreatingFolder && (
              <div className="mt-3 p-3 border rounded bg-light">
                <div className="d-flex">
                  <input
                    type="text"
                    className="form-control me-2"
                    placeholder="New folder name"
                    value={newFolderName}
                    onChange={(e) => setNewFolderName(e.target.value)}
                    autoFocus
                  />
                  <button 
                    className="btn btn-success me-1"
                    onClick={handleCreateFolder}
                  >
                    <FontAwesomeIcon icon={faCheck} />
                  </button>
                  <button 
                    className="btn btn-secondary"
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
          
          {uploading && (
            <div className="mb-4">
              <label className="form-label">Upload Progress</label>
              <div className="progress mb-3">
                <div 
                  className="progress-bar progress-bar-striped progress-bar-animated" 
                  role="progressbar" 
                  style={{ width: `${uploadProgress}%` }}
                  aria-valuenow={uploadProgress} 
                  aria-valuemin="0" 
                  aria-valuemax="100"
                >
                  {uploadProgress}%
                </div>
              </div>
              
              {processingLogs.length > 0 && (
                <div className="mt-4">
                  <h5>Processing Logs</h5>
                  <div className="log-container p-3 bg-dark text-light rounded" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {processingLogs.map((log, index) => (
                      <div key={index} className="log-entry">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div className="d-grid">
            <button 
              className="btn btn-primary" 
              onClick={handleUpload}
              disabled={files.length === 0 || uploading}
            >
              {uploading ? (
                <>
                  <FontAwesomeIcon icon={faSpinner} spin className="me-2" />
                  Uploading & Indexing...
                </>
              ) : (
                <>
                  <FontAwesomeIcon icon={faFileUpload} className="me-2" />
                  Upload Files
                </>
              )}
            </button>
          </div>
        </div>
      </div>
      
      <div className="card shadow">
        <div className="card-header">
          <h5 className="mb-0">Tips for Better Results</h5>
        </div>
        <div className="card-body">
          <ul className="mb-0">
            <li>Make sure your PDFs are not password-protected</li>
            <li>For best results, use PDFs with selectable text rather than scanned documents</li>
            <li>Larger PDFs (over 100 pages) may take several minutes to process</li>
            <li>The system will automatically handle duplicate uploads</li>
            <li>You can upload multiple PDFs at once</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Upload;
