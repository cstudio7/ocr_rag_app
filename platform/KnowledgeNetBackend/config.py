"""
Configuration settings for the PDF Knowledge Base application.
"""
import os
import logging
import warnings
from pathlib import Path
from datetime import timedelta

# Suppress common warnings that don't affect functionality
warnings.filterwarnings("ignore", message=".*huggingface.*tokenizers.*parallelism.*")
warnings.filterwarnings("ignore", message=".*np.NaN.*removed.*NumPy 2.0.*")
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

# Set environment variable to suppress tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
OCR_DPI = 250  # Optimal DPI for this document type (tested and verified)

# Cross-platform Poppler and Tesseract configuration
def get_poppler_path():
    """
    Get the appropriate Poppler path for the current platform.
    Returns None if Poppler should be found in PATH.
    """
    import platform
    import shutil

    system = platform.system().lower()

    # First, check if poppler is already in PATH
    if shutil.which('pdftoppm') is not None:
        logging.info("Poppler found in system PATH")
        return None

    # Platform-specific paths
    if system == 'windows':
        # Common Windows installation paths
        possible_paths = [
            r"C:\poppler\Library\bin",
            r"C:\poppler-23.11.0\Library\bin",
            r"C:\Program Files\poppler\bin",
            r"C:\Program Files (x86)\poppler\bin",
            os.path.expanduser("~/poppler/bin"),
            os.path.expanduser("~/Downloads/poppler/bin")
        ]

        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'pdftoppm.exe')):
                logging.info(f"Found Poppler at: {path}")
                return path

        # If not found, return None and let the system handle it
        logging.warning("Poppler not found in common Windows paths. Please install Poppler or add it to PATH.")
        return None

    elif system == 'darwin':  # macOS
        # Check common macOS paths
        possible_paths = [
            '/usr/local/bin',
            '/opt/homebrew/bin',
            '/usr/bin'
        ]

        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'pdftoppm')):
                logging.info(f"Found Poppler at: {path}")
                return path

        # On macOS, usually installed via Homebrew and in PATH
        logging.info("Using system PATH for Poppler on macOS")
        return None

    else:  # Linux and other Unix-like systems
        logging.info("Using system PATH for Poppler on Unix-like system")
        return None

def get_tesseract_path():
    """
    Get the appropriate Tesseract path for the current platform.
    Returns None if Tesseract should be found in PATH.
    """
    import platform
    import shutil

    system = platform.system().lower()

    # First, check if tesseract is already in PATH
    if shutil.which('tesseract') is not None:
        logging.info("Tesseract found in system PATH")
        return None

    # Platform-specific paths
    if system == 'windows':
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
            os.path.expanduser("~/AppData/Local/Tesseract-OCR/tesseract.exe")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logging.info(f"Found Tesseract at: {path}")
                return path

        logging.warning("Tesseract not found in common Windows paths. Please install Tesseract or add it to PATH.")
        return None

    elif system == 'darwin':  # macOS
        # Check common macOS paths
        possible_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            '/usr/bin/tesseract'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logging.info(f"Found Tesseract at: {path}")
                return path

        logging.info("Using system PATH for Tesseract on macOS")
        return None

    else:  # Linux and other Unix-like systems
        logging.info("Using system PATH for Tesseract on Unix-like system")
        return None

# Set the paths
POPPLER_PATH = get_poppler_path()
TESSERACT_PATH = get_tesseract_path()

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

# Suppress ChromaDB logging errors and verbose output
logging.getLogger("chromadb.db.mixins.embeddings_queue").setLevel(logging.CRITICAL)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

# Configure logging formatter to truncate very long messages
class TruncatingFormatter(logging.Formatter):
    def format(self, record):
        # Truncate very long log messages (like embedding arrays)
        if len(str(record.msg)) > 500:
            record.msg = str(record.msg)[:500] + "... [truncated]"
        return super().format(record)

# Apply truncating formatter to all handlers
for handler in logging.getLogger().handlers:
    handler.setFormatter(TruncatingFormatter(LOG_FORMAT))

# ChromaDB batch size
CHROMA_BATCH_SIZE = 100

# Search configuration
SEARCH_TOP_K = 10  # Number of results to return
SEARCH_THRESHOLD = 50  # Minimum similarity score (0-100) to include in results
