#!/usr/bin/env python3
"""
Simple installation script for OCR RAG App
Quick setup for users who want to get started fast
"""

import os
import sys
import subprocess
import platform

def print_step(step, message):
    """Print installation step"""
    print(f"\n[{step}] {message}")
    print("-" * 50)

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except Exception as e:
        return False, str(e)

def check_python():
    """Check Python version"""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Install Python requirements"""
    print_step(2, "Installing Python Packages")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found!")
        return False
    
    print("Installing packages...")
    success, output = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    
    if success:
        print("✅ Python packages installed")
        return True
    else:
        print(f"❌ Installation failed: {output}")
        return False

def create_directories():
    """Create necessary directories"""
    print_step(3, "Creating Directories")
    
    dirs = ['data', 'data/pdfs', 'data/vector_store', 'data/cache', 'logs']
    
    for directory in dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
            return False
    
    return True

def check_system_deps():
    """Check system dependencies"""
    print_step(4, "Checking System Dependencies")
    
    # Check Tesseract
    success, _ = run_command("tesseract --version")
    if success:
        print("✅ Tesseract OCR found")
    else:
        print("⚠️ Tesseract OCR not found")
        print_install_instructions()
    
    # Check Poppler (via pdf2image test)
    try:
        from pdf2image import convert_from_path
        print("✅ Poppler found (pdf2image works)")
        poppler_ok = True
    except Exception:
        print("⚠️ Poppler not found")
        poppler_ok = False
        print_install_instructions()
    
    return success and poppler_ok

def print_install_instructions():
    """Print manual installation instructions"""
    system = platform.system().lower()
    
    print("\n📋 Manual Installation Instructions:")
    
    if system == "windows":
        print("Windows:")
        print("  • Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  • Poppler: https://github.com/oschwartz10612/poppler-windows/releases/")
    elif system == "darwin":
        print("macOS:")
        print("  • brew install tesseract poppler")
    elif system == "linux":
        print("Linux:")
        print("  • sudo apt install tesseract-ocr poppler-utils  # Ubuntu/Debian")
        print("  • sudo yum install tesseract poppler-utils      # CentOS/RHEL")

def test_imports():
    """Test critical imports"""
    print_step(5, "Testing Installation")
    
    critical_packages = [
        'flask',
        'pytesseract', 
        'pdf2image',
        'chromadb',
        'sentence_transformers'
    ]
    
    all_good = True
    for package in critical_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            all_good = False
    
    return all_good

def main():
    """Main installation function"""
    print("🚀 OCR RAG App - Quick Installation")
    print("=" * 50)
    
    # Check Python
    if not check_python():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed at requirements step")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Installation failed at directory creation")
        sys.exit(1)
    
    # Check system dependencies
    system_ok = check_system_deps()
    
    # Test imports
    imports_ok = test_imports()
    
    # Final status
    print("\n" + "=" * 50)
    if imports_ok and system_ok:
        print("🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. python app.py")
        print("2. Open http://localhost:5000")
        print("3. Login with admin/admin123")
    elif imports_ok:
        print("⚠️ Installation mostly successful!")
        print("Some system dependencies may need manual installation.")
        print("The app should still work for most PDFs.")
        print("\nTo start: python app.py")
    else:
        print("❌ Installation failed!")
        print("Please check the errors above and try again.")

if __name__ == "__main__":
    main()
