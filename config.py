"""
Configuration settings for the PDF Knowledge Base application.
"""
import os
import logging
from pathlib import Path
from datetime import timedelta

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

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Database settings
DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(DATA_DIR, "app.db")}'
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Session settings
PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Remember me duration
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Authentication settings
LOGIN_DISABLED = False  # Set to True to disable authentication (for development)

# Embedding model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "documents"

# OCR configuration
OCR_LANGUAGE = "eng"
OCR_DPI = 200  # Lower for faster processing, higher for better quality

# Detect OS and set appropriate Poppler path
import platform
if platform.system() == "Windows":
    POPPLER_PATH = r"C:\\poppler-23.11.0\\Library\\bin"
elif platform.system() == "Darwin":  # macOS
    # For Apple Silicon Macs
    POPPLER_PATH = "/opt/homebrew/bin"
else:  # Linux
    POPPLER_PATH = "/usr/bin"  # Default on most Linux distributions

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
