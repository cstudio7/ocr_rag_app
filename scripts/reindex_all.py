"""
Script to reindex all PDF files in the pdfs directory.
This will ensure all documents are properly indexed and persisted.
"""
import os
import sys
import time
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PDF_DIR, LOG_LEVEL, LOG_FORMAT
from core.indexer import index_pdf

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler("logs/reindex.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def reindex_all_pdfs():
    """Reindex all PDFs in the pdfs directory."""
    if not os.path.exists(PDF_DIR):
        logging.error(f"❌ PDF directory '{PDF_DIR}' not found!")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logging.error(f"❌ No PDF files found in '{PDF_DIR}'!")
        return
    
    logging.info(f"📄 Found {len(pdf_files)} PDF file(s) to reindex")
    
    # Process each PDF
    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        doc_id = os.path.splitext(pdf_file)[0]
        
        logging.info(f"📄 [{i+1}/{len(pdf_files)}] Reindexing: {pdf_file}")
        
        start_time = time.time()
        try:
            index_pdf(pdf_path)
            end_time = time.time()
            logging.info(f"✅ Successfully reindexed {doc_id} in {end_time - start_time:.2f} seconds")
        except Exception as e:
            logging.error(f"❌ Failed to reindex {doc_id}: {str(e)}")
    
    logging.info("🎉 Reindexing complete!")

if __name__ == "__main__":
    logging.info("🔄 Starting reindexing process")
    reindex_all_pdfs()
