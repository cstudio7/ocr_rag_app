#!/usr/bin/env python3
"""
Migration script to sync documents from ChromaDB to SQL database.
This script will find all documents in the vector database and create
corresponding entries in the SQL database.
"""

import os
import sys
import glob
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from models import db, Document, User, Folder
from core.search import get_chroma_collection
import logging

def migrate_documents():
    """Migrate documents from ChromaDB to SQL database."""
    print("🔄 Starting document migration from ChromaDB to SQL database...")
    
    with app.app_context():
        try:
            # Get the ChromaDB collection
            collection = get_chroma_collection()
            
            # Get all documents from ChromaDB
            all_data = collection.get()
            
            if not all_data or not all_data.get('ids'):
                print("❌ No documents found in ChromaDB")
                return False
            
            print(f"📊 Found {len(all_data['ids'])} chunks in ChromaDB")
            
            # Group chunks by document ID
            doc_chunks = {}
            for i, chunk_id in enumerate(all_data['ids']):
                metadata = all_data['metadatas'][i]
                doc_id = metadata.get('doc_id')
                
                if doc_id not in doc_chunks:
                    doc_chunks[doc_id] = []
                doc_chunks[doc_id].append(metadata)
            
            print(f"📄 Found {len(doc_chunks)} unique documents")
            
            # Get admin user (assuming documents belong to admin)
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ Admin user not found")
                return False
            
            # Get or create Uncategorized folder
            uncategorized_folder = Folder.query.filter_by(
                name='Uncategorized', 
                user_id=admin_user.id
            ).first()
            
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
            
            migrated_count = 0
            
            # Process each document
            for doc_id, chunks in doc_chunks.items():
                # Check if document already exists in SQL database
                existing_doc = Document.query.filter_by(doc_id=doc_id).first()
                if existing_doc:
                    print(f"⏭️  Document {doc_id} already exists in database")
                    continue
                
                # Get file information from first chunk
                first_chunk = chunks[0]
                file_path = first_chunk.get('file_path')
                
                # Try to find the file in the PDF directory
                if not file_path or not os.path.exists(file_path):
                    # Search for the file in PDF directory
                    pdf_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '**', f"{doc_id}.pdf"), recursive=True)
                    if pdf_files:
                        file_path = pdf_files[0]
                    else:
                        print(f"⚠️  File not found for document {doc_id}, skipping")
                        continue
                
                # Get file information
                try:
                    file_size = os.path.getsize(file_path)
                    filename = os.path.basename(file_path)
                    
                    # Determine folder based on file path or metadata
                    folder_name = first_chunk.get('folder_name', 'Uncategorized')
                    folder = uncategorized_folder
                    
                    if folder_name != 'Uncategorized':
                        # Try to find or create the folder
                        folder = Folder.query.filter_by(
                            name=folder_name, 
                            user_id=admin_user.id
                        ).first()
                        
                        if not folder:
                            folder = Folder(
                                name=folder_name,
                                user_id=admin_user.id,
                                description=f'Auto-created folder for {folder_name}',
                                color='#6366f1'
                            )
                            db.session.add(folder)
                            db.session.commit()
                            print(f"✅ Created folder: {folder_name}")
                    
                    # Create document record
                    document = Document(
                        doc_id=doc_id,
                        filename=filename,
                        original_filename=filename,
                        file_path=file_path,
                        file_size=file_size,
                        user_id=admin_user.id,
                        folder_id=folder.id
                    )

                    # Set chunk count after creation
                    document.chunk_count = len(chunks)

                    db.session.add(document)
                    db.session.commit()
                    
                    migrated_count += 1
                    print(f"✅ Migrated document: {doc_id} ({len(chunks)} chunks)")
                    
                except Exception as e:
                    print(f"❌ Error migrating document {doc_id}: {e}")
                    db.session.rollback()
                    continue
            
            print(f"🎉 Migration completed! Migrated {migrated_count} documents")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            logging.error(f"Migration error: {e}")
            return False

if __name__ == "__main__":
    migrate_documents()
