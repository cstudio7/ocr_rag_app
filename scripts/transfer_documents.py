#!/usr/bin/env python3
"""
Script to transfer documents from admin user to another user.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import db, Document, User, Folder
import logging

def transfer_documents(from_username, to_username):
    """Transfer all documents from one user to another."""
    print(f"🔄 Transferring documents from {from_username} to {to_username}...")
    
    with app.app_context():
        try:
            # Get users
            from_user = User.query.filter_by(username=from_username).first()
            to_user = User.query.filter_by(username=to_username).first()
            
            if not from_user:
                print(f"❌ User '{from_username}' not found")
                return False
            
            if not to_user:
                print(f"❌ User '{to_username}' not found")
                return False
            
            print(f"📊 From user: {from_user.username} (id: {from_user.id})")
            print(f"📊 To user: {to_user.username} (id: {to_user.id})")
            
            # Get documents to transfer
            documents = Document.query.filter_by(user_id=from_user.id).all()
            print(f"📄 Found {len(documents)} documents to transfer")
            
            if not documents:
                print("✅ No documents to transfer")
                return True
            
            # Get or create folders for target user
            from_folders = Folder.query.filter_by(user_id=from_user.id).all()
            folder_mapping = {}
            
            for from_folder in from_folders:
                # Check if target user already has a folder with this name
                to_folder = Folder.query.filter_by(
                    name=from_folder.name, 
                    user_id=to_user.id
                ).first()
                
                if not to_folder:
                    # Create new folder for target user
                    to_folder = Folder(
                        name=from_folder.name,
                        user_id=to_user.id,
                        description=from_folder.description,
                        color=from_folder.color
                    )
                    db.session.add(to_folder)
                    db.session.commit()
                    print(f"✅ Created folder '{from_folder.name}' for {to_user.username}")
                
                folder_mapping[from_folder.id] = to_folder.id
            
            # Transfer documents
            transferred_count = 0
            for doc in documents:
                # Update user_id
                doc.user_id = to_user.id
                
                # Update folder_id if needed
                if doc.folder_id and doc.folder_id in folder_mapping:
                    doc.folder_id = folder_mapping[doc.folder_id]
                
                transferred_count += 1
                print(f"   📝 Transferred: {doc.filename}")
            
            db.session.commit()
            print(f"🎉 Successfully transferred {transferred_count} documents")
            
            # Verify transfer
            final_count = Document.query.filter_by(user_id=to_user.id).count()
            print(f"📊 {to_user.username} now has {final_count} documents")
            
            return True
            
        except Exception as e:
            print(f"❌ Transfer failed: {e}")
            logging.error(f"Transfer error: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    # Transfer from admin to shabreen
    transfer_documents("admin", "shabreen")
