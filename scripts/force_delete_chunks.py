#!/usr/bin/env python3
"""
Force delete specific chunks from ChromaDB using direct IDs
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.indexer import get_chroma_collection
from models import db, Document, init_db
from app import app

def force_delete_by_ids(doc_id):
    """Force delete chunks by collecting all IDs and deleting them directly"""
    print(f"🗑️ Force deleting all chunks for document: {doc_id}")
    print("=" * 60)
    
    try:
        collection = get_chroma_collection()
        
        # Get all data from ChromaDB
        all_data = collection.get()
        
        if not all_data or not all_data.get('ids'):
            print("📭 ChromaDB is empty")
            return
        
        # Find all chunk IDs that start with the document ID
        target_ids = []
        for chunk_id in all_data['ids']:
            if chunk_id.startswith(f"{doc_id}_"):
                target_ids.append(chunk_id)
        
        if not target_ids:
            print(f"❌ No chunks found for document {doc_id}")
            return
        
        print(f"📊 Found {len(target_ids)} chunks to delete")
        print(f"   Sample IDs: {target_ids[:5]}...")
        
        # Ask for confirmation
        response = input(f"❓ Force delete {len(target_ids)} chunks? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Deletion cancelled")
            return
        
        # Delete chunks in batches to avoid memory issues
        batch_size = 100
        deleted_count = 0
        
        for i in range(0, len(target_ids), batch_size):
            batch = target_ids[i:i + batch_size]
            try:
                collection.delete(ids=batch)
                deleted_count += len(batch)
                print(f"   ✅ Deleted batch {i//batch_size + 1}: {len(batch)} chunks")
            except Exception as e:
                print(f"   ❌ Failed to delete batch {i//batch_size + 1}: {e}")
        
        print(f"\n🎉 Force deletion complete!")
        print(f"   Attempted to delete: {deleted_count} chunks")
        
        # Verify deletion
        print(f"\n🔍 Verifying deletion...")
        verify_data = collection.get()
        remaining_target_ids = []
        
        if verify_data and verify_data.get('ids'):
            for chunk_id in verify_data['ids']:
                if chunk_id.startswith(f"{doc_id}_"):
                    remaining_target_ids.append(chunk_id)
        
        if remaining_target_ids:
            print(f"⚠️ Warning: {len(remaining_target_ids)} chunks still remain!")
            print(f"   Sample remaining: {remaining_target_ids[:5]}...")
        else:
            print(f"✅ Verified: All chunks for {doc_id} successfully removed")
            
    except Exception as e:
        print(f"❌ Error during force deletion: {e}")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python force_delete_chunks.py <doc_id>")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    force_delete_by_ids(doc_id)

if __name__ == "__main__":
    main()
