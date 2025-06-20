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

def query_knowledge_base(query_text, top_k=SEARCH_TOP_K, threshold=SEARCH_THRESHOLD, include_keywords=True):
    """
    Searches the vector store for semantically similar chunks.

    Args:
        query_text (str): The query text to search for
        top_k (int): Number of results to return
        threshold (float): Minimum similarity score (0-100) to include in results
        include_keywords (bool): Whether to include keyword search results

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

        # Check if collection has any documents
        try:
            count = collection.count()
            if count == 0:
                logging.warning("No documents in collection")
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

        # ALWAYS do semantic search, but only do keyword search if include_keywords is True
        semantic_results = []
        keyword_results = []
        
        # 1. Semantic search
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]

                for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                    similarity = max(0, min(100, (1 - dist) * 100))
                    if similarity >= threshold:
                        semantic_results.append({
                            'document': meta.get('doc_id', 'unknown'),
                            'page': meta.get('page_num', 0),
                            'text': doc,
                            'similarity': round(similarity, 2),
                            'source': 'semantic'
                        })
        except Exception as e:
            logging.error(f"Error during semantic search: {e}")
        
        # 2. Keyword search (only if include_keywords is True)
        if include_keywords:
            logging.info("Running keyword search as well")
            try:
                # Get all documents (with pagination if needed)
                all_docs = []
                all_metadatas = []
                
                # Get documents in batches to handle large collections
                batch_size = 1000
                offset = 0
                
                while True:
                    batch = collection.get(limit=batch_size, offset=offset)
                    if not batch or not batch['documents'] or len(batch['documents']) == 0:
                        break
                        
                    all_docs.extend(batch['documents'])
                    all_metadatas.extend(batch['metadatas'])
                    offset += len(batch['documents'])
                    
                    # Safety check to prevent infinite loops
                    if offset > 10000:  # Arbitrary limit
                        break
                
                # Manual search through documents
                for doc, meta in zip(all_docs, all_metadatas):
                    doc_lower = doc.lower()
                    term_lower = query_text.lower()
                    
                    # Check if the document contains the search term
                    if term_lower in doc_lower:
                        # Calculate a simple relevance score based on term frequency
                        term_count = doc_lower.count(term_lower)
                        doc_length = len(doc_lower)
                        frequency = term_count / max(1, doc_length)
                        similarity = min(100, max(50, frequency * 10000))  # Scale to reasonable range
                        
                        keyword_results.append({
                            'document': meta.get('doc_id', 'unknown'),
                            'page': meta.get('page_num', 0),
                            'text': doc,
                            'similarity': round(similarity, 2),
                            'source': 'keyword'
                        })
            except Exception as e:
                logging.error(f"Error during keyword search: {e}")
        
        # Combine and deduplicate results
        all_results = semantic_results + keyword_results
        
        # Sort by similarity score (descending)
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Deduplicate based on text content
        seen_texts = set()
        final_results = []
        
        for result in all_results:
            # Use a hash of the text as a unique identifier
            text_hash = hash(result['text'])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                final_results.append(result)
                
                # Limit to top_k results
                if len(final_results) >= top_k:
                    break
        
        end_time = time.time()
        logging.info(f"Search completed in {round(end_time - start_time, 3)} seconds")
        logging.info(f"Found {len(final_results)} results (semantic: {len(semantic_results)}, keyword: {len(keyword_results)})")

        return {
            'query': original_query,
            'corrected_query': corrected_query if has_corrections else None,
            'corrections': corrections_made if has_corrections else [],
            'has_corrections': has_corrections,
            'results': final_results,
            'total_results': len(final_results),
            'search_time': round(end_time - start_time, 3)
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
            'error': str(e)
        }
    


def query_knowledge_base_no_correction(query_text, top_k=SEARCH_TOP_K, threshold=SEARCH_THRESHOLD):
    """
    Searches the vector store for semantically similar chunks without spell correction.
    Falls back to exact match if semantic results are insufficient.

    Args:
        query_text (str): The query text to search for
        top_k (int): Number of results to return
        threshold (float): Minimum similarity score (0-100) to include in results

    Returns:
        Dict: Dictionary with query, results, and metadata
    """
    import time
    start_time = time.time()
    logging.info(f"Searching for (no correction): {query_text}")

    try:
        collection = get_chroma_collection()

        # Check if collection has any documents
        try:
            count = collection.count()
            if count == 0:
                logging.warning("No documents in collection")
                return {
                    'query': query_text,
                    'corrected_query': None,
                    'corrections': [],
                    'has_corrections': False,
                    'results': [],
                    'total_results': 0,
                    'message': "No documents have been indexed yet."
                }
        except Exception as e:
            logging.warning(f"Error checking collection count: {e}")

        # ALWAYS do both semantic search and keyword search
        semantic_results = []
        keyword_results = []
        
        # 1. Semantic search
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]

                for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                    similarity = max(0, min(100, (1 - dist) * 100))
                    if similarity >= threshold:
                        semantic_results.append({
                            'document': meta.get('doc_id', 'unknown'),
                            'page': meta.get('page_num', 0),
                            'text': doc,
                            'similarity': round(similarity, 2),
                            'source': 'semantic'
                        })
        except Exception as e:
            logging.error(f"Error during semantic search: {e}")
        
        # 2. Keyword search (always run this)
        logging.info("Running keyword search as well (no correction)")
        try:
            # Get all documents (with pagination if needed)
            all_docs = []
            all_metadatas = []
            
            # Get documents in batches to handle large collections
            batch_size = 1000
            offset = 0
            
            while True:
                batch = collection.get(limit=batch_size, offset=offset)
                if not batch or not batch['documents'] or len(batch['documents']) == 0:
                    break
                    
                all_docs.extend(batch['documents'])
                all_metadatas.extend(batch['metadatas'])
                offset += len(batch['documents'])
                
                # Safety check to prevent infinite loops
                if offset > 10000:  # Arbitrary limit
                    break
            
            # Manual search through documents
            for doc, meta in zip(all_docs, all_metadatas):
                doc_lower = doc.lower()
                term_lower = query_text.lower()
                
                # Check for exact match or word boundary match
                if term_lower in doc_lower:
                    # Check if it's a word boundary match
                    is_word = False
                    
                    # Simple word boundary check
                    term_pos = doc_lower.find(term_lower)
                    before_char = ' ' if term_pos == 0 else doc_lower[term_pos-1]
                    after_pos = term_pos + len(term_lower)
                    after_char = ' ' if after_pos >= len(doc_lower) else doc_lower[after_pos]
                    
                    # Check if term is surrounded by spaces or punctuation
                    if (before_char.isspace() or not before_char.isalnum()) and \
                       (after_char.isspace() or not after_char.isalnum()):
                        is_word = True
                    
                    # Add to results with appropriate score
                    similarity = 100.0 if is_word else 80.0
                    
                    keyword_results.append({
                        'document': meta.get('doc_id', 'unknown'),
                        'page': meta.get('page_num', 0),
                        'text': doc,
                        'similarity': similarity,
                        'source': 'keyword'
                    })
        except Exception as e:
            logging.error(f"Error during keyword search: {e}")
        
        # 3. Combine results, removing duplicates
        all_results = []
        seen_texts = set()
        
        # First add semantic results
        for result in semantic_results:
            text_hash = hash(result['text'])
            if text_hash not in seen_texts:
                all_results.append(result)
                seen_texts.add(text_hash)
        
        # Then add keyword results if not already included
        for result in keyword_results:
            text_hash = hash(result['text'])
            if text_hash not in seen_texts:
                all_results.append(result)
                seen_texts.add(text_hash)
        
        # Sort by similarity (descending)
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Limit to top_k
        final_results = all_results[:top_k]
        
        # Remove the 'source' field before returning
        for result in final_results:
            if 'source' in result:
                del result['source']

        end_time = time.time()
        logging.info(f"Search completed in {round(end_time - start_time, 3)} seconds")
        logging.info(f"Found {len(final_results)} results (semantic: {len(semantic_results)}, keyword: {len(keyword_results)})")

        return {
            'query': query_text,
            'corrected_query': None,
            'corrections': [],
            'has_corrections': False,
            'results': final_results,
            'total_results': len(final_results),
            'search_time': round(end_time - start_time, 3)
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

def enhanced_search(query_text, top_k=10):
    """
    Enhanced search function that combines semantic search with keyword matching.
    
    Args:
        query_text: The search query
        top_k: Number of results to return
        
    Returns:
        Dict: Search results
    """
    collection = get_chroma_collection()
    
    # 1. Try semantic search first
    semantic_results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    
    # 2. Try keyword search
    try:
        # First try exact match
        keyword_results = collection.get(
            where={"$contains": query_text},
            limit=top_k
        )
    except Exception:
        # If that fails, try a more basic approach
        keyword_results = {"ids": [], "documents": [], "metadatas": []}
        all_docs = collection.get()
        
        # Manual search through documents
        for i, doc in enumerate(all_docs["documents"]):
            if query_text.lower() in doc.lower():
                keyword_results["ids"].append(all_docs["ids"][i])
                keyword_results["documents"].append(doc)
                keyword_results["metadatas"].append(all_docs["metadatas"][i])
                
                if len(keyword_results["ids"]) >= top_k:
                    break
    
    # 3. Combine results (avoiding duplicates)
    combined_results = {
        "ids": semantic_results["ids"][0][:],
        "documents": semantic_results["documents"][0][:],
        "metadatas": semantic_results["metadatas"][0][:],
        "distances": semantic_results.get("distances", [[]])[0][:]
    }
    
    seen_ids = set(combined_results["ids"])
    
    for i, doc_id in enumerate(keyword_results.get("ids", [])):
        if doc_id not in seen_ids and i < len(keyword_results.get("documents", [])):
            combined_results["ids"].append(doc_id)
            combined_results["documents"].append(keyword_results["documents"][i])
            combined_results["metadatas"].append(keyword_results["metadatas"][i])
            # Add a placeholder distance
            if "distances" in combined_results:
                combined_results["distances"].append(1.0)
            seen_ids.add(doc_id)
    
    # 4. Format results for the frontend
    formatted_results = {
        "query": query_text,
        "corrected_query": query_text,  # No correction in this function
        "has_corrections": False,
        "results": [],
        "total_results": len(combined_results["ids"])
    }
    
    for i, doc_id in enumerate(combined_results["ids"]):
        if i < len(combined_results["documents"]):
            result = {
                "document_id": combined_results["metadatas"][i].get("doc_id", "unknown"),
                "page_num": combined_results["metadatas"][i].get("page_num", 0),
                "chunk_index": combined_results["metadatas"][i].get("chunk_index", 0),
                "text": combined_results["documents"][i],
                "relevance": 100 - int(combined_results.get("distances", [0])[i] * 100) if i < len(combined_results.get("distances", [])) else 50
            }
            formatted_results["results"].append(result)
    
    return formatted_results
