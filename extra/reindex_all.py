"""
Script to reindex all PDF files in the pdfs directory.
This will ensure all documents are properly indexed and persisted.
"""
import os
import sys
import time
import logging
from parallel_indexer import index_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("reindex.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def reindex_all_pdfs():
    """Reindex all PDFs in the pdfs directory."""
    pdf_dir = "pdfs"
    
    if not os.path.exists(pdf_dir):
        logging.error(f"❌ PDF directory '{pdf_dir}' not found!")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logging.error(f"❌ No PDF files found in '{pdf_dir}'!")
        return
    
    logging.info(f"📄 Found {len(pdf_files)} PDF file(s) to reindex")
    
    # Process each PDF
    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(pdf_dir, pdf_file)
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
