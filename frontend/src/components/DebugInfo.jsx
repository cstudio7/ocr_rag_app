import React from 'react';

const DebugInfo = ({ 
  currentFolder, 
  folders, 
  documents, 
  onDebugFolderIssue, 
  onAssignFolders, 
  onResetFolders,
  onCheckDocuments,
  onRecoverDocuments
}) => {
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }
  
  return (
    <div className="card mt-4">
      <div className="card-header">Debug Information</div>
      <div className="card-body">
        <div className="mb-3">
          <button 
            className="btn btn-sm btn-warning me-2"
            onClick={onDebugFolderIssue}
          >
            Debug Folder Issue
          </button>
          <button 
            className="btn btn-sm btn-primary me-2"
            onClick={onAssignFolders}
          >
            Assign Documents to Folders
          </button>
          <button 
            className="btn btn-sm btn-danger me-2"
            onClick={onResetFolders}
          >
            Reset Document Folders
          </button>
          <button 
            className="btn btn-sm btn-info me-2"
            onClick={onCheckDocuments}
          >
            Check Documents Exist
          </button>
          <button 
            className="btn btn-sm btn-danger"
            onClick={onRecoverDocuments}
          >
            Recover Documents
          </button>
        </div>
        <h6>Current Folder: {currentFolder}</h6>
        <h6>Folders:</h6>
        <pre className="bg-light p-2" style={{maxHeight: '200px', overflow: 'auto'}}>
          {JSON.stringify(folders, null, 2)}
        </pre>
        <h6>Documents:</h6>
        <pre className="bg-light p-2" style={{maxHeight: '200px', overflow: 'auto'}}>
          {JSON.stringify(documents, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default DebugInfo;
