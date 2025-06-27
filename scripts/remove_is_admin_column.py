#!/usr/bin/env python3
"""
Script to remove is_admin column from users table.
"""

import sqlite3
import shutil
from pathlib import Path

def remove_is_admin_column():
    """Remove is_admin column from users table."""
    print("🔄 Removing is_admin column from users table...")
    
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    backup_path = db_path.with_suffix('.backup')
    
    if not db_path.exists():
        print("❌ Database file not found.")
        return False
    
    try:
        # Create backup
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        print("🔄 Recreating users table without is_admin column...")
        
        # Create new table without is_admin column
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                role VARCHAR(20) NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                last_login DATETIME
            )
        """)
        
        # Copy data from old table to new table (excluding is_admin)
        cursor.execute("""
            INSERT INTO users_new (
                id, username, email, password_hash, first_name, last_name, 
                role, is_active, created_at, last_login
            )
            SELECT 
                id, username, email, password_hash, first_name, last_name,
                role, is_active, created_at, last_login
            FROM users
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE users")
        
        # Rename new table
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # Recreate indexes
        cursor.execute("CREATE UNIQUE INDEX ix_users_username ON users (username)")
        cursor.execute("CREATE UNIQUE INDEX ix_users_email ON users (email)")
        
        # Commit changes
        conn.commit()
        
        print("✅ Successfully removed is_admin column")
        
        # Verify the new schema
        print("\n📊 New users table schema:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for column in columns:
            cid, name, type_, notnull, default_value, pk = column
            print(f"   {name}: {type_} (nullable: {not notnull}, default: {default_value})")
        
        # Check users
        cursor.execute("SELECT username, email, role, is_active FROM users")
        users = cursor.fetchall()
        
        print("\n📊 Current Users:")
        for user in users:
            username, email, role, is_active = user
            status = "Active" if is_active else "Inactive"
            role_icon = "🔑" if role == "admin" else "📤" if role == "uploader" else "👀"
            print(f"   {role_icon} {username} ({email}) - Role: {role} - Status: {status}")
        
        conn.close()
        print("\n✅ Database migration completed successfully!")
        print(f"💾 Backup saved as: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        
        # Restore backup if something went wrong
        if backup_path.exists():
            shutil.copy2(backup_path, db_path)
            print("🔄 Restored database from backup")
        
        return False

if __name__ == "__main__":
    remove_is_admin_column()
