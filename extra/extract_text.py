"""
Text extraction module for PDF documents.
Uses OCR to extract text from scanned PDFs and generate sentence embeddings.
"""

import os
import sys
import platform
import logging
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytesseract
from pdf2image import convert_from_path
from sentence_transformers import SentenceTransformer

# Configuration constants (can be moved to a config file)
OCR_LANGUAGE = "eng"
OCR_DPI = 200
MAX_WORKERS = 4
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_POPPLER_PATH = "/opt/homebrew/bin"  # Adjust if needed for macOS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_tesseract_path():
    """Detect and return the tesseract executable path."""
    if platform.system().lower() == "windows":
        path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Tesseract not found at {path}")
        return path
    else:
        path = shutil.which("tesseract")
        if path is None:
            raise FileNotFoundError("Tesseract not found in PATH. Install it via `brew install tesseract`.")
        return path


def get_poppler_path():
    """Return poppler path based on OS."""
    if platform.system().lower() == "windows":
        return os.getenv("POPPLER_PATH", None)  # Set in environment or config
    return DEFAULT_POPPLER_PATH


def initialize_ocr():
    """Configure pytesseract with the correct binary path."""
    tesseract_path = get_tesseract_path()
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    logging.info(f"Tesseract found at: {tesseract_path}")


def load_model(model_name):
    """Load SentenceTransformer model."""
    try:
        return SentenceTransformer(model_name)
    except Exception as e:
        logging.error(f"Failed to load embedding model: {e}")
        raise


def convert_pdf_to_images(pdf_path, dpi=OCR_DPI, poppler_path=None, page_ranges=None):
    """Convert PDF pages to images (optionally by range)."""
    poppler_path = poppler_path or get_poppler_path()

    try:
        if page_ranges:
            images, page_nums = [], []
            for start, end in page_ranges:
                partial_images = convert_from_path(
                    pdf_path, dpi=dpi, poppler_path=poppler_path, first_page=start, last_page=end
                )
                images.extend(partial_images)
                page_nums.extend(range(start, end + 1))
        else:
            images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
            page_nums = list(range(1, len(images) + 1))

        logging.info(f"Converted {len(images)} pages from PDF.")
        return list(zip(images, page_nums))

    except Exception as e:
        logging.error(f"PDF to image conversion failed: {e}")
        return []


def perform_ocr(image, lang=OCR_LANGUAGE):
    """Run Tesseract OCR on a PIL image."""
    try:
        return pytesseract.image_to_string(image, lang=lang).strip()
    except Exception as e:
        logging.error(f"OCR failed: {e}")
        return ""


def process_image(args):
    image, page_num, lang = args
    text = perform_ocr(image, lang)
    return {'page_num': page_num, 'text': text}


def extract_text_by_page(pdf_path, lang=OCR_LANGUAGE, page_ranges=None, max_workers=MAX_WORKERS):
    """Extract OCR text from a PDF using parallel threads."""
    images_with_nums = convert_pdf_to_images(pdf_path, page_ranges=page_ranges)
    if not images_with_nums:
        return []

    args = [(img, page, lang) for img, page in images_with_nums]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_image, args))

    return sorted(results, key=lambda x: x['page_num'])


def chunk_text(text, max_length=500):
    """Split text into clean chunks with length constraints."""
    lines = text.strip().split('\n')
    chunks, current = [], ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(current) + len(line) > max_length:
            if current:
                chunks.append(current.strip())
            current = line
        else:
            current += (" " + line) if current else line

    if current:
        chunks.append(current.strip())

    return chunks


def generate_embeddings(text_chunks, model):
    """Encode text chunks using a transformer model."""
    try:
        return model.encode(text_chunks, show_progress_bar=False)
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        return []


# ----------------
# Example Usage
# ----------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract and embed text from a scanned PDF.")
    parser.add_argument("pdf", help="Path to the PDF file")
    args = parser.parse_args()

    try:
        initialize_ocr()
        model = load_model(EMBEDDING_MODEL)

        results = extract_text_by_page(args.pdf)
        for page in results:
            logging.info(f"Page {page['page_num']}: {len(page['text'])} characters extracted.")

        all_chunks = []
        for result in results:
            chunks = chunk_text(result['text'])
            all_chunks.extend(chunks)

        embeddings = generate_embeddings(all_chunks, model)
        logging.info(f"Generated {len(embeddings)} embeddings.")

    except Exception as ex:
        logging.exception(f"Unhandled exception: {ex}")
