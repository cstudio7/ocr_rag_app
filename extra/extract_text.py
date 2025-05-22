from pdf2image import convert_from_path
import pytesseract
from concurrent.futures import ThreadPoolExecutor
import logging

# Optional: Set this only if Tesseract is not in your system PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

def extract_text_by_page(pdf_path, lang='eng', poppler_path=None, max_workers=None, dpi=200, page_ranges=None):
    """
    Extracts text from each page of a scanned PDF using Tesseract OCR in parallel.
    Optimized for speed with lower DPI and page range processing.

    Args:
        pdf_path (str): Path to the input PDF file.
        lang (str): Language code for OCR (e.g., 'eng').
        poppler_path (str): Optional poppler binary path (Windows only).
        max_workers (int): Maximum number of worker threads for OCR. Default is None (uses CPU count).
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

# Example usage
if __name__ == "__main__":
    pdf_file = "TMC0058.pdf"
    poppler_bin_path = r"C:\poppler\bin"  # Change if your poppler is elsewhere

    results = extract_text_by_page(pdf_file, poppler_path=poppler_bin_path)

    for page in results:
        print(f"\n--- Page {page['page_num']} ---")
        print(page['text'][:500])  # Preview first 500 characters
