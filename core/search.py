"""
Search module for querying the vector database.
"""
import os
import logging
import time
import sys

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SEARCH_TOP_K, SEARCH_THRESHOLD

# Import the get_chroma_collection function from indexer
from core.indexer import get_chroma_collection

def query_knowledge_base(query_text, top_k=SEARCH_TOP_K, threshold=SEARCH_THRESHOLD):
    """
    Searches the vector store for semantically similar chunks.

    Args:
        query_text (str): The query text to search for
        top_k (int): Number of results to return
        threshold (float): Minimum similarity score (0-100) to include in results

    Returns:
        Dict: Dictionary with query, results, and metadata
    """
    start_time = time.time()
    logging.info(f"Searching for: {query_text}")

    try:
        collection = get_chroma_collection()

        # Check if collection has any documents
        try:
            count = collection.count()
            if count == 0:
                logging.warning("No documents in collection")
                return {
                    'query': query_text,
                    'results': [],
                    'total_results': 0,
                    'message': "No documents have been indexed yet."
                }
        except Exception as e:
            logging.warning(f"Error checking collection count: {e}")

        try:
            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logging.error(f"Error during query: {e}")
            # This might happen if the collection was created without an embedding function
            return {
                'query': query_text,
                'results': [],
                'total_results': 0,
                'error': "Search functionality is not available. Please index documents first."
            }

        # Process results
        processed_results = []

        if results and 'documents' in results and results['documents']:
            documents = results['documents'][0]  # First query results
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                # Convert distance to similarity score (0-100%)
                similarity = max(0, min(100, (1 - dist) * 100))

                # Skip results below threshold
                if similarity < threshold:
                    continue

                # Get document info
                doc_id = meta.get('doc_id', 'unknown')
                page_num = meta.get('page_num', 0)

                processed_results.append({
                    'document': doc_id,
                    'page': page_num,
                    'text': doc,
                    'similarity': round(similarity, 2)
                })

        end_time = time.time()
        logging.info(f"Search completed in {round(end_time - start_time, 3)} seconds")
        logging.info(f"Found {len(processed_results)} results")

        return {
            'query': query_text,
            'results': processed_results,
            'total_results': len(processed_results),
            'search_time': round(end_time - start_time, 3)
        }

    except Exception as e:
        logging.error(f"Error searching knowledge base: {e}")
        return {
            'query': query_text,
            'results': [],
            'total_results': 0,
            'error': str(e)
        }

def get_document_stats():
    """
    Get statistics about indexed documents.

    Returns:
        Dict: Dictionary with document count and chunk count
    """
    try:
        collection = get_chroma_collection()

        # First check if we can get the count
        try:
            count = collection.count()
        except Exception as e:
            logging.warning(f"Error getting collection count: {e}")
            return {'doc_count': 0, 'chunk_count': 0}

        # If count is 0, no need to try to get data
        if count == 0:
            return {'doc_count': 0, 'chunk_count': 0}

        try:
            all_data = collection.get()

            if not all_data or 'metadatas' not in all_data or not all_data['metadatas']:
                return {'doc_count': 0, 'chunk_count': count}

            # Count unique documents
            doc_ids = set()
            for meta in all_data['metadatas']:
                if 'doc_id' in meta:
                    doc_ids.add(meta['doc_id'])

            return {
                'doc_count': len(doc_ids),
                'chunk_count': count
            }
        except Exception as e:
            logging.warning(f"Error getting collection data: {e}")
            # Return just the count if we can't get the data
            return {'doc_count': 0, 'chunk_count': count}

    except Exception as e:
        logging.error(f"Error getting document stats: {e}")
        return {
            'doc_count': 0,
            'chunk_count': 0
        }

def get_document_list():
    """
    Get list of all indexed documents with their chunk counts.

    Returns:
        List[Tuple]: List of (doc_id, chunk_count) tuples
    """
    try:
        collection = get_chroma_collection()

        # First check if we can get the count
        try:
            count = collection.count()
            if count == 0:
                return []
        except Exception as e:
            logging.warning(f"Error getting collection count: {e}")
            return []

        try:
            # Get all metadatas
            all_data = collection.get()

            if not all_data or 'metadatas' not in all_data or not all_data['metadatas']:
                return []

            # Count chunks per document
            doc_counts = {}
            for meta in all_data['metadatas']:
                if 'doc_id' in meta:
                    doc_id = meta['doc_id']
                    doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1

            # Convert to list of tuples for JSON serialization
            return list(doc_counts.items())
        except Exception as e:
            logging.warning(f"Error getting collection data: {e}")
            return []

    except Exception as e:
        logging.error(f"Error getting document list: {e}")
        return []
