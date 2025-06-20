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
import platform

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OCR_LANGUAGE, OCR_DPI, POPPLER_PATH, MAX_WORKERS

# Set Tesseract path based on OS
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
elif platform.system() == "Darwin":  # macOS
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
else:  # Linux
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

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
    """
    try:
        # Verify poppler is installed and accessible
        if poppler_path:
            # Check if poppler is in the specified path
            if os.name == 'nt':  # Windows
                pdfinfo_path = os.path.join(poppler_path, "pdfinfo.exe")
            else:  # macOS/Linux
                pdfinfo_path = os.path.join(poppler_path, "pdfinfo")
            
            if not os.path.exists(pdfinfo_path):
                logging.error(f"Poppler not found at {poppler_path}. Checking system PATH...")
                poppler_path = None
        
        # If poppler_path is None or not found, try to find it in system PATH
        if not poppler_path:
            import shutil
            pdfinfo_in_path = shutil.which("pdfinfo")
            if pdfinfo_in_path:
                poppler_path = os.path.dirname(pdfinfo_in_path)
                logging.info(f"Found Poppler in system PATH: {poppler_path}")
            else:
                logging.error("Poppler not found in system PATH. Please install Poppler.")
                logging.error("On macOS: brew install poppler")
                logging.error("On Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/")
                logging.error("On Linux: apt-get install poppler-utils")
                return []
        
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
        
        logging.info(f"Successfully converted {len(images)} pages to images")
        
        # Process images with OCR in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            all_results = list(executor.map(
                process_image, 
                [(img, num, lang) for img, num in zip(images, page_nums)]
            ))
        
        # Sort results by page number to maintain order
        all_results.sort(key=lambda x: x['page_num'])
        return all_results

    except Exception as e:
        logging.error(f"Error during PDF conversion: {e}")
        return []
