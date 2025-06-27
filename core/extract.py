"""
Smart text extraction module for PDF documents.
Uses direct PDF text extraction first, falls back to OCR for scanned documents.
Handles both native PDFs and image-based PDFs with optimal performance.
"""
from pdf2image import convert_from_path
import pytesseract
from concurrent.futures import ThreadPoolExecutor
import logging
import sys
import os

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OCR_LANGUAGE, OCR_DPI, POPPLER_PATH, TESSERACT_PATH, MAX_WORKERS

# Set Tesseract path if found by configuration
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    logging.info(f"Using Tesseract at: {TESSERACT_PATH}")
else:
    logging.info("Using Tesseract from system PATH")

def extract_text_direct_pymupdf(pdf_path):
    """
    Extract text directly from PDF using PyMuPDF (fastest method).

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        List[Dict]: List of {'page_num': int, 'text': str} or None if failed
    """
    try:
        import fitz  # PyMuPDF

        logging.info(f"Attempting direct text extraction with PyMuPDF: {pdf_path}")

        doc = fitz.open(pdf_path)
        pages_text = []
        total_chars = 0

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()

            pages_text.append({
                'page_num': page_num + 1,
                'text': page_text
            })

            total_chars += len(page_text.strip())

        doc.close()

        # Check if we got meaningful text (threshold: 50 chars per page on average)
        avg_chars_per_page = total_chars / len(pages_text) if pages_text else 0

        if avg_chars_per_page > 50:
            logging.info(f"PyMuPDF successful: {total_chars} characters from {len(pages_text)} pages")
            return pages_text
        else:
            logging.info(f"PyMuPDF extracted minimal text ({total_chars} chars), likely scanned PDF")
            return None

    except ImportError:
        logging.info("PyMuPDF not available, skipping direct extraction")
        return None
    except Exception as e:
        logging.warning(f"PyMuPDF extraction failed: {e}")
        return None

def extract_text_direct_pdfplumber(pdf_path):
    """
    Extract text directly from PDF using PDFPlumber (alternative method).

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        List[Dict]: List of {'page_num': int, 'text': str} or None if failed
    """
    try:
        import pdfplumber

        logging.info(f"Attempting direct text extraction with PDFPlumber: {pdf_path}")

        pages_text = []
        total_chars = 0

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""

                pages_text.append({
                    'page_num': i,
                    'text': page_text
                })

                total_chars += len(page_text.strip())

        # Check if we got meaningful text
        avg_chars_per_page = total_chars / len(pages_text) if pages_text else 0

        if avg_chars_per_page > 50:
            logging.info(f"PDFPlumber successful: {total_chars} characters from {len(pages_text)} pages")
            return pages_text
        else:
            logging.info(f"PDFPlumber extracted minimal text ({total_chars} chars), likely scanned PDF")
            return None

    except ImportError:
        logging.info("PDFPlumber not available, skipping direct extraction")
        return None
    except Exception as e:
        logging.warning(f"PDFPlumber extraction failed: {e}")
        return None

def process_image(args):
    """
    Process a single image with OCR using optimized settings.

    Args:
        args: Tuple of (image, page_num, lang)

    Returns:
        Dict with page_num and extracted text
    """
    image, page_num, lang = args
    try:
        logging.info(f"OCR processing page {page_num}...")

        # Use optimized OCR configuration for better accuracy
        # PSM 6 works well for document blocks, PSM 1 for full page analysis
        custom_config = r'--oem 3 --psm 6'

        try:
            # Try with optimized config first
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)

            # If we get very little text, try PSM 1 (full page analysis)
            if len(text.strip()) < 10:
                text = pytesseract.image_to_string(image, lang=lang, config=r'--oem 3 --psm 1')

        except:
            # Fallback to basic OCR if custom config fails
            text = pytesseract.image_to_string(image, lang=lang)

        # Clean up the extracted text
        text = text.strip()

        # Log success with text length for debugging
        if text:
            logging.info(f"OCR page {page_num}: extracted {len(text)} characters")
        else:
            logging.warning(f"OCR page {page_num}: no text extracted")

        return {
            'page_num': page_num,
            'text': text
        }
    except Exception as e:
        logging.error(f"Error processing page {page_num}: {e}")
        return {
            'page_num': page_num,
            'text': ""
        }

def extract_text_by_page_smart(pdf_path, lang=OCR_LANGUAGE, poppler_path=POPPLER_PATH,
                              max_workers=MAX_WORKERS, dpi=OCR_DPI, page_ranges=None):
    """
    Smart text extraction that tries direct PDF text extraction first,
    falls back to OCR for scanned documents.

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
    logging.info(f"Starting smart text extraction for: {pdf_path}")

    # Try direct text extraction first (PyMuPDF)
    pages_text = extract_text_direct_pymupdf(pdf_path)
    if pages_text:
        logging.info("Direct text extraction successful with PyMuPDF")
        return pages_text

    # Try PDFPlumber as backup
    pages_text = extract_text_direct_pdfplumber(pdf_path)
    if pages_text:
        logging.info("Direct text extraction successful with PDFPlumber")
        return pages_text

    # Fall back to OCR for scanned documents
    logging.info("Direct extraction failed, falling back to OCR")
    return extract_text_by_page_ocr(pdf_path, lang, poppler_path, max_workers, dpi, page_ranges)

def extract_text_by_page(pdf_path, lang=OCR_LANGUAGE, poppler_path=POPPLER_PATH,
                         max_workers=MAX_WORKERS, dpi=OCR_DPI, page_ranges=None):
    """
    Main text extraction function - uses smart extraction by default.

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
    return extract_text_by_page_smart(pdf_path, lang, poppler_path, max_workers, dpi, page_ranges)

def extract_text_by_page_ocr(pdf_path, lang=OCR_LANGUAGE, poppler_path=POPPLER_PATH,
                             max_workers=MAX_WORKERS, dpi=OCR_DPI, page_ranges=None):
    """
    Extracts text from each page of a scanned PDF using Tesseract OCR in parallel.
    This is the OCR-only version, used as fallback when direct extraction fails.

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
