#!/usr/bin/env python3
"""
Script to check database schema.
"""

import sqlite3
from pathlib import Path

def check_schema():
    """Check the current database schema."""
    print("🔍 Checking database schema...")
    
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not db_path.exists():
        print("❌ Database file not found.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check users table schema
        print("\n📊 Users table schema:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for column in columns:
            cid, name, type_, notnull, default_value, pk = column
            print(f"   {name}: {type_} (nullable: {not notnull}, default: {default_value}, pk: {bool(pk)})")
        
        # Check if is_admin column exists
        column_names = [col[1] for col in columns]
        if 'is_admin' in column_names:
            print("\n⚠️  WARNING: is_admin column still exists!")
            print("   This might be causing conflicts with the role-based system.")
        else:
            print("\n✅ No is_admin column found - good!")
        
        if 'role' in column_names:
            print("✅ Role column exists")
        else:
            print("❌ Role column missing!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Check failed: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    check_schema()
