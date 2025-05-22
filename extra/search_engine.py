import chromadb
from chromadb import PersistentClient, Client
from chromadb.utils import embedding_functions
import os
import logging

# Configuration
CHROMA_DIR = "vector_store"
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize client with explicit persistence
try:
    # First try persistent client
    logging.info(f"Initializing ChromaDB PersistentClient at {os.path.abspath(CHROMA_DIR)}")
    chroma_client = PersistentClient(path=CHROMA_DIR)

    # Set up embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    # Get or create collection
    collection = chroma_client.get_or_create_collection("documents", embedding_function=embedding_fn)

    # Log collection info
    logging.info(f"ChromaDB collection 'documents' initialized with {collection.count()} chunks")

except Exception as e:
    logging.error(f"Error initializing persistent ChromaDB: {e}")

    # Fallback to in-memory client with persistence settings
    logging.info("Falling back to regular Client with persistence settings")
    chroma_client = Client(chromadb.config.Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    ))

    # Set up embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    # Get or create collection
    collection = chroma_client.get_or_create_collection("documents", embedding_function=embedding_fn)

def query_knowledge_base(query_text, top_k=10):
    """
    Searches the vector store for semantically similar chunks.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )

    response = []
    for text, metadata, score in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        response.append({
            'text': text,
            'doc_id': metadata['doc_id'],
            'page': metadata['page_num'],
            'score': round(score, 4)
        })

    return response
