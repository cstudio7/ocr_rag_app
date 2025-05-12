import os
from pdf2image import convert_from_path
import pytesseract

# Optional: Set this only if Tesseract is not in your system PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_by_page(pdf_path, lang='eng', poppler_path=None):
    """
    Extracts text from each page of a scanned PDF using Tesseract OCR.

    Args:
        pdf_path (str): Path to the input PDF file.
        lang (str): Language code for OCR (e.g., 'eng').
        poppler_path (str): Optional poppler binary path (Windows only).

    Returns:
        List[Dict]: List of {'page_num': int, 'text': str}
    """
    try:
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        output = []

        for i, image in enumerate(images):
            print(f"Processing page {i + 1}...")
            text = pytesseract.image_to_string(image, lang=lang)
            output.append({
                'page_num': i + 1,
                'text': text.strip()
            })

        return output

    except Exception as e:
        print(f"Error during OCR: {e}")
        return []

# Example usage
if __name__ == "__main__":
    pdf_file = "TMC0058.pdf"
    poppler_bin_path = r"C:\poppler\bin"  # Change if your poppler is elsewhere

    results = extract_text_by_page(pdf_file, poppler_path=poppler_bin_path)

    for page in results:
        print(f"\n--- Page {page['page_num']} ---")
        print(page['text'][:500])  # Preview first 500 characters
