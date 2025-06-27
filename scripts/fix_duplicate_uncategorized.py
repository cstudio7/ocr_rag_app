#!/usr/bin/env python3
"""
Script to fix duplicate Uncategorized folders.
"""

import sqlite3
import os
import shutil
from pathlib import Path

def fix_duplicate_uncategorized():
    """Fix duplicate Uncategorized folders."""
    print("🔍 Checking for duplicate Uncategorized folders...")
    
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not db_path.exists():
        print("❌ Database file not found.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Find all folders with "Uncategorized" name (case insensitive)
        cursor.execute("""
            SELECT id, name, user_id, created_at 
            FROM folders 
            WHERE LOWER(name) LIKE '%uncategorized%'
            ORDER BY created_at ASC
        """)
        uncategorized_folders = cursor.fetchall()
        
        print(f"\n📊 Found {len(uncategorized_folders)} Uncategorized-like folders:")
        for folder in uncategorized_folders:
            folder_id, name, user_id, created_at = folder
            print(f"   ID: {folder_id}, Name: '{name}', User: {user_id}, Created: {created_at}")
        
        if len(uncategorized_folders) <= 1:
            print("✅ No duplicate Uncategorized folders found.")
            conn.close()
            return True
        
        # Keep the first (oldest) folder as the main one
        main_folder = uncategorized_folders[0]
        main_folder_id = main_folder[0]
        duplicate_folders = uncategorized_folders[1:]
        
        print(f"\n🎯 Keeping folder ID {main_folder_id} as the main Uncategorized folder")
        print(f"📝 Will merge {len(duplicate_folders)} duplicate folders")
        
        # Move documents from duplicate folders to main folder
        total_moved = 0
        for dup_folder in duplicate_folders:
            dup_folder_id = dup_folder[0]
            dup_folder_name = dup_folder[1]
            
            # Find documents in this duplicate folder
            cursor.execute("SELECT id, filename, doc_id FROM documents WHERE folder_id = ?", (dup_folder_id,))
            documents = cursor.fetchall()
            
            print(f"\n📄 Moving {len(documents)} documents from folder '{dup_folder_name}' (ID: {dup_folder_id})")
            
            # Update documents to point to main folder
            for doc in documents:
                doc_id, filename, doc_doc_id = doc
                cursor.execute("UPDATE documents SET folder_id = ? WHERE id = ?", (main_folder_id, doc_id))
                print(f"   ✅ Moved document: {filename}")
                total_moved += 1
        
        # Delete duplicate folders
        for dup_folder in duplicate_folders:
            dup_folder_id = dup_folder[0]
            dup_folder_name = dup_folder[1]
            
            cursor.execute("DELETE FROM folders WHERE id = ?", (dup_folder_id,))
            print(f"🗑️  Deleted duplicate folder: '{dup_folder_name}' (ID: {dup_folder_id})")
        
        # Ensure the main folder has the correct name
        cursor.execute("UPDATE folders SET name = 'Uncategorized' WHERE id = ?", (main_folder_id,))
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ Successfully fixed duplicate Uncategorized folders!")
        print(f"📊 Summary:")
        print(f"   - Kept main folder ID: {main_folder_id}")
        print(f"   - Deleted {len(duplicate_folders)} duplicate folders")
        print(f"   - Moved {total_moved} documents to main folder")
        
        # Check final state
        cursor.execute("SELECT COUNT(*) FROM folders WHERE LOWER(name) = 'uncategorized'")
        final_count = cursor.fetchone()[0]
        print(f"   - Final Uncategorized folder count: {final_count}")
        
        # Show documents in Uncategorized folder
        cursor.execute("SELECT COUNT(*) FROM documents WHERE folder_id = ?", (main_folder_id,))
        doc_count = cursor.fetchone()[0]
        print(f"   - Documents in Uncategorized folder: {doc_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_physical_folders():
    """Check for duplicate physical folders."""
    print("\n🔍 Checking physical folder structure...")
    
    pdf_dir = Path(__file__).parent.parent / "data" / "pdfs"
    
    if not pdf_dir.exists():
        print("❌ PDF directory not found.")
        return
    
    # Look for Uncategorized-like folders
    uncategorized_dirs = []
    for item in pdf_dir.iterdir():
        if item.is_dir() and 'uncategorized' in item.name.lower():
            uncategorized_dirs.append(item)
    
    print(f"📁 Found {len(uncategorized_dirs)} Uncategorized-like physical folders:")
    for folder in uncategorized_dirs:
        file_count = len(list(folder.glob("*.pdf"))) if folder.exists() else 0
        print(f"   - {folder.name} ({file_count} PDF files)")
    
    if len(uncategorized_dirs) > 1:
        print("\n⚠️  Multiple physical Uncategorized folders found!")
        print("   You may want to manually consolidate these folders.")

if __name__ == "__main__":
    print("🔧 Fixing Duplicate Uncategorized Folders")
    print("=" * 50)
    
    # Fix database duplicates
    success = fix_duplicate_uncategorized()
    
    # Check physical folders
    check_physical_folders()
    
    if success:
        print("\n🎉 Database cleanup completed!")
        print("💡 Tip: Restart your Flask application to see the changes.")
    else:
        print("\n❌ Cleanup failed. Please check the logs.")
