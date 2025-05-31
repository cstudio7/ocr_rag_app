"""
Text extraction module for PDF documents.
Uses OCR to extract text from scanned PDFs.
"""
from pdf2image import convert_from_path
import pytesseract
from concurrent.futures import ThreadPoolExecutor
import logging
import sys
import os
from sentence_transformers import SentenceTransformer

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OCR_LANGUAGE, OCR_DPI, POPPLER_PATH, MAX_WORKERS, EMBEDDING_MODEL

# Optional: Set this only if Tesseract is not in your system PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize the embedding model
model = SentenceTransformer(EMBEDDING_MODEL)

def convert_pdf_to_images(pdf_path, dpi=OCR_DPI, poppler_path=POPPLER_PATH):
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path (str): Path to the PDF file
        dpi (int): DPI for conversion
        poppler_path (str): Path to poppler binaries
        
    Returns:
        list: List of PIL Image objects
    """
    try:
        return convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    except Exception as e:
        logging.error(f"Error converting PDF to images: {e}")
        return []

def process_ocr(image, lang=OCR_LANGUAGE):
    """
    Process a single image with OCR.
    
    Args:
        image: PIL Image object
        lang (str): Language for OCR
        
    Returns:
        str: Extracted text
    """
    try:
        return pytesseract.image_to_string(image, lang=lang).strip()
    except Exception as e:
        logging.error(f"Error processing OCR: {e}")
        return ""

def chunk_text(text, page_num, max_length=500):
    """
    Split text into chunks with metadata.
    
    Args:
        text (str): Text to chunk
        page_num (int): Page number
        max_length (int): Maximum chunk length
        
    Returns:
        list: List of chunks with metadata
    """
    chunks = []
    lines = text.strip().split('\n')
    current_chunk = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # If line would make chunk too long, save current chunk and start new one
        if len(current_chunk) + len(line) > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            current_chunk = current_chunk + " " + line if current_chunk else line
            
    # Add final chunk if any
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def generate_embeddings(text_chunks):
    """
    Generate embeddings for text chunks.
    
    Args:
        text_chunks (list): List of text chunks
        
    Returns:
        list: List of embeddings
    """
    try:
        return model.encode(text_chunks, show_progress_bar=False)
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        return []

def process_image(args):
    """
    Process a single image with OCR.
    
    Args:
        args: Tuple of (image, page_num, lang)
        
    Returns:
        Dict with page_num and extracted text
    """
    image, page_num, lang = args
    try:
        logging.info(f"OCR processing page {page_num}...")
        text = pytesseract.image_to_string(image, lang=lang)
        return {
            'page_num': page_num,
            'text': text.strip()
        }
    except Exception as e:
        logging.error(f"Error processing page {page_num}: {e}")
        return {
            'page_num': page_num,
            'text': ""
        }

def extract_text_by_page(pdf_path, lang=OCR_LANGUAGE, poppler_path=POPPLER_PATH, 
                         max_workers=MAX_WORKERS, dpi=OCR_DPI, page_ranges=None):
    """
    Extracts text from each page of a scanned PDF using Tesseract OCR in parallel.
    Optimized for speed with lower DPI and page range processing.

    Args:
        pdf_path (str): Path to the input PDF file.
        lang (str): Language code for OCR (e.g., 'eng').
        poppler_path (str): Optional poppler binary path (Windows only).
        max_workers (int): Maximum number of worker threads for OCR.
        dpi (int): DPI for image conversion. Lower values are faster but less accurate.
        page_ranges (list): Optional list of page ranges to process, e.g. [(1,10), (20,30)].
                           If None, processes all pages.

    Returns:
        List[Dict]: List of {'page_num': int, 'text': str}
    """
    try:
        logging.info(f"Converting PDF to images: {pdf_path}")
        
        # Process specific page ranges if provided
        if page_ranges:
            all_images = []
            all_page_nums = []
            
            for start, end in page_ranges:
                logging.info(f"Converting pages {start} to {end}...")
                # Note: pdf2image uses 1-based indexing for first_page, last_page
                images = convert_from_path(
                    pdf_path, 
                    dpi=dpi, 
                    poppler_path=poppler_path,
                    first_page=start,
                    last_page=end
                )
                all_images.extend(images)
                all_page_nums.extend(range(start, end + 1))
                
            images = all_images
            page_nums = all_page_nums
        else:
            # Convert all pages at once
            images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
            page_nums = list(range(1, len(images) + 1))
        
        logging.info(f"PDF converted to {len(images)} images")
        
        # Prepare arguments for parallel processing
        process_args = [(image, page_num, lang) for image, page_num in zip(images, page_nums)]
        
        # Use ThreadPoolExecutor for OCR (I/O bound task)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process in smaller chunks to avoid memory issues
            chunk_size = 20  # Process 20 pages at a time
            all_results = []
            
            for i in range(0, len(process_args), chunk_size):
                chunk = process_args[i:i+chunk_size]
                logging.info(f"Processing OCR batch {i//chunk_size + 1}/{(len(process_args)-1)//chunk_size + 1}...")
                results = list(executor.map(process_image, chunk))
                all_results.extend(results)
        
        # Sort results by page number to maintain order
        all_results.sort(key=lambda x: x['page_num'])
        return all_results

    except Exception as e:
        logging.error(f"Error during PDF conversion: {e}")
        return []
