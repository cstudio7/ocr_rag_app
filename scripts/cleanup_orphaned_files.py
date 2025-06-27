#!/usr/bin/env python3
"""
Script to check for and optionally clean up orphaned files in the data directory.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import Document

def cleanup_orphaned_files(dry_run=True):
    """Check for and optionally clean up orphaned files."""
    print("🔍 Checking for orphaned files...")
    
    with app.app_context():
        try:
            # Get all PDF files in the data directory
            data_dir = "./data/pdfs"
            pdf_files = []
            
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file)
                        # Extract doc_id from filename (remove .pdf extension)
                        doc_id = os.path.splitext(file)[0]
                        pdf_files.append((doc_id, full_path, file))
            
            print(f"📄 Found {len(pdf_files)} PDF files on disk")
            
            # Get all documents from database
            db_documents = Document.query.all()
            db_doc_ids = {doc.doc_id for doc in db_documents}
            
            print(f"📊 Found {len(db_doc_ids)} documents in database")
            
            # Check for orphaned files
            orphaned_files = []
            for doc_id, file_path, filename in pdf_files:
                if doc_id not in db_doc_ids:
                    orphaned_files.append((doc_id, file_path, filename))
            
            if orphaned_files:
                print(f"\n❌ Found {len(orphaned_files)} orphaned files:")
                total_size = 0
                for doc_id, file_path, filename in orphaned_files:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    size_mb = file_size / (1024 * 1024)
                    print(f"   - {filename} ({size_mb:.1f} MB)")
                    print(f"     Path: {file_path}")
                
                total_size_mb = total_size / (1024 * 1024)
                print(f"\n📊 Total size of orphaned files: {total_size_mb:.1f} MB")
                
                if dry_run:
                    print(f"\n🗑️  To clean up orphaned files, run this script with --cleanup flag")
                else:
                    print(f"\n🗑️  Cleaning up orphaned files...")
                    for doc_id, file_path, filename in orphaned_files:
                        try:
                            os.remove(file_path)
                            print(f"   ✅ Deleted: {filename}")
                        except Exception as e:
                            print(f"   ❌ Failed to delete {filename}: {e}")
                    print(f"✅ Cleanup completed!")
            else:
                print("✅ No orphaned files found!")
            
            # Check for missing files (in database but not on disk)
            missing_files = []
            for doc in db_documents:
                if not os.path.exists(doc.file_path):
                    missing_files.append(doc)
            
            if missing_files:
                print(f"\n⚠️  Found {len(missing_files)} database records with missing files:")
                for doc in missing_files:
                    print(f"   - {doc.filename} (ID: {doc.doc_id})")
                    print(f"     Expected path: {doc.file_path}")
                print(f"\n💡 Consider removing these database records or re-uploading the files")
            else:
                print("✅ All database records have corresponding files!")
                
        except Exception as e:
            print(f"❌ Error checking orphaned files: {e}")

if __name__ == "__main__":
    # Check for --cleanup flag
    cleanup = "--cleanup" in sys.argv
    
    if cleanup:
        print("⚠️  CLEANUP MODE: Will delete orphaned files!")
        response = input("Are you sure you want to proceed? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    cleanup_orphaned_files(dry_run=not cleanup)
