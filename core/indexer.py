"""
PDF indexing module for processing and indexing PDF documents.
"""
import os
import logging
import time
import hashlib
import pickle
import sys
import chromadb
from chromadb.utils import embedding_functions
try:
    import PyPDF2
except ImportError:
    logging.warning("PyPDF2 not installed. Will use alternative method to count pages.")

# Import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    VECTOR_STORE_DIR, CACHE_DIR, CHROMA_BATCH_SIZE, MAX_WORKERS,
    POPPLER_PATH, EMBEDDING_MODEL, COLLECTION_NAME
)
from core.extract import (
    extract_text_by_page, convert_pdf_to_images,
    process_ocr, chunk_text, generate_embeddings
)
from core.embedding import embed_chunks

# Create necessary directories
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize ChromaDB client once
_client = None
_collection = None

def get_chroma_collection():
    """
    Get or initialize the ChromaDB collection.
    Uses a singleton pattern to avoid recreating the client.
    Ensures proper persistence to disk.
    """
    global _client, _collection

    if _client is None:
        try:
            # First try with PersistentClient for better persistence
            logging.info(f"Initializing ChromaDB PersistentClient at {os.path.abspath(VECTOR_STORE_DIR)}")
            _client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        except Exception as e:
            logging.warning(f"Error initializing PersistentClient: {e}")
            logging.info("Falling back to regular Client with persistence settings")
            _client = chromadb.Client(chromadb.config.Settings(
                persist_directory=VECTOR_STORE_DIR,
                anonymized_telemetry=False
            ))

        try:
            # Set up embedding function with explicit CPU device
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL,
                device="cpu"  # Explicitly use CPU to avoid CUDA/device issues
            )

            # Get or create collection
            _collection = _client.get_or_create_collection(COLLECTION_NAME, embedding_function=embed_fn)

            # Force persistence by adding and then deleting a test document
            try:
                test_id = "test_persistence"
                if test_id not in [id for id in _collection.get()['ids']]:
                    _collection.add(
                        documents=["Test document for persistence"],
                        ids=[test_id],
                        metadatas=[{"test": True}]
                    )
                    _collection.delete(ids=[test_id])
                    logging.info("Persistence test successful")
            except Exception as e:
                logging.warning(f"Persistence test failed: {e}")

        except Exception as e:
            # Handle PyTorch/embedding function errors
            logging.warning(f"Error with embedding function: {e}")
            logging.info("Creating collection without embedding function")
            # Create collection without embedding function for basic operations
            _collection = _client.get_or_create_collection(COLLECTION_NAME)

    return _collection

def get_file_hash(file_path):
    """
    Generate a hash for the file to use as cache key.
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)  # Read in 64k chunks
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def check_cache(file_path, doc_id):
    """
    Check if the PDF has already been processed and cached.
    Returns the cached data if available, None otherwise.
    """
    file_hash = get_file_hash(file_path)
    cache_path = os.path.join(CACHE_DIR, f"{doc_id}_{file_hash}.pkl")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                logging.info(f"Using cached data for {doc_id}")
                return pickle.load(f)
        except Exception as e:
            logging.warning(f"Cache read error for {doc_id}: {e}")

    return None

def save_to_cache(file_path, doc_id, data):
    """
    Save processed data to cache.
    """
    file_hash = get_file_hash(file_path)
    cache_path = os.path.join(CACHE_DIR, f"{doc_id}_{file_hash}.pkl")

    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        logging.info(f"Saved {doc_id} to cache")
    except Exception as e:
        logging.warning(f"Cache write error for {doc_id}: {e}")

def process_and_embed_pages(file_path, doc_id):
    """
    Extract text from PDF pages and generate embeddings.
    Returns a list of processed chunks with embeddings.
    Uses a chunked approach for large PDFs to avoid memory issues.
    """
    # Check cache first
    cached_data = check_cache(file_path, doc_id)
    if cached_data is not None:
        return cached_data

    # For large PDFs, process in chunks of 50 pages
    chunk_size = 50
    all_chunks = []

    # First, determine total number of pages
    try:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            total_pages = len(pdf.pages)
            logging.info(f"PDF has {total_pages} pages")
    except Exception as e:
        logging.warning(f"Error reading PDF metadata with PyPDF2: {e}")
        # Fallback method: try to get page count using pdf2image
        try:
            import subprocess
            # Try using pdfinfo from poppler if available
            cmd = os.path.join(POPPLER_PATH, "pdfinfo.exe") if os.name == 'nt' else "pdfinfo"

            output = subprocess.check_output([cmd, file_path], universal_newlines=True)
            for line in output.splitlines():
                if "Pages:" in line:
                    total_pages = int(line.split(":")[1].strip())
                    logging.info(f"PDF has {total_pages} pages (from pdfinfo)")
                    break
        except Exception as e2:
            logging.error(f"Error getting page count with fallback method: {e2}")
            # Fall back to processing all at once
            total_pages = 0

    # If it's a large PDF, process in chunks
    if total_pages > chunk_size:
        logging.info(f"Processing large PDF in chunks of {chunk_size} pages")

        # Create page ranges
        page_ranges = []
        for start in range(1, total_pages + 1, chunk_size):
            end = min(start + chunk_size - 1, total_pages)
            page_ranges.append((start, end))

        # Process each chunk
        for i, page_range in enumerate(page_ranges):
            logging.info(f"Processing chunk {i+1}/{len(page_ranges)}: pages {page_range[0]}-{page_range[1]}")

            # Extract text for this chunk
            pages = extract_text_by_page(
                file_path,
                poppler_path=POPPLER_PATH,
                max_workers=MAX_WORKERS,
                dpi=200,  # Lower DPI for faster processing
                page_ranges=[page_range]
            )

            if not pages:
                logging.warning(f"No text extracted from chunk {i+1}")
                continue

            # Generate embeddings for this chunk
            logging.info(f"Generating embeddings for {len(pages)} pages from chunk {i+1}")
            chunk_chunks = embed_chunks(pages, doc_id, batch_size=64)
            all_chunks.extend(chunk_chunks)

            # Intermediate progress report
            logging.info(f"Processed {page_range[1]} of {total_pages} pages ({(page_range[1]/total_pages)*100:.1f}%)")
    else:
        # For smaller PDFs, process all at once
        pages = extract_text_by_page(
            file_path,
            poppler_path=POPPLER_PATH,
            max_workers=MAX_WORKERS,
            dpi=200  # Lower DPI for faster processing
        )

        if not pages:
            logging.error(f"No text extracted from {doc_id}")
            return []

        # Generate embeddings with batching
        logging.info(f"Generating embeddings for {len(pages)} pages from {doc_id}")
        all_chunks = embed_chunks(pages, doc_id, batch_size=64)

    # Save to cache
    if all_chunks:
        save_to_cache(file_path, doc_id, all_chunks)
    else:
        logging.error(f"No chunks generated for {doc_id}")

    return all_chunks

def add_chunks_to_db(chunks, doc_id, category="Uncategorized", batch_size=CHROMA_BATCH_SIZE, progress_callback=None):
    """
    Add chunks to ChromaDB in batches for better performance.
    Optimized with smaller batch sizes and incremental updates.
    """
    if not chunks:
        logging.warning(f"No chunks to add for {doc_id}")
        return

    collection = get_chroma_collection()
    total_chunks = len(chunks)
    logging.info(f"Adding {total_chunks} chunks to vector store for {doc_id}")

    # Use smaller batch size for very large documents to avoid memory issues
    if total_chunks > 1000:
        adjusted_batch_size = min(batch_size, 50)  # Reduce batch size for large docs
        logging.info(f"Adjusting batch size to {adjusted_batch_size} for large document")
    else:
        adjusted_batch_size = batch_size

    # Check for existing document chunks to avoid duplicates
    try:
        existing_ids = collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )
        if existing_ids and 'ids' in existing_ids and existing_ids['ids']:
            if progress_callback:
                progress_callback(f"Found {len(existing_ids['ids'])} existing chunks for {doc_id}")
            # Option to delete existing chunks
            # collection.delete(where={"doc_id": doc_id})
            # logging.info(f"Deleted existing chunks for {doc_id}")
    except Exception as e:
        logging.warning(f"Error checking for existing chunks: {e}")
        existing_ids = None

    # Process in batches with progress tracking
    total_batches = (total_chunks - 1) // adjusted_batch_size + 1

    for i in range(0, total_chunks, adjusted_batch_size):
        batch = chunks[i:i+adjusted_batch_size]
        batch_num = i // adjusted_batch_size + 1

        # Prepare batch data
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for chunk in batch:
            uid = f"{doc_id}_p{chunk['page_num']}_c{chunk['chunk_index']}"

            # Skip if this ID already exists
            if (existing_ids and 'ids' in existing_ids and
                uid in existing_ids['ids']):
                if progress_callback:
                    progress_callback(f"Skipping batch {batch_num}/{total_batches} (already indexed)")
                continue

            ids.append(uid)
            documents.append(chunk['text'])
            embeddings.append(chunk['embedding'])

            metadatas.append({
                'doc_id': doc_id,
                'page_num': chunk['page_num'],
                'chunk_index': chunk['chunk_index'],
                'category': category,
                'upload_date': time.strftime('%Y-%m-%d'),
                'last_updated': time.strftime('%Y-%m-%d')
            })

        # Skip empty batches
        if not ids:
            continue

        # Add batch to ChromaDB
        try:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
            if progress_callback:
                progress_callback(f"Added batch {batch_num}/{total_batches} to vector store ({len(ids)} chunks)")
        except Exception as e:
            logging.error(f"Error adding batch {batch_num}: {e}")

        # Report progress percentage
        progress = min(100, (i + adjusted_batch_size) / total_chunks * 100)
        if progress_callback:
            progress_callback(f"Database progress: {progress:.1f}%")

def build_knowledge_base_optimized(file_path, doc_id, category="Uncategorized"):
    """
    Optimized version of knowledge base building with:
    - Parallel OCR processing
    - Batched embeddings
    - Batched ChromaDB additions
    - Caching of processed data
    """
    start_time = time.time()

    # Process PDF and generate embeddings
    chunks = process_and_embed_pages(file_path, doc_id)

    if not chunks:
        logging.error(f"No chunks generated for {doc_id}")
        return False

    # Add chunks to vector database with category
    add_chunks_to_db(chunks, doc_id, category)

    end_time = time.time()
    logging.info(f"Finished indexing {doc_id} in {round(end_time - start_time, 2)} seconds")
    return True

def index_pdf(pdf_path, category="Uncategorized", progress_callback=None):
    """Index a PDF document and store it in the vector database."""
    try:
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if progress_callback:
            progress_callback(f"Starting indexing for {doc_id}")
        
        # Convert PDF to images
        if progress_callback:
            progress_callback(f"Converting PDF to images: {pdf_path}")
            
        images = convert_pdf_to_images(pdf_path)
        total_pages = len(images)
        
        if progress_callback:
            progress_callback(f"PDF has {total_pages} pages")
            progress_callback(f"PDF converted to {total_pages} images")
        
        # Process OCR in batches
        text_chunks = []
        for i, image in enumerate(images, 1):
            if progress_callback:
                progress_callback(f"OCR processing page {i}...")
            
            # Process OCR for this page
            page_text = process_ocr(image)
            text_chunks.extend(chunk_text(page_text, i))
        
        if progress_callback:
            progress_callback(f"Generating embeddings for {total_pages} pages from {doc_id}")
            
        # Generate embeddings
        chunks_with_embeddings = generate_embeddings(text_chunks)
        
        if progress_callback:
            progress_callback(f"Adding {len(chunks_with_embeddings)} chunks to vector store for {doc_id}")
            
        # Add to vector store with progress updates
        add_chunks_to_db(chunks_with_embeddings, doc_id, category, progress_callback=progress_callback)
        
        if progress_callback:
            progress_callback(f"Finished indexing {doc_id}")
            
        return True
        
    except Exception as e:
        logging.error(f"Error indexing PDF {pdf_path}: {e}")
        if progress_callback:
            progress_callback(f"Error indexing PDF: {str(e)}")
        return False
