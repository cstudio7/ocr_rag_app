"""
Script to check all documents in the ChromaDB collection.
This will print detailed information about all indexed documents.
"""
import os
import sys
import glob
from collections import Counter
import chromadb
from chromadb.utils import embedding_functions

# Configuration - try multiple possible paths
POSSIBLE_PATHS = [
    "vector_store",
    "./vector_store",
    "../vector_store",
    "d:/Project/vector_store"
]

def main():
    print("\n📊 ChromaDB Document Analysis")
    print("=" * 50)

    # Search for vector store in possible locations
    found_path = None
    for path in POSSIBLE_PATHS:
        if os.path.exists(path):
            print(f"✅ Found vector store at: {os.path.abspath(path)}")
            found_path = path
            break

    if not found_path:
        print("❌ Vector store directory not found in any of these locations:")
        for path in POSSIBLE_PATHS:
            print(f"  - {os.path.abspath(path)}")

        # Search for any directory with 'vector' in the name
        print("\nSearching for any vector store directories...")
        for root, dirs, _ in os.walk('.', topdown=True):
            for dir_name in dirs:
                if 'vector' in dir_name.lower() or 'chroma' in dir_name.lower():
                    full_path = os.path.join(root, dir_name)
                    print(f"  - Found potential vector store: {os.path.abspath(full_path)}")
        return

    try:
        # Initialize ChromaDB client
        client = chromadb.Client(chromadb.config.Settings(persist_directory=found_path))

        # List all collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collection(s):")
        for i, collection in enumerate(collections):
            print(f"  {i+1}. {collection.name} (id: {collection.id})")

        if not collections:
            print("❌ No collections found in the vector store!")
            return

        # Try to get the collection with different possible names
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        possible_collection_names = ["documents", "document", "pdf", "pdfs", "vector_store"]
        collection = None

        # First try to get existing collections
        for coll in collections:
            collection = client.get_collection(coll.name, embedding_function=embed_fn)
            print(f"\n🔍 Examining collection: {coll.name}")
            break

        # If no collections found, try to create with common names
        if not collection and not collections:
            for name in possible_collection_names:
                try:
                    print(f"Trying to access collection '{name}'...")
                    collection = client.get_or_create_collection(name, embedding_function=embed_fn)
                    break
                except Exception as e:
                    print(f"  Error with collection '{name}': {str(e)}")

        if not collection:
            print("❌ Could not access any collection!")
            return

        # Get all documents
        all_docs = collection.get()

        if not all_docs or not all_docs.get('ids'):
            print("❌ No documents found in the collection!")
            return

        # Count documents by doc_id
        doc_ids = [meta.get('doc_id') for meta in all_docs.get('metadatas', [])]
        doc_counter = Counter(doc_ids)

        print(f"\n📄 Found {len(doc_counter)} unique document(s):")
        for i, (doc_id, count) in enumerate(doc_counter.most_common()):
            print(f"  {i+1}. {doc_id}: {count} chunks")

        # Print total chunks
        print(f"\n📊 Total chunks: {len(all_docs.get('ids', []))}")

        # Check for documents with unusual metadata
        print("\n🔍 Checking for unusual document entries...")
        unusual_docs = []
        for i, meta in enumerate(all_docs.get('metadatas', [])):
            if not meta.get('doc_id'):
                unusual_docs.append((i, meta))

        if unusual_docs:
            print(f"⚠️ Found {len(unusual_docs)} entries with unusual metadata:")
            for i, meta in unusual_docs[:5]:  # Show first 5 only
                print(f"  Entry {i}: {meta}")
            if len(unusual_docs) > 5:
                print(f"  ... and {len(unusual_docs) - 5} more")
        else:
            print("✅ All document entries have expected metadata structure")

        # Print document IDs for verification
        print("\n📋 All unique document IDs for verification:")
        for doc_id in sorted(doc_counter.keys()):
            print(f"  • {doc_id}")

    except Exception as e:
        print(f"❌ Error analyzing ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
