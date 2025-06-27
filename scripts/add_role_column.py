#!/usr/bin/env python3
"""
Script to add role column to users table.
"""

import sqlite3
import os
from pathlib import Path

def add_role_column():
    """Add role column to users table."""
    print("🔄 Adding role column to users table...")
    
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not db_path.exists():
        print("❌ Database file not found. Please run the app first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if role column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' in columns:
            print("✅ Role column already exists")
        else:
            # Add role column
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'viewer'")
            print("✅ Added role column to users table")
        
        # Update existing users
        print("🔄 Updating existing users...")
        
        # Set admin role for admin user
        cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
        admin_updated = cursor.rowcount
        
        # Set viewer role for all other users who don't have a role
        cursor.execute("UPDATE users SET role = 'viewer' WHERE role IS NULL OR role = ''")
        viewer_updated = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Updated {admin_updated} admin users")
        print(f"✅ Updated {viewer_updated} users to viewer role")
        
        # Show current users
        cursor.execute("SELECT username, email, role, is_active FROM users")
        users = cursor.fetchall()
        
        print("\n📊 Current Users:")
        for user in users:
            username, email, role, is_active = user
            status = "Active" if is_active else "Inactive"
            print(f"   - {username} ({email}) - Role: {role} - Status: {status}")
        
        conn.close()
        print("\n✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    add_role_column()
