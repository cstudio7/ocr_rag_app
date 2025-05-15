from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import os

CHROMA_DIR = "vector_store"
chroma_client = PersistentClient(path=CHROMA_DIR)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
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
