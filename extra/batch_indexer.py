import os
from indexer import build_knowledge_base

PDF_FOLDER = "pdfs"  # Place your PDFs in this folder

# Create the folder if it doesn't exist
os.makedirs(PDF_FOLDER, exist_ok=True)

def index_all_pdfs():
    files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    if not files:
        print("❌ No PDF files found in 'pdfs' folder.")
        return

    for file in files:
        path = os.path.join(PDF_FOLDER, file)
        doc_id = os.path.splitext(file)[0]
        print(f"📄 Indexing {file}...")
        build_knowledge_base(path, doc_id)
        print(f"✅ Done indexing {file}\n")

if __name__ == "__main__":
    index_all_pdfs()