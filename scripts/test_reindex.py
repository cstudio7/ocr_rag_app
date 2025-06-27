#!/usr/bin/env python3
"""
Test script to verify reindex functionality works correctly.
This script will help debug the reindex process.
"""

import os
import sys
import glob
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from config import CACHE_DIR, VECTOR_STORE_DIR
from core.indexer import get_chroma_collection, get_file_hash
from models import db, Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def check_document_status(doc_id):
    """Check the current status of a document in cache and vector database."""
    print(f"\n=== Document Status Check: {doc_id} ===")
    
    # Check database record
    document = Document.query.filter_by(doc_id=doc_id).first()
    if document:
        print(f"📄 Database Record: {document.filename}")
        print(f"   - File Path: {document.file_path}")
        print(f"   - Chunk Count: {document.chunk_count}")
        print(f"   - Folder: {document.folder.name if document.folder else 'None'}")
        
        # Check if file exists
        if os.path.exists(document.file_path):
            print(f"   - File exists: ✅")
            file_hash = get_file_hash(document.file_path)
            print(f"   - File hash: {file_hash}")
        else:
            print(f"   - File exists: ❌")
            return
    else:
        print(f"❌ No database record found for {doc_id}")
        return
    
    # Check cache files
    cache_pattern = os.path.join(CACHE_DIR, f"{doc_id}_*.pkl")
    cache_files = glob.glob(cache_pattern)
    print(f"💾 Cache Files: {len(cache_files)}")
    for cache_file in cache_files:
        print(f"   - {os.path.basename(cache_file)}")
    
    # Check vector database
    try:
        collection = get_chroma_collection()
        existing_chunks = collection.get(where={"doc_id": doc_id})
        print(f"🔍 Vector Database Chunks: {len(existing_chunks['ids']) if existing_chunks['ids'] else 0}")
        if existing_chunks['ids']:
            print(f"   - First chunk ID: {existing_chunks['ids'][0]}")
            print(f"   - Last chunk ID: {existing_chunks['ids'][-1]}")
    except Exception as e:
        print(f"❌ Error checking vector database: {e}")

def simulate_reindex_process(doc_id):
    """Simulate the reindex process to see what happens."""
    print(f"\n=== Simulating Reindex Process: {doc_id} ===")
    
    document = Document.query.filter_by(doc_id=doc_id).first()
    if not document:
        print(f"❌ Document {doc_id} not found in database")
        return
    
    print("1. Checking cache files...")
    cache_pattern = os.path.join(CACHE_DIR, f"{doc_id}_*.pkl")
    cache_files = glob.glob(cache_pattern)
    print(f"   Found {len(cache_files)} cache files")
    
    print("2. Checking vector database entries...")
    try:
        collection = get_chroma_collection()
        existing_chunks = collection.get(where={"doc_id": doc_id})
        print(f"   Found {len(existing_chunks['ids']) if existing_chunks['ids'] else 0} vector chunks")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("3. This is what reindex would do:")
    print("   - Clear cache files")
    print("   - Remove vector database entries")
    print("   - Reprocess the PDF file")
    print("   - Generate new embeddings")
    print("   - Store new data in vector database")
    print("   - Update cache with new data")

def list_all_documents():
    """List all documents in the database."""
    print("\n=== All Documents in Database ===")
    documents = Document.query.all()
    for doc in documents:
        print(f"📄 {doc.doc_id} - {doc.filename}")
        print(f"   Path: {doc.file_path}")
        print(f"   Chunks: {doc.chunk_count}")
        print(f"   Folder: {doc.folder.name if doc.folder else 'None'}")
        print()

if __name__ == "__main__":
    from app import app
    
    with app.app_context():
        print("🔍 Reindex Functionality Test")
        print("=" * 50)
        
        # List all documents
        list_all_documents()
        
        # Get first document for testing
        first_doc = Document.query.first()
        if first_doc:
            doc_id = first_doc.doc_id
            print(f"\n🧪 Testing with document: {doc_id}")
            
            # Check current status
            check_document_status(doc_id)
            
            # Simulate reindex process
            simulate_reindex_process(doc_id)
            
            print(f"\n💡 To test reindex, use the web interface or call:")
            print(f"   curl -X POST http://localhost:5000/api/documents/{first_doc.id}/reindex")
        else:
            print("❌ No documents found in database")
