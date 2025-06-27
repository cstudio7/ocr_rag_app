#!/usr/bin/env python3
"""
Script to check the current state of ChromaDB
Useful for debugging duplicate chunk issues
"""

import sys
import os
from collections import defaultdict

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.indexer import get_chroma_collection
from config import VECTOR_STORE_DIR

def check_chromadb_state():
    """Check the current state of ChromaDB"""
    print("🔍 Checking ChromaDB State")
    print("=" * 50)
    
    try:
        # Get the collection
        collection = get_chroma_collection()
        
        # Get all data
        all_data = collection.get()
        
        if not all_data or not all_data.get('ids'):
            print("📭 ChromaDB is empty - no documents found")
            return
        
        total_chunks = len(all_data['ids'])
        print(f"📊 Total chunks in database: {total_chunks}")
        
        # Group by document ID
        doc_chunks = defaultdict(list)
        for i, chunk_id in enumerate(all_data['ids']):
            metadata = all_data['metadatas'][i] if all_data.get('metadatas') else {}
            doc_id = metadata.get('doc_id', 'unknown')
            doc_chunks[doc_id].append(chunk_id)
        
        print(f"📚 Documents found: {len(doc_chunks)}")
        print()
        
        # Show details for each document
        for doc_id, chunks in doc_chunks.items():
            print(f"📄 Document: {doc_id}")
            print(f"   Chunks: {len(chunks)}")
            
            # Show sample chunk IDs
            if len(chunks) <= 5:
                print(f"   IDs: {chunks}")
            else:
                print(f"   Sample IDs: {chunks[:3]} ... {chunks[-2:]}")
            
            # Check for duplicates within this document
            if len(chunks) != len(set(chunks)):
                duplicates = len(chunks) - len(set(chunks))
                print(f"   ⚠️  WARNING: {duplicates} duplicate chunks found!")
            
            print()
        
        # Check for any orphaned chunks (chunks without proper doc_id)
        orphaned = [chunk_id for chunk_id in all_data['ids'] 
                   if not any(chunk_id in chunks for chunks in doc_chunks.values())]
        
        if orphaned:
            print(f"🚨 Found {len(orphaned)} orphaned chunks:")
            for chunk_id in orphaned[:10]:  # Show first 10
                print(f"   {chunk_id}")
            if len(orphaned) > 10:
                print(f"   ... and {len(orphaned) - 10} more")
        
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        print(f"Vector store directory: {VECTOR_STORE_DIR}")
        print(f"Directory exists: {os.path.exists(VECTOR_STORE_DIR)}")

def find_document_chunks(doc_id):
    """Find all chunks for a specific document"""
    print(f"🔍 Searching for chunks with doc_id: {doc_id}")
    print("=" * 50)
    
    try:
        collection = get_chroma_collection()
        
        # Search by metadata
        chunks = collection.get(where={"doc_id": doc_id})
        
        if chunks and chunks.get('ids'):
            print(f"✅ Found {len(chunks['ids'])} chunks for {doc_id}")
            for i, chunk_id in enumerate(chunks['ids'][:10]):  # Show first 10
                metadata = chunks['metadatas'][i] if chunks.get('metadatas') else {}
                print(f"   {chunk_id} - Page: {metadata.get('page_num', '?')}")
            
            if len(chunks['ids']) > 10:
                print(f"   ... and {len(chunks['ids']) - 10} more chunks")
        else:
            print(f"❌ No chunks found for {doc_id}")
            
            # Try to find similar doc_ids
            all_data = collection.get()
            if all_data and all_data.get('metadatas'):
                similar_docs = set()
                for metadata in all_data['metadatas']:
                    if metadata and 'doc_id' in metadata:
                        existing_doc_id = metadata['doc_id']
                        if doc_id.lower() in existing_doc_id.lower() or existing_doc_id.lower() in doc_id.lower():
                            similar_docs.add(existing_doc_id)
                
                if similar_docs:
                    print(f"🔍 Found similar document IDs:")
                    for similar_id in similar_docs:
                        print(f"   {similar_id}")
    
    except Exception as e:
        print(f"❌ Error searching for document: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Search for specific document
        doc_id = sys.argv[1]
        find_document_chunks(doc_id)
    else:
        # Show overall state
        check_chromadb_state()
        
        print("\n💡 Usage:")
        print("   python check_chromadb.py                    # Show all documents")
        print("   python check_chromadb.py <doc_id>          # Search for specific document")

if __name__ == "__main__":
    main()
