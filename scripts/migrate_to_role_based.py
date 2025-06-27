#!/usr/bin/env python3
"""
Migration script to convert from user-specific to role-based shared system.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import db, Document, User, Folder
import logging

def migrate_to_role_based():
    """Migrate the system to role-based with shared documents."""
    print("🔄 Migrating to role-based system with shared documents...")
    
    with app.app_context():
        try:
            # Step 1: Add role column if it doesn't exist
            print("📊 Checking database schema...")
            
            # Check if role column exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'role' not in columns:
                print("➕ Adding role column to users table...")
                db.engine.execute('ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT "viewer"')
                db.session.commit()
            
            # Step 2: Update existing users with roles
            print("👥 Updating user roles...")
            users = User.query.all()
            
            for user in users:
                if user.username == 'admin':
                    user.role = 'admin'
                    print(f"   ✅ Set {user.username} as admin")
                elif hasattr(user, 'is_admin') and user.is_admin:
                    user.role = 'admin'
                    print(f"   ✅ Set {user.username} as admin")
                else:
                    # Set default role based on username or make them uploaders
                    if 'admin' in user.username.lower():
                        user.role = 'admin'
                    elif any(keyword in user.username.lower() for keyword in ['upload', 'editor', 'manager']):
                        user.role = 'uploader'
                    else:
                        user.role = 'viewer'  # Default for regular users
                    print(f"   ✅ Set {user.username} as {user.role}")
            
            db.session.commit()
            
            # Step 3: Create shared folders if needed
            print("📁 Setting up shared folder structure...")
            
            # Check if we have an admin user
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                print("❌ No admin user found. Creating default admin...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    first_name='System',
                    last_name='Administrator'
                )
                admin_user.role = 'admin'
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Created default admin user")
            
            # Ensure there's an Uncategorized folder
            uncategorized_folder = Folder.query.filter_by(name='Uncategorized').first()
            if not uncategorized_folder:
                uncategorized_folder = Folder(
                    name='Uncategorized',
                    user_id=admin_user.id,
                    description='Default folder for uncategorized documents',
                    color='#6b7280'
                )
                db.session.add(uncategorized_folder)
                db.session.commit()
                print("✅ Created Uncategorized folder")
            
            # Step 4: Update document ownership (optional - documents are now shared)
            print("📄 Updating document access...")
            documents = Document.query.all()
            print(f"   📊 Found {len(documents)} documents - now accessible to all users")
            
            # Step 5: Summary
            print("\n🎉 Migration completed successfully!")
            print("\n📊 System Summary:")
            
            # User statistics
            total_users = User.query.count()
            admin_users = User.query.filter_by(role='admin').count()
            uploader_users = User.query.filter_by(role='uploader').count()
            viewer_users = User.query.filter_by(role='viewer').count()
            
            print(f"   👥 Total Users: {total_users}")
            print(f"   🔑 Administrators: {admin_users}")
            print(f"   📤 Uploaders: {uploader_users}")
            print(f"   👀 Viewers: {viewer_users}")
            
            # Document statistics
            total_docs = Document.query.count()
            total_folders = Folder.query.count()
            
            print(f"   📄 Total Documents: {total_docs} (shared across all users)")
            print(f"   📁 Total Folders: {total_folders}")
            
            print("\n🔐 Role Permissions:")
            print("   👀 Viewer: Can search and view documents")
            print("   📤 Uploader: Can search, view, and upload documents")
            print("   🔑 Admin: Full access (upload, manage users, manage documents, manage folders)")
            
            print("\n✅ Migration complete! Users can now login and access shared documents based on their roles.")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            logging.error(f"Migration error: {e}")
            db.session.rollback()
            return False

def show_current_users():
    """Show current users and their roles."""
    print("\n👥 Current Users:")
    with app.app_context():
        users = User.query.all()
        for user in users:
            role = getattr(user, 'role', 'unknown')
            status = "Active" if user.is_active else "Inactive"
            print(f"   - {user.username} ({user.email}) - Role: {role} - Status: {status}")

if __name__ == "__main__":
    print("🚀 Role-Based System Migration")
    print("=" * 50)
    
    # Show current state
    show_current_users()
    
    # Ask for confirmation
    response = input("\n❓ Do you want to proceed with the migration? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        success = migrate_to_role_based()
        if success:
            print("\n🎉 Migration completed successfully!")
            show_current_users()
        else:
            print("\n❌ Migration failed. Please check the logs.")
    else:
        print("❌ Migration cancelled.")
