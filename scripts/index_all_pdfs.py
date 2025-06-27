#!/usr/bin/env python3
"""
Script to index all PDF files in the data/pdfs directory that haven't been indexed yet.
This will process all PDFs and add them to both the vector database and SQL database.
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
from core.indexer import index_pdf
from core.search import get_chroma_collection
import logging

def get_indexed_documents():
    """Get list of document IDs that are already indexed in ChromaDB."""
    try:
        collection = get_chroma_collection()
        all_data = collection.get()
        
        if not all_data or not all_data.get('metadatas'):
            return set()
        
        # Extract unique document IDs
        doc_ids = set()
        for metadata in all_data['metadatas']:
            doc_id = metadata.get('doc_id')
            if doc_id:
                doc_ids.add(doc_id)
        
        return doc_ids
    except Exception as e:
        logging.error(f"Error getting indexed documents: {e}")
        return set()

def index_all_pdfs():
    """Index all PDF files that haven't been processed yet."""
    print("🔍 Scanning for unindexed PDF files...")
    
    with app.app_context():
        try:
            # Get admin user
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
            
            # Get list of already indexed documents
            indexed_docs = get_indexed_documents()
            print(f"📊 Found {len(indexed_docs)} already indexed documents")
            
            # Find all PDF files
            pdf_pattern = os.path.join(app.config['UPLOAD_FOLDER'], "**", "*.pdf")
            pdf_files = glob.glob(pdf_pattern, recursive=True)
            print(f"📁 Found {len(pdf_files)} PDF files in directory")
            
            # Filter out already indexed files
            unindexed_files = []
            for pdf_file in pdf_files:
                doc_id = os.path.splitext(os.path.basename(pdf_file))[0]
                if doc_id not in indexed_docs:
                    unindexed_files.append(pdf_file)
            
            print(f"🆕 Found {len(unindexed_files)} unindexed PDF files")
            
            if not unindexed_files:
                print("✅ All PDF files are already indexed!")
                return True
            
            # Index each unindexed file
            success_count = 0
            failed_count = 0
            
            for i, pdf_file in enumerate(unindexed_files, 1):
                doc_id = os.path.splitext(os.path.basename(pdf_file))[0]
                print(f"\n📄 [{i}/{len(unindexed_files)}] Processing: {doc_id}")
                
                try:
                    # Index the PDF
                    result = index_pdf(pdf_file, folder_name="Uncategorized")
                    
                    if result:
                        # Create database record
                        file_size = os.path.getsize(pdf_file)
                        filename = os.path.basename(pdf_file)

                        # Get chunk count from ChromaDB
                        chunk_count = 0
                        try:
                            from core.search import get_chroma_collection
                            collection = get_chroma_collection()
                            doc_chunks = collection.get(where={"doc_id": doc_id})
                            if doc_chunks and doc_chunks.get('ids'):
                                chunk_count = len(doc_chunks['ids'])
                                print(f"   📊 Found {chunk_count} chunks for {doc_id}")
                        except Exception as e:
                            print(f"   ⚠️  Could not get chunk count for {doc_id}: {e}")

                        # Check if document already exists in SQL database
                        existing_doc = Document.query.filter_by(doc_id=doc_id, user_id=admin_user.id).first()
                        if existing_doc:
                            print(f"   📝 Document {doc_id} already exists in database, updating...")
                            existing_doc.file_path = pdf_file
                            existing_doc.file_size = file_size
                            existing_doc.chunk_count = chunk_count
                            existing_doc.upload_date = datetime.utcnow()
                        else:
                            document = Document(
                                doc_id=doc_id,
                                filename=filename,
                                original_filename=filename,
                                file_path=pdf_file,
                                file_size=file_size,
                                user_id=admin_user.id,
                                folder_id=uncategorized_folder.id
                            )
                            document.chunk_count = chunk_count
                            db.session.add(document)

                        db.session.commit()
                        success_count += 1
                        print(f"   ✅ Successfully indexed {doc_id} with {chunk_count} chunks")
                        
                    else:
                        failed_count += 1
                        print(f"   ❌ Failed to index {doc_id}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"   ❌ Error indexing {doc_id}: {e}")
                    db.session.rollback()
                    continue
            
            print(f"\n🎉 Indexing completed!")
            print(f"   ✅ Successfully indexed: {success_count} documents")
            print(f"   ❌ Failed to index: {failed_count} documents")
            print(f"   📊 Total documents now indexed: {len(indexed_docs) + success_count}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            logging.error(f"Indexing error: {e}")
            return False

if __name__ == "__main__":
    index_all_pdfs()
