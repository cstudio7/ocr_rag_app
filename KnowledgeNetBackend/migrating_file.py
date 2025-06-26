import os
import shutil
from config import PDF_DIR
from app.core.search import get_document_list

def organize_existing_pdfs():
    documents = get_document_list()

    for doc in documents:
        doc_id = doc['doc_id']
        folder = doc.get('folder', 'uncategorized')
        src_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
        dest_folder = os.path.join(PDF_DIR, folder)
        dest_path = os.path.join(dest_folder, f"{doc_id}.pdf")

        if os.path.exists(src_path):
            os.makedirs(dest_folder, exist_ok=True)
            shutil.move(src_path, dest_path)
            print(f"Moved {src_path} -> {dest_path}")
        else:
            print(f"File not found: {src_path}")

if __name__ == "__main__":
    organize_existing_pdfs()
