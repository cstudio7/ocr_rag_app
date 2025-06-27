#!/usr/bin/env python3
"""
Script to check file sizes in the database.
"""

import sqlite3
from pathlib import Path

def check_file_sizes():
    """Check file sizes in the database."""
    print("🔍 Checking file sizes in database...")
    
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not db_path.exists():
        print("❌ Database file not found.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check documents table schema
        print("\n📊 Documents table schema:")
        cursor.execute("PRAGMA table_info(documents)")
        columns = cursor.fetchall()
        
        for column in columns:
            cid, name, type_, notnull, default_value, pk = column
            if name in ['filename', 'file_size', 'upload_date']:
                print(f"   {name}: {type_} (nullable: {not notnull}, default: {default_value})")
        
        # Check file sizes
        print("\n📄 Document file sizes:")
        cursor.execute("""
            SELECT filename, file_size, upload_date 
            FROM documents 
            ORDER BY file_size DESC 
            LIMIT 10
        """)
        documents = cursor.fetchall()
        
        if not documents:
            print("   No documents found in database")
        else:
            print("   Top 10 largest files:")
            for doc in documents:
                filename, file_size, upload_date = doc
                if file_size:
                    # Format file size
                    if file_size >= 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    elif file_size >= 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    else:
                        size_str = f"{file_size} bytes"
                else:
                    size_str = "Unknown"
                
                print(f"   - {filename}: {size_str} (raw: {file_size})")
        
        # Check for NULL file sizes
        cursor.execute("SELECT COUNT(*) FROM documents WHERE file_size IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"\n📊 Documents with NULL file_size: {null_count}")
        
        # Check for zero file sizes
        cursor.execute("SELECT COUNT(*) FROM documents WHERE file_size = 0")
        zero_count = cursor.fetchone()[0]
        print(f"📊 Documents with zero file_size: {zero_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Check failed: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    check_file_sizes()
