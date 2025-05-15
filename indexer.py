import os
from extract_text import extract_text_by_page
from embedding_utils import embed_chunks
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

CHROMA_DIR = "vector_store"
os.makedirs(CHROMA_DIR, exist_ok=True)

chroma_client = PersistentClient(path=CHROMA_DIR)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_or_create_collection("documents", embedding_function=embedding_fn)

def build_knowledge_base(pdf_path, doc_id):
    """
    Extracts text from a PDF, embeds it, and stores it with metadata.
    """
    pages = extract_text_by_page(pdf_path, poppler_path=r"C:\\poppler-23.11.0\\Library\\bin")
    embedded_chunks = embed_chunks(pages, doc_id)

    for chunk in embedded_chunks:
        uid = f"{doc_id}_p{chunk['page_num']}_c{chunk['chunk_index']}"
        collection.add(
            documents=[chunk['text']],
            embeddings=[chunk['embedding']],
            ids=[uid],
            metadatas=[{
                'doc_id': doc_id,
                'page_num': chunk['page_num'],
                'chunk_index': chunk['chunk_index']
            }]
        )
