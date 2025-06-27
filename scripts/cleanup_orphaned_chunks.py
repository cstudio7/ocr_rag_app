#!/usr/bin/env python3
"""
Cleanup script to remove orphaned chunks from ChromaDB
These are chunks that exist in the vector database but not in the SQL database
"""

import sys
import os
from collections import defaultdict

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.indexer import get_chroma_collection
from models import db, Document, init_db
from app import app

def cleanup_orphaned_chunks():
    """Remove chunks from ChromaDB that don't have corresponding documents in SQL database"""
    print("🧹 Cleaning up orphaned chunks from ChromaDB")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Get the ChromaDB collection
            collection = get_chroma_collection()
            
            # Get all chunks from ChromaDB
            all_data = collection.get()
            if not all_data or not all_data.get('ids'):
                print("📭 ChromaDB is empty - nothing to clean")
                return
            
            total_chunks = len(all_data['ids'])
            print(f"📊 Total chunks in ChromaDB: {total_chunks}")
            
            # Group chunks by document ID
            chroma_docs = defaultdict(list)
            for i, chunk_id in enumerate(all_data['ids']):
                metadata = all_data['metadatas'][i] if all_data.get('metadatas') else {}
                doc_id = metadata.get('doc_id', 'unknown')
                chroma_docs[doc_id].append(chunk_id)
            
            print(f"📚 Documents in ChromaDB: {len(chroma_docs)}")
            
            # Get all document IDs from SQL database
            sql_docs = set()
            documents = Document.query.all()
            for doc in documents:
                sql_docs.add(doc.doc_id)
            
            print(f"🗄️ Documents in SQL database: {len(sql_docs)}")
            
            # Find orphaned documents (in ChromaDB but not in SQL)
            orphaned_docs = []
            for doc_id in chroma_docs.keys():
                if doc_id not in sql_docs and doc_id != 'unknown':
                    orphaned_docs.append(doc_id)
            
            if not orphaned_docs:
                print("✅ No orphaned chunks found - database is clean!")
                return
            
            print(f"\n🚨 Found {len(orphaned_docs)} orphaned documents:")
            
            total_orphaned_chunks = 0
            for doc_id in orphaned_docs:
                chunk_count = len(chroma_docs[doc_id])
                total_orphaned_chunks += chunk_count
                print(f"   📄 {doc_id}: {chunk_count} chunks")
            
            print(f"\n📊 Total orphaned chunks: {total_orphaned_chunks}")
            
            # Ask for confirmation
            response = input(f"\n❓ Delete {total_orphaned_chunks} orphaned chunks from {len(orphaned_docs)} documents? (y/N): ")
            
            if response.lower() != 'y':
                print("❌ Cleanup cancelled")
                return
            
            # Delete orphaned chunks
            print(f"\n🗑️ Deleting orphaned chunks...")
            
            deleted_count = 0
            for doc_id in orphaned_docs:
                chunk_ids = chroma_docs[doc_id]
                try:
                    # Delete by document ID (more efficient)
                    collection.delete(where={"doc_id": doc_id})
                    deleted_count += len(chunk_ids)
                    print(f"   ✅ Deleted {len(chunk_ids)} chunks for {doc_id}")
                except Exception as e:
                    print(f"   ❌ Failed to delete chunks for {doc_id}: {e}")
            
            print(f"\n🎉 Cleanup complete!")
            print(f"   Deleted: {deleted_count} chunks")
            print(f"   From: {len(orphaned_docs)} orphaned documents")
            
            # Verify cleanup
            print(f"\n🔍 Verifying cleanup...")
            remaining_data = collection.get()
            remaining_chunks = len(remaining_data['ids']) if remaining_data and remaining_data.get('ids') else 0
            print(f"   Remaining chunks: {remaining_chunks}")
            print(f"   Removed: {total_chunks - remaining_chunks}")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def cleanup_specific_document(doc_id):
    """Remove chunks for a specific document from ChromaDB"""
    print(f"🧹 Cleaning up chunks for document: {doc_id}")
    print("=" * 60)
    
    try:
        collection = get_chroma_collection()
        
        # Check if document exists in ChromaDB
        chunks = collection.get(where={"doc_id": doc_id})
        
        if not chunks or not chunks.get('ids'):
            print(f"❌ No chunks found for document {doc_id}")
            return
        
        chunk_count = len(chunks['ids'])
        print(f"📊 Found {chunk_count} chunks for {doc_id}")
        
        # Ask for confirmation
        response = input(f"❓ Delete {chunk_count} chunks for {doc_id}? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Cleanup cancelled")
            return
        
        # Delete chunks
        collection.delete(where={"doc_id": doc_id})
        print(f"✅ Deleted {chunk_count} chunks for {doc_id}")
        
        # Verify deletion
        verify_chunks = collection.get(where={"doc_id": doc_id})
        if verify_chunks and verify_chunks.get('ids'):
            print(f"⚠️ Warning: {len(verify_chunks['ids'])} chunks still remain!")
        else:
            print(f"✅ Verified: All chunks for {doc_id} successfully removed")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Clean up specific document
        doc_id = sys.argv[1]
        cleanup_specific_document(doc_id)
    else:
        # Clean up all orphaned chunks
        cleanup_orphaned_chunks()
        
        print("\n💡 Usage:")
        print("   python cleanup_orphaned_chunks.py                    # Clean all orphaned chunks")
        print("   python cleanup_orphaned_chunks.py <doc_id>          # Clean specific document")

if __name__ == "__main__":
    main()
