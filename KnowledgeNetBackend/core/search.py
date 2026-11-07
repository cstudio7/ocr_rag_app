"""
Search module for querying the vector database.
"""
import os
import logging
import time
import sys
import re
from spellchecker import SpellChecker

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SEARCH_TOP_K, SEARCH_THRESHOLD

# Import the get_chroma_collection function from indexer
from core.indexer import get_chroma_collection

# Initialize spell checker
spell = SpellChecker()

def correct_spelling(text):
    """
    Corrects spelling mistakes in the input text.

    Args:
        text (str): Input text that may contain spelling mistakes

    Returns:
        dict: Dictionary containing:
            - corrected_text: Text with spelling corrections
            - corrections: List of corrections made
            - has_corrections: Boolean indicating if any corrections were made
    """
    # Split text into words, preserving punctuation and spacing
    words = re.findall(r'\b\w+\b|\W+', text)
    corrected_words = []
    corrections = []
    has_corrections = False

    for word in words:
        # Only process actual words (not punctuation/spaces)
        if re.match(r'\b\w+\b', word):
            word_lower = word.lower()

            # Check if word is misspelled
            if word_lower not in spell:
                # Get the most likely correction
                candidates = spell.candidates(word_lower)
                if candidates:
                    # Get the most likely correction (first in the set)
                    corrected = list(candidates)[0]

                    # Preserve original case
                    if word.isupper():
                        corrected = corrected.upper()
                    elif word.istitle():
                        corrected = corrected.capitalize()

                    corrected_words.append(corrected)
                    corrections.append({
                        'original': word,
                        'corrected': corrected,
                        'position': len(''.join(corrected_words[:-1]))
                    })
                    has_corrections = True
                else:
                    # No correction found, keep original
                    corrected_words.append(word)
            else:
                # Word is correctly spelled
                corrected_words.append(word)
        else:
            # Punctuation or whitespace, keep as is
            corrected_words.append(word)

    corrected_text = ''.join(corrected_words)

    return {
        'corrected_text': corrected_text,
        'corrections': corrections,
        'has_corrections': has_corrections
    }

# def query_knowledge_base(query_text, top_k=SEARCH_TOP_K, threshold=SEARCH_THRESHOLD, page=1, per_page=10):
#     """
#     Searches the vector store for semantically similar chunks.

#     Args:
#         query_text (str): The query text to search for
#         top_k (int): Number of results to return
#         threshold (float): Minimum similarity score (0-100) to include in results

#     Returns:
#         Dict: Dictionary with query, results, and metadata
#     """
#     start_time = time.time()
#     original_query = query_text
#     logging.info(f"Searching for: {query_text}")

#     # Apply spell correction
#     spell_result = correct_spelling(query_text)
#     corrected_query = spell_result['corrected_text']
#     corrections_made = spell_result['corrections']
#     has_corrections = spell_result['has_corrections']

#     if has_corrections:
#         logging.info(f"Spell corrections applied: {corrections_made}")
#         query_text = corrected_query

#     try:
#         collection = get_chroma_collection()

#         # Check if collection has any documents
#         try:
#             count = collection.count()
#             if count == 0:
#                 logging.warning("No documents in collection")
#                 return {
#                     'query': original_query,
#                     'corrected_query': corrected_query if has_corrections else None,
#                     'corrections': corrections_made if has_corrections else [],
#                     'has_corrections': has_corrections,
#                     'results': [],
#                     'total_results': 0,
#                     'message': "No documents have been indexed yet."
#                 }
#         except Exception as e:
#             logging.warning(f"Error checking collection count: {e}")

#         try:
#             # Query the collection
#             results = collection.query(
#                 query_texts=[query_text],
#                 n_results=top_k,
#                 include=["documents", "metadatas", "distances"]
#             )
#         except Exception as e:
#             logging.error(f"Error during query: {e}")
#             # This might happen if the collection was created without an embedding function
#             return {
#                 'query': original_query,
#                 'corrected_query': corrected_query if has_corrections else None,
#                 'corrections': corrections_made if has_corrections else [],
#                 'has_corrections': has_corrections,
#                 'results': [],
#                 'total_results': 0,
#                 'error': "Search functionality is not available. Please index documents first."
#             }

#         # Process results
#         processed_results = []

#         if results and 'documents' in results and results['documents']:
#             documents = results['documents'][0]  # First query results
#             metadatas = results['metadatas'][0]
#             distances = results['distances'][0]

#             for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
#                 # Convert distance to similarity score (0-100%)
#                 similarity = max(0, min(100, (1 - dist) * 100))

#                 # Skip results below threshold
#                 if similarity < threshold:
#                     continue

#                 # Get document info
#                 doc_id = meta.get('doc_id', 'unknown')
#                 page_num = meta.get('page_num', 0)

#                 processed_results.append({
#                     'document': doc_id,
#                     'page': page_num,
#                     'text': doc,
#                     'similarity': round(similarity, 2)
#                 })

#         end_time = time.time()
#         logging.info(f"Search completed in {round(end_time - start_time, 3)} seconds")
#         logging.info(f"Found {len(processed_results)} results")
                
#         if not processed_results or max([r['similarity'] for r in processed_results], default=0) < 60:
#             logging.info("⚠️ Using fallback exact match for query")
#             all_data = collection.get()
#             fallback_matches = []
#             for doc, meta in zip(all_data['documents'], all_data['metadatas']):
#                 if query_text.lower() in doc.lower():
#                     fallback_matches.append({
#                         'document': meta.get('doc_id', 'unknown'),
#                         'page': meta.get('page_num', 0),
#                         'text': doc,
#                         'similarity': 100.0
#                     })

#             if fallback_matches:
#                 return {
#                     'query': original_query,
#                     'corrected_query': corrected_query if has_corrections else None,
#                     'corrections': corrections_made if has_corrections else [],
#                     'has_corrections': has_corrections,
#                     'results': fallback_matches,
#                     'total_results': len(fallback_matches),
#                     'search_time': round(time.time() - start_time, 3),
#                     'message': "Fallback exact match used"
#                 }

#         return {
#             'query': original_query,
#             'corrected_query': corrected_query if has_corrections else None,
#             'corrections': corrections_made if has_corrections else [],
#             'has_corrections': has_corrections,
#             'results': processed_results,
#             'total_results': len(processed_results),
#             'search_time': round(end_time - start_time, 3)
#         }

#     except Exception as e:
#         logging.error(f"Error searching knowledge base: {e}")
#         return {
#             'query': original_query,
#             'corrected_query': corrected_query if has_corrections else None,
#             'corrections': corrections_made if has_corrections else [],
#             'has_corrections': has_corrections,
#             'results': [],
#             'total_results': 0,
#             'error': str(e)
#         }
def query_knowledge_base(query_text, top_k=SEARCH_TOP_K, threshold=SEARCH_THRESHOLD, page=1, per_page=10):
    """
    Searches the vector store for semantically similar chunks with optional pagination.

    Args:
        query_text (str): The query text to search for
        top_k (int): Number of top results to fetch before filtering
        threshold (float): Minimum similarity score (0-100) to include in results
        page (int): Page number (1-based)
        per_page (int): Number of results per page

    Returns:
        Dict: Dictionary with query, results, and metadata
    """
    start_time = time.time()
    original_query = query_text
    logging.info(f"Searching for: {query_text}")

    # Apply spell correction
    spell_result = correct_spelling(query_text)
    corrected_query = spell_result['corrected_text']
    corrections_made = spell_result['corrections']
    has_corrections = spell_result['has_corrections']

    if has_corrections:
        logging.info(f"Spell corrections applied: {corrections_made}")
        query_text = corrected_query

    try:
        collection = get_chroma_collection()

        try:
            if collection.count() == 0:
                return {
                    'query': original_query,
                    'corrected_query': corrected_query if has_corrections else None,
                    'corrections': corrections_made if has_corrections else [],
                    'has_corrections': has_corrections,
                    'results': [],
                    'total_results': 0,
                    'message': "No documents have been indexed yet."
                }
        except Exception as e:
            logging.warning(f"Error checking collection count: {e}")

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logging.error(f"Error during query: {e}")
            return {
                'query': original_query,
                'corrected_query': corrected_query if has_corrections else None,
                'corrections': corrections_made if has_corrections else [],
                'has_corrections': has_corrections,
                'results': [],
                'total_results': 0,
                'error': "Search functionality is not available. Please index documents first."
            }

        processed_results = []

        if results and 'documents' in results and results['documents']:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            for doc, meta, dist in zip(documents, metadatas, distances):
                similarity = max(0, min(100, (1 - dist) * 100))
                if similarity >= threshold:
                    processed_results.append({
                        'document': meta.get('doc_id', 'unknown'),
                        'page': meta.get('page_num', 0),
                        'text': doc,
                        'similarity': round(similarity, 2)
                    })

        total_results = len(processed_results)
        start = (page - 1) * per_page
        end = start + per_page
        paged_results = processed_results[start:end]

        logging.info(f"Search completed in {round(time.time() - start_time, 3)} seconds")
        logging.info(f"Found {total_results} results")

        # Fallback to exact match if no strong results
        if not processed_results or max([r['similarity'] for r in processed_results], default=0) < 60:
            logging.info("⚠️ Using fallback exact match for query")
            all_data = collection.get()
            fallback_matches = []

            for doc, meta in zip(all_data['documents'], all_data['metadatas']):
                if query_text.lower() in doc.lower():
                    fallback_matches.append({
                        'document': meta.get('doc_id', 'unknown'),
                        'page': meta.get('page_num', 0),
                        'text': doc,
                        'similarity': 100.0
                    })

            total_fallback = len(fallback_matches)
            start = (page - 1) * per_page
            end = start + per_page
            paged_fallback = fallback_matches[start:end]

            return {
                'query': original_query,
                'corrected_query': corrected_query if has_corrections else None,
                'corrections': corrections_made if has_corrections else [],
                'has_corrections': has_corrections,
                'results': paged_fallback,
                'total_results': total_fallback,
                'page': page,
                'per_page': per_page,
                'search_time': round(time.time() - start_time, 3),
                'message': "Fallback exact match used"
            }

        return {
            'query': original_query,
            'corrected_query': corrected_query if has_corrections else None,
            'corrections': corrections_made if has_corrections else [],
            'has_corrections': has_corrections,
            'results': paged_results,
            'total_results': total_results,
            'page': page,
            'per_page': per_page,
            'search_time': round(time.time() - start_time, 3)
        }

    except Exception as e:
        logging.error(f"Error searching knowledge base: {e}")
        return {
            'query': original_query,
            'corrected_query': corrected_query if has_corrections else None,
            'corrections': corrections_made if has_corrections else [],
            'has_corrections': has_corrections,
            'results': [],
            'total_results': 0,
            'page': page,
            'per_page': per_page,
            'error': str(e)
        }

    


def query_knowledge_base_no_correction(query_text, top_k=SEARCH_TOP_K, threshold=SEARCH_THRESHOLD, page=1, per_page=10):
    """
    Searches the vector store for semantically similar chunks without spell correction.
    Includes pagination and fallback to exact match.

    Args:
        query_text (str): The query text to search for
        top_k (int): Number of top results to fetch
        threshold (float): Minimum similarity score (0-100)
        page (int): Page number (1-based)
        per_page (int): Number of results per page

    Returns:
        Dict: Dictionary with query, results, and metadata
    """
    import time
    start_time = time.time()
    logging.info(f"Searching (no correction): {query_text}")

    try:
        collection = get_chroma_collection()

        try:
            if collection.count() == 0:
                return {
                    'query': query_text,
                    'corrected_query': None,
                    'corrections': [],
                    'has_corrections': False,
                    'results': [],
                    'total_results': 0,
                    'page': page,
                    'per_page': per_page,
                    'message': "No documents have been indexed yet."
                }
        except Exception as e:
            logging.warning(f"Error checking collection count: {e}")

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logging.error(f"Error during query: {e}")
            return {
                'query': query_text,
                'corrected_query': None,
                'corrections': [],
                'has_corrections': False,
                'results': [],
                'total_results': 0,
                'page': page,
                'per_page': per_page,
                'error': "Search failed. Please reindex documents."
            }

        processed_results = []

        if results and 'documents' in results and results['documents']:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            for doc, meta, dist in zip(documents, metadatas, distances):
                similarity = max(0, min(100, (1 - dist) * 100))
                if similarity >= threshold:
                    processed_results.append({
                        'document': meta.get('doc_id', 'unknown'),
                        'page': meta.get('page_num', 0),
                        'text': doc,
                        'similarity': round(similarity, 2)
                    })

        total_results = len(processed_results)
        start = (page - 1) * per_page
        end = start + per_page
        paged_results = processed_results[start:end]

        # Fallback to exact match if needed
        if not processed_results or max([r['similarity'] for r in processed_results], default=0) < threshold:
            logging.info("⚠️ Using fallback exact match (no correction)")
            all_data = collection.get()
            fallback_matches = []

            for doc, meta in zip(all_data['documents'], all_data['metadatas']):
                if query_text.lower() in doc.lower():
                    fallback_matches.append({
                        'document': meta.get('doc_id', 'unknown'),
                        'page': meta.get('page_num', 0),
                        'text': doc,
                        'similarity': 100.0
                    })

            total_fallback = len(fallback_matches)
            start = (page - 1) * per_page
            end = start + per_page
            paged_fallback = fallback_matches[start:end]

            return {
                'query': query_text,
                'corrected_query': None,
                'corrections': [],
                'has_corrections': False,
                'results': paged_fallback,
                'total_results': total_fallback,
                'page': page,
                'per_page': per_page,
                'search_time': round(time.time() - start_time, 3),
                'message': "Fallback exact match used"
            }

        return {
            'query': query_text,
            'corrected_query': None,
            'corrections': [],
            'has_corrections': False,
            'results': paged_results,
            'total_results': total_results,
            'page': page,
            'per_page': per_page,
            'search_time': round(time.time() - start_time, 3)
        }

    except Exception as e:
        logging.error(f"Error in query_knowledge_base_no_correction: {e}")
        return {
            'query': query_text,
            'corrected_query': None,
            'corrections': [],
            'has_corrections': False,
            'results': [],
            'total_results': 0,
            'page': page,
            'per_page': per_page,
            'error': str(e)
        }

def get_search_suggestions(query, limit=5):
    """
    Get search suggestions based on the partial query.

    Args:
        query (str): Partial query text
        limit (int): Maximum number of suggestions to return

    Returns:
        List[str]: List of suggested search queries
    """
    try:
        collection = get_chroma_collection()

        # Check if collection has any documents
        try:
            count = collection.count()
            if count == 0:
                return []
        except Exception as e:
            logging.warning(f"Error checking collection count: {e}")
            return []

        # Get all documents to extract common phrases and terms
        try:
            # Query with the partial text to get relevant chunks
            results = collection.query(
                query_texts=[query],
                n_results=min(20, count),  # Get more results for better suggestions
                include=["documents", "metadatas"]
            )

            if not results or 'documents' not in results or not results['documents']:
                return []

            documents = results['documents'][0]
            suggestions = set()

            # Extract potential search queries from the documents
            for doc in documents:
                # Split document into sentences
                sentences = re.split(r'[.!?]+', doc)

                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 10 or len(sentence) > 100:
                        continue

                    # Check if the sentence contains the query (case insensitive)
                    if query.lower() in sentence.lower():
                        # Extract phrases that start with common question words
                        question_patterns = [
                            r'\b(what is|what are|how does|how do|why is|why are|when is|when are|where is|where are)\s+[^.!?]*',
                            r'\b(explain|describe|define|tell me about)\s+[^.!?]*',
                            r'\b(benefits of|advantages of|disadvantages of|types of|examples of)\s+[^.!?]*'
                        ]

                        for pattern in question_patterns:
                            matches = re.findall(pattern, sentence, re.IGNORECASE)
                            for match in matches:
                                if len(match) > len(query) and len(match) < 80:
                                    suggestions.add(match.strip())

                        # Also add the sentence itself if it's a good length
                        if 20 <= len(sentence) <= 80 and sentence.count(' ') >= 3:
                            suggestions.add(sentence.strip())

            # Convert to list and sort by relevance (length and similarity to query)
            suggestion_list = list(suggestions)

            # Score suggestions based on how well they match the query
            scored_suggestions = []
            for suggestion in suggestion_list:
                # Calculate a simple relevance score
                score = 0
                suggestion_lower = suggestion.lower()
                query_lower = query.lower()

                # Boost score if suggestion starts with query
                if suggestion_lower.startswith(query_lower):
                    score += 10

                # Boost score based on how many query words are in the suggestion
                query_words = query_lower.split()
                for word in query_words:
                    if word in suggestion_lower:
                        score += 2

                # Prefer shorter, more concise suggestions
                if len(suggestion) < 50:
                    score += 1

                scored_suggestions.append((score, suggestion))

            # Sort by score (descending) and return top suggestions
            scored_suggestions.sort(key=lambda x: x[0], reverse=True)

            # Return unique suggestions up to the limit
            final_suggestions = []
            seen = set()

            for score, suggestion in scored_suggestions:
                if suggestion.lower() not in seen and len(final_suggestions) < limit:
                    final_suggestions.append(suggestion)
                    seen.add(suggestion.lower())

            return final_suggestions

        except Exception as e:
            logging.error(f"Error generating suggestions: {e}")
            return []

    except Exception as e:
        logging.error(f"Error in get_search_suggestions: {e}")
        return []

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
