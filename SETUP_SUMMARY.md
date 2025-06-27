# Setup Files Summary - OCR RAG App

This document provides an overview of all the setup and installation files available for the OCR RAG App.

## 📁 Setup Files Overview

| File | Purpose | Recommended For |
|------|---------|-----------------|
| `quick_setup.py` | **One-click installation** with colored output and fallback options | **Most users** |
| `install.py` | Simple, fast installation script | Quick testing |
| `setup.py` | Comprehensive setup with system dependency installation | Production environments |
| `requirements.txt` | Full Python package dependencies | Standard installation |
| `requirements-minimal.txt` | Minimal dependencies for basic functionality | Systems with build issues |

## 📋 Documentation Files

| File | Content |
|------|---------|
| `INSTALL.md` | Detailed installation guide with troubleshooting |
| `SETUP_GUIDE.md` | Platform-specific setup instructions |
| `README.md` | Main project documentation with quick start |

## 🚀 Quick Start Options

### Option 1: Recommended (One-Click)
```bash
python quick_setup.py
```
- ✅ Colored output and progress indicators
- ✅ Automatic fallback to minimal requirements if needed
- ✅ System dependency checking
- ✅ Installation testing

### Option 2: Simple Installation
```bash
python install.py
```
- ✅ Fast and straightforward
- ✅ Basic dependency checking
- ✅ Good for quick testing

### Option 3: Comprehensive Setup
```bash
python setup.py
```
- ✅ Full system dependency installation
- ✅ Detailed logging and error handling
- ✅ Best for production environments

## 📦 Requirements Files

### requirements.txt (Full Installation)
Contains all dependencies including:
- Flask web framework and extensions
- OCR libraries (pytesseract, pdf2image)
- PDF processing (PyMuPDF, pdfplumber, PyPDF2)
- Vector database (ChromaDB)
- Machine learning (sentence-transformers, transformers)
- Utilities and spell checking

### requirements-minimal.txt (Fallback)
Minimal dependencies for basic functionality:
- Core Flask components
- Essential OCR libraries
- Basic vector database
- Simplified embeddings

## 🔧 System Dependencies

The app requires these system-level dependencies:

### Tesseract OCR
- **Purpose:** Text extraction from images and scanned PDFs
- **Installation:**
  - Windows: Download from GitHub releases
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`

### Poppler
- **Purpose:** PDF to image conversion
- **Installation:**
  - Windows: Download and extract to C:\poppler
  - macOS: `brew install poppler`
  - Linux: `sudo apt install poppler-utils`

## 🧪 Testing Your Installation

After running any setup script:

```bash
# Start the application
python app.py

# Open browser to
http://localhost:5000




## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Python Package Installation Fails
```bash
# Try minimal requirements
pip install -r requirements-minimal.txt

# Or install packages individually
pip install flask pytesseract pdf2image chromadb
```

#### 2. Rust Compiler Error (tokenizers package)
```bash
# Use older version or skip advanced features
pip install tokenizers==0.13.3
```

#### 3. System Dependencies Not Found
- Check the installation instructions in `INSTALL.md`
- Verify PATH environment variables
- Try manual installation for your platform

#### 4. Permission Errors
```bash
# Use user installation
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 📊 Feature Availability by Installation Type

| Feature | Full Install | Minimal Install |
|---------|--------------|-----------------|
| PDF Upload & Storage | ✅ | ✅ |
| OCR Text Extraction | ✅ | ✅ |
| Basic Search | ✅ | ✅ |
| Vector Search | ✅ | ✅ |
| Spell Correction | ✅ | ✅ |
| Advanced ML Features | ✅ | ⚠️ Limited |
| Folder Organization | ✅ | ✅ |
| User Management | ✅ | ✅ |

## 🎯 Recommended Installation Path

1. **Start with:** `python quick_setup.py`
2. **If it fails:** Check error messages and install missing system dependencies
3. **If still issues:** Try `python install.py` with minimal requirements
4. **For production:** Use `python setup.py` after resolving all dependencies

## 📞 Getting Help

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Review the troubleshooting section in `INSTALL.md`
3. Verify system dependencies are properly installed
4. Try the minimal installation as a fallback

## 🔄 Updating the Installation

To update an existing installation:

```bash
# Update Python packages
pip install -r requirements.txt --upgrade

# Re-run setup if needed
python quick_setup.py
```

## ✅ Verification

After successful installation, you should be able to:
- Start the app with `python app.py`
- Access the web interface at http://localhost:5000
- Upload PDF documents
- Search through document content
- Create and organize folders
- Manage user accounts

The setup is complete when all these functions work properly!
