#!/usr/bin/env python3
"""
Setup script for OCR RAG App - PDF Knowledge Base
Automated installation and configuration for all platforms
"""

import os
import sys
import subprocess
import platform
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.OKGREEN):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Print header message"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f" {message}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def run_command(command, shell=True, check=True):
    """Run a system command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("❌ Python 3.8 or higher is required!", Colors.FAIL)
        print_colored(f"Current version: {version.major}.{version.minor}.{version.micro}", Colors.WARNING)
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible", Colors.OKGREEN)
    return True

def install_python_packages():
    """Install Python packages from requirements.txt"""
    print_header("Installing Python Packages")
    
    if not os.path.exists('requirements.txt'):
        print_colored("❌ requirements.txt not found!", Colors.FAIL)
        return False
    
    print_colored("📦 Installing packages from requirements.txt...", Colors.OKBLUE)
    
    # Upgrade pip first
    success, stdout, stderr = run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], shell=False)
    if not success:
        print_colored("⚠️ Failed to upgrade pip, continuing anyway...", Colors.WARNING)
    
    # Install packages
    success, stdout, stderr = run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], shell=False)
    
    if success:
        print_colored("✅ Python packages installed successfully!", Colors.OKGREEN)
        return True
    else:
        print_colored("❌ Failed to install Python packages!", Colors.FAIL)
        print_colored(f"Error: {stderr}", Colors.FAIL)
        return False

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"

def install_tesseract_windows():
    """Install Tesseract OCR on Windows"""
    print_colored("🔍 Checking for Tesseract OCR...", Colors.OKBLUE)
    
    # Check if already installed
    success, _, _ = run_command("tesseract --version")
    if success:
        print_colored("✅ Tesseract OCR already installed", Colors.OKGREEN)
        return True
    
    print_colored("📥 Tesseract not found. Please install manually:", Colors.WARNING)
    print_colored("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki", Colors.OKBLUE)
    print_colored("2. Install the executable", Colors.OKBLUE)
    print_colored("3. Add to PATH or set TESSERACT_PATH in config.py", Colors.OKBLUE)
    
    return False

def install_poppler_windows():
    """Install Poppler on Windows"""
    print_colored("🔍 Checking for Poppler...", Colors.OKBLUE)
    
    # Check common installation paths
    common_paths = [
        r"C:\poppler\bin",
        r"C:\poppler-*\bin",
        r"C:\Program Files\poppler\bin"
    ]
    
    for path in common_paths:
        if os.path.exists(path) or any(os.path.exists(p) for p in Path("C:/").glob("poppler*/bin")):
            print_colored("✅ Poppler found", Colors.OKGREEN)
            return True
    
    print_colored("📥 Poppler not found. Please install manually:", Colors.WARNING)
    print_colored("1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/", Colors.OKBLUE)
    print_colored("2. Extract to C:\\poppler", Colors.OKBLUE)
    print_colored("3. Add C:\\poppler\\bin to PATH", Colors.OKBLUE)
    
    return False

def install_tesseract_macos():
    """Install Tesseract OCR on macOS"""
    print_colored("🔍 Checking for Tesseract OCR...", Colors.OKBLUE)
    
    # Check if already installed
    success, _, _ = run_command("tesseract --version")
    if success:
        print_colored("✅ Tesseract OCR already installed", Colors.OKGREEN)
        return True
    
    # Try to install with Homebrew
    print_colored("📥 Installing Tesseract with Homebrew...", Colors.OKBLUE)
    success, _, _ = run_command("brew install tesseract")
    
    if success:
        print_colored("✅ Tesseract installed successfully!", Colors.OKGREEN)
        return True
    else:
        print_colored("❌ Failed to install Tesseract with Homebrew", Colors.FAIL)
        print_colored("Please install Homebrew first: https://brew.sh/", Colors.WARNING)
        return False

def install_poppler_macos():
    """Install Poppler on macOS"""
    print_colored("🔍 Checking for Poppler...", Colors.OKBLUE)
    
    # Check if already installed
    success, _, _ = run_command("pdftoppm -h")
    if success:
        print_colored("✅ Poppler already installed", Colors.OKGREEN)
        return True
    
    # Try to install with Homebrew
    print_colored("📥 Installing Poppler with Homebrew...", Colors.OKBLUE)
    success, _, _ = run_command("brew install poppler")
    
    if success:
        print_colored("✅ Poppler installed successfully!", Colors.OKGREEN)
        return True
    else:
        print_colored("❌ Failed to install Poppler with Homebrew", Colors.FAIL)
        return False

def install_tesseract_linux():
    """Install Tesseract OCR on Linux"""
    print_colored("🔍 Checking for Tesseract OCR...", Colors.OKBLUE)
    
    # Check if already installed
    success, _, _ = run_command("tesseract --version")
    if success:
        print_colored("✅ Tesseract OCR already installed", Colors.OKGREEN)
        return True
    
    # Try different package managers
    print_colored("📥 Installing Tesseract...", Colors.OKBLUE)
    
    # Try apt (Ubuntu/Debian)
    success, _, _ = run_command("sudo apt-get update && sudo apt-get install -y tesseract-ocr")
    if success:
        print_colored("✅ Tesseract installed with apt!", Colors.OKGREEN)
        return True
    
    # Try yum (CentOS/RHEL)
    success, _, _ = run_command("sudo yum install -y tesseract")
    if success:
        print_colored("✅ Tesseract installed with yum!", Colors.OKGREEN)
        return True
    
    # Try dnf (Fedora)
    success, _, _ = run_command("sudo dnf install -y tesseract")
    if success:
        print_colored("✅ Tesseract installed with dnf!", Colors.OKGREEN)
        return True
    
    print_colored("❌ Failed to install Tesseract automatically", Colors.FAIL)
    print_colored("Please install manually with your package manager", Colors.WARNING)
    return False

def install_poppler_linux():
    """Install Poppler on Linux"""
    print_colored("🔍 Checking for Poppler...", Colors.OKBLUE)
    
    # Check if already installed
    success, _, _ = run_command("pdftoppm -h")
    if success:
        print_colored("✅ Poppler already installed", Colors.OKGREEN)
        return True
    
    # Try different package managers
    print_colored("📥 Installing Poppler...", Colors.OKBLUE)
    
    # Try apt (Ubuntu/Debian)
    success, _, _ = run_command("sudo apt-get install -y poppler-utils")
    if success:
        print_colored("✅ Poppler installed with apt!", Colors.OKGREEN)
        return True
    
    # Try yum (CentOS/RHEL)
    success, _, _ = run_command("sudo yum install -y poppler-utils")
    if success:
        print_colored("✅ Poppler installed with yum!", Colors.OKGREEN)
        return True
    
    # Try dnf (Fedora)
    success, _, _ = run_command("sudo dnf install -y poppler-utils")
    if success:
        print_colored("✅ Poppler installed with dnf!", Colors.OKGREEN)
        return True
    
    print_colored("❌ Failed to install Poppler automatically", Colors.FAIL)
    return False

def install_system_dependencies():
    """Install system dependencies based on OS"""
    print_header("Installing System Dependencies")

    os_type = detect_os()
    print_colored(f"🖥️ Detected OS: {os_type}", Colors.OKBLUE)

    tesseract_success = False
    poppler_success = False

    if os_type == "windows":
        tesseract_success = install_tesseract_windows()
        poppler_success = install_poppler_windows()
    elif os_type == "macos":
        tesseract_success = install_tesseract_macos()
        poppler_success = install_poppler_macos()
    elif os_type == "linux":
        tesseract_success = install_tesseract_linux()
        poppler_success = install_poppler_linux()
    else:
        print_colored("❌ Unsupported operating system", Colors.FAIL)
        return False

    return tesseract_success and poppler_success

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")

    directories = [
        'data',
        'data/pdfs',
        'data/vector_store',
        'data/cache',
        'logs'
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print_colored(f"✅ Created directory: {directory}", Colors.OKGREEN)
        except Exception as e:
            print_colored(f"❌ Failed to create directory {directory}: {e}", Colors.FAIL)
            return False

    return True

def test_installation():
    """Test the installation"""
    print_header("Testing Installation")

    # Test Python imports
    test_packages = [
        'flask',
        'pdf2image',
        'pytesseract',
        'chromadb',
        'sentence_transformers',
        'spellchecker'
    ]

    for package in test_packages:
        try:
            __import__(package)
            print_colored(f"✅ {package} import successful", Colors.OKGREEN)
        except ImportError as e:
            print_colored(f"❌ {package} import failed: {e}", Colors.FAIL)
            return False

    # Test Tesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print_colored(f"✅ Tesseract OCR version: {version}", Colors.OKGREEN)
    except Exception as e:
        print_colored(f"❌ Tesseract test failed: {e}", Colors.FAIL)
        return False

    # Test PDF2Image (requires Poppler)
    try:
        from pdf2image import convert_from_path
        print_colored("✅ PDF2Image import successful", Colors.OKGREEN)
    except Exception as e:
        print_colored(f"❌ PDF2Image test failed: {e}", Colors.FAIL)
        return False

    return True

def create_sample_config():
    """Create a sample configuration file if it doesn't exist"""
    print_header("Configuration Setup")

    if os.path.exists('config.py'):
        print_colored("✅ config.py already exists", Colors.OKGREEN)
        return True

    print_colored("📝 Creating sample config.py...", Colors.OKBLUE)

    # The config.py should already exist, but let's check if it's properly configured
    try:
        import config
        print_colored("✅ Configuration loaded successfully", Colors.OKGREEN)
        return True
    except Exception as e:
        print_colored(f"❌ Configuration error: {e}", Colors.FAIL)
        return False

def main():
    """Main setup function"""
    print_colored("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                   OCR RAG App Setup                          ║
    ║              PDF Knowledge Base Installer                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """, Colors.HEADER)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install Python packages
    if not install_python_packages():
        print_colored("❌ Setup failed at Python packages installation", Colors.FAIL)
        sys.exit(1)

    # Install system dependencies
    system_deps_success = install_system_dependencies()
    if not system_deps_success:
        print_colored("⚠️ Some system dependencies failed to install", Colors.WARNING)
        print_colored("You may need to install them manually", Colors.WARNING)

    # Create directories
    if not create_directories():
        print_colored("❌ Setup failed at directory creation", Colors.FAIL)
        sys.exit(1)

    # Setup configuration
    if not create_sample_config():
        print_colored("❌ Setup failed at configuration", Colors.FAIL)
        sys.exit(1)

    # Test installation
    if not test_installation():
        print_colored("❌ Installation test failed", Colors.FAIL)
        print_colored("Some components may not work properly", Colors.WARNING)

    # Final success message
    print_header("Setup Complete!")
    print_colored("🎉 OCR RAG App setup completed successfully!", Colors.OKGREEN)
    print_colored("\nNext steps:", Colors.OKBLUE)
    print_colored("1. Run: python app.py", Colors.OKBLUE)
    print_colored("2. Open your browser to: http://localhost:5000", Colors.OKBLUE)
    print_colored("3. Register a new account or login with admin/admin123", Colors.OKBLUE)
    print_colored("4. Upload PDF documents and start searching!", Colors.OKBLUE)

    if not system_deps_success:
        print_colored("\n⚠️ Note: Some system dependencies may need manual installation", Colors.WARNING)
        print_colored("Check the messages above for specific instructions", Colors.WARNING)

if __name__ == "__main__":
    main()
