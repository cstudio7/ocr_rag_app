"""
Script to install all required dependencies for the PDF Knowledge Base application.
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip."""
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print(f"✅ {package} installed successfully")

def main():
    """Install all required dependencies for the PDF indexer."""
    print("📦 Installing required dependencies for PDF Knowledge Base...")
    
    # Core dependencies
    dependencies = [
        "flask",            # Web framework
        "PyPDF2",           # For PDF metadata extraction
        "pdf2image",        # For converting PDF to images
        "pytesseract",      # For OCR
        "sentence-transformers", # For embeddings
        "chromadb",         # Vector database
        "tqdm",             # Progress bars
        "psutil"            # System resource monitoring
    ]
    
    for package in dependencies:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✓ {package} is already installed")
        except ImportError:
            install_package(package)
    
    # Check for Tesseract OCR
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✓ Tesseract OCR is installed and accessible")
    except Exception as e:
        print("⚠️ Tesseract OCR may not be installed or not in PATH")
        print("Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
    
    # Check for Poppler
    poppler_path = r"C:\poppler-23.11.0\Library\bin"
    if os.path.exists(poppler_path):
        print("✓ Poppler appears to be installed")
    else:
        print("⚠️ Poppler may not be installed or not in the expected location")
        print("Please install Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
    
    print("\n✅ All dependencies checked. Run app.py to start the application.")

if __name__ == "__main__":
    main()
