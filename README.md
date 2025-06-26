# Save the README content to a .md file

readme_content = """
# OCR RAG App

This is an OCR-based Retrieval-Augmented Generation (RAG) web application built with Flask. It supports extracting text from PDFs using OCR (Optical Character Recognition) and enables processing and storage of data with modern NLP tools.

---

## 🚀 Features

- Upload and extract text from PDF files
- OCR using Tesseract and PDF to image conversion with Poppler
- Search and retrieval using `chromadb` and `sentence-transformers`
- Flask-based web interface with user authentication
- SQLAlchemy for database integration
- Spellchecking support
- Progress tracking with `tqdm`

---

## 🛠 Requirements

### 📦 Python Packages

Install all required packages via:

```bash
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
pip install -r requirements.txt
