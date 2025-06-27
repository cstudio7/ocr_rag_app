"""
Text embedding module for generating vector representations of text.
"""
from sentence_transformers import SentenceTransformer
import logging
import sys
import os

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMBEDDING_MODEL

# Load the embedding model once
model = SentenceTransformer(EMBEDDING_MODEL)
logging.info(f"Loaded embedding model: {EMBEDDING_MODEL}")

def chunk_text(text, max_length=500):
    """
    Splits text into semantically coherent chunks while preserving headings, short lines,
    and limiting chunk size for embedding purposes.

    Args:
        text (str): The raw extracted text
        max_length (int): Maximum number of characters per chunk

    Returns:
        List[str]: List of cleaned and sized text chunks
    """
    lines = text.strip().split('\n')
    chunks = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Standalone heading or section marker
        is_heading = (
            len(line) < 60 and
            (line.isupper() or line.endswith(':') or line[:2].isdigit())
        )

        if is_heading:
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            chunks.append(line)
            continue

        # Try to fill the buffer up to max_length
        if len(buffer + " " + line) <= max_length:
            buffer += " " + line
        else:
            if buffer:
                chunks.append(buffer.strip())
            buffer = line  # start new buffer

    # Add any remaining content
    if buffer:
        chunks.append(buffer.strip())

    return chunks


def embed_chunks(page_texts, doc_id, batch_size=64):
    """
    Takes page-wise OCR output and returns embedded text chunks with metadata.
    Uses batching for more efficient embedding.

    Args:
        page_texts (List[Dict]): [{'page_num': int, 'text': str}, ...]
        doc_id (str): Unique document identifier.
        batch_size (int): Number of chunks to embed at once.

    Returns:
        List[Dict]: Embedded chunks with metadata.
    """
    results = []
    all_chunks = []
    chunk_metadata = []

    # First, collect all chunks and their metadata
    for page in page_texts:
        page_chunks = chunk_text(page['text'])
        if not page_chunks:
            continue
            
        for i, chunk in enumerate(page_chunks):
            all_chunks.append(chunk)
            chunk_metadata.append({
                'doc_id': doc_id,
                'page_num': page['page_num'],
                'chunk_index': i
            })
    
    # Process in batches for efficiency
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_metadata = chunk_metadata[i:i+batch_size]
        
        # Encode the batch
        batch_embeddings = model.encode(batch_chunks, show_progress_bar=False)
        
        # Combine with metadata
        for chunk, embedding, metadata in zip(batch_chunks, batch_embeddings, batch_metadata):
            results.append({
                'embedding': embedding.tolist(),  # Convert numpy array to list for ChromaDB
                'text': chunk,
                'doc_id': metadata['doc_id'],
                'page_num': metadata['page_num'],
                'chunk_index': metadata['chunk_index']
            })

    return results
