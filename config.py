"""
Configuration settings for the PDF Knowledge Base application.
"""
import os
import logging
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# PDF storage
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# Vector database
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# Cache directory
CACHE_DIR = os.path.join(DATA_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Flask configuration
FLASK_DEBUG = True
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max upload size

# Embedding model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "documents"

# OCR configuration
OCR_LANGUAGE = "eng"
OCR_DPI = 200  # Lower for faster processing, higher for better quality
POPPLER_PATH = r"C:\\poppler-23.11.0\\Library\\bin"  # Adjust for your system

# Parallel processing
MAX_WORKERS = None  # None = use CPU count - 1

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_FILE = os.path.join(LOGS_DIR, "pdf_indexer.log")

# Initialize logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# ChromaDB batch size
CHROMA_BATCH_SIZE = 100

# Search configuration
SEARCH_TOP_K = 10  # Number of results to return
SEARCH_THRESHOLD = 50  # Minimum similarity score (0-100) to include in results
