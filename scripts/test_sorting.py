#!/usr/bin/env python3
"""
Script to test the sorting functionality directly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import db, Document

def test_sorting():
    """Test the sorting functionality."""
    print("🔍 Testing document sorting...")
    
    with app.app_context():
        try:
            # Test size sorting - largest first
            print("\n📊 Testing size sorting (largest first):")
            docs_desc = Document.query.order_by(Document.file_size.desc()).limit(5).all()
            for doc in docs_desc:
                size_mb = doc.file_size / (1024 * 1024) if doc.file_size else 0
                print(f"   {doc.filename}: {size_mb:.1f} MB")
            
            # Test size sorting - smallest first
            print("\n📊 Testing size sorting (smallest first):")
            docs_asc = Document.query.order_by(Document.file_size.asc()).limit(5).all()
            for doc in docs_asc:
                size_mb = doc.file_size / (1024 * 1024) if doc.file_size else 0
                print(f"   {doc.filename}: {size_mb:.1f} MB")
            
            # Test name sorting
            print("\n📊 Testing name sorting (A-Z):")
            docs_name_asc = Document.query.order_by(Document.filename.asc()).limit(5).all()
            for doc in docs_name_asc:
                print(f"   {doc.filename}")
            
            # Test date sorting
            print("\n📊 Testing date sorting (newest first):")
            docs_date_desc = Document.query.order_by(Document.upload_date.desc()).limit(5).all()
            for doc in docs_date_desc:
                print(f"   {doc.filename}: {doc.upload_date}")
            
            print("\n✅ Sorting tests completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

if __name__ == "__main__":
    test_sorting()
