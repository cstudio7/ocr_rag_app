#!/usr/bin/env python3
"""
Script to update chunk counts for all documents in the database.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import db, Document
from core.search import get_chroma_collection
import logging

def update_chunk_counts():
    """Update chunk counts for all documents."""
    print("🔄 Updating chunk counts for all documents...")
    
    with app.app_context():
        try:
            # Get the ChromaDB collection
            collection = get_chroma_collection()
            
            # Get all documents from ChromaDB
            all_data = collection.get()
            
            if not all_data or not all_data.get('ids'):
                print("❌ No documents found in ChromaDB")
                return False
            
            # Count chunks per document
            doc_chunk_counts = {}
            for metadata in all_data['metadatas']:
                doc_id = metadata.get('doc_id')
                if doc_id:
                    doc_chunk_counts[doc_id] = doc_chunk_counts.get(doc_id, 0) + 1
            
            print(f"📊 Found chunk counts for {len(doc_chunk_counts)} documents")
            
            # Update database records
            updated_count = 0
            for doc_id, chunk_count in doc_chunk_counts.items():
                document = Document.query.filter_by(doc_id=doc_id).first()
                if document:
                    if document.chunk_count != chunk_count:
                        document.chunk_count = chunk_count
                        updated_count += 1
                        print(f"   📝 Updated {doc_id}: {chunk_count} chunks")
                    else:
                        print(f"   ✅ {doc_id}: {chunk_count} chunks (already correct)")
                else:
                    print(f"   ⚠️  Document {doc_id} not found in database")
            
            if updated_count > 0:
                db.session.commit()
                print(f"✅ Updated chunk counts for {updated_count} documents")
            else:
                print("✅ All chunk counts were already correct")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating chunk counts: {e}")
            logging.error(f"Chunk count update error: {e}")
            return False

if __name__ == "__main__":
    update_chunk_counts()
