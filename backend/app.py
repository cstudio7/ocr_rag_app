"""
Main Flask application for PDF Knowledge Base.
Provides a web interface for uploading, indexing, and searching PDF documents.
"""
from flask import Flask, request, jsonify, render_template, Response, stream_with_context, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import time
import logging
import glob
from datetime import datetime

# Import configuration
from config import (
    PDF_DIR, FLASK_DEBUG, FLASK_HOST, FLASK_PORT, MAX_CONTENT_LENGTH,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE, CACHE_DIR,
    SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    PERMANENT_SESSION_LIFETIME, LOGIN_DISABLED
)

# Import core functionality
from core.indexer import index_pdf, get_chroma_collection
from core.search import query_knowledge_base, get_document_stats, get_document_list

# Import authentication components
from models import db, User, Folder, Document, init_db
from forms import LoginForm, RegistrationForm, ChangePasswordForm, ProfileForm

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = PDF_DIR
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME

# Initialize database
init_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

# Global variable to store progress updates
progress_updates = []

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Check if login is by username or email
        user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.username.data)
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()

            # Redirect to next page or home
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')

            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password.', 'error')

    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    form = ProfileForm(current_user.email)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email

    return render_template('auth/profile.html', form=form)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'error')

    return render_template('auth/change_password.html', form=form)

# Routes for UI pages
@app.route('/')
@login_required
def index():
    """Home page with navigation"""
    return render_template('index.html')

@app.route('/upload')
@login_required
def upload_page():
    """Page for uploading and indexing PDFs"""
    if not current_user.can_upload():
        flash("Access denied. Upload privileges required.", "error")
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/search')
@login_required
def search_page():
    """Page for searching indexed documents"""
    return render_template('search.html')

@app.route('/manage')
@login_required
def manage_page():
    """Legacy route - redirect to appropriate page based on role"""
    if current_user.can_manage_documents():
        return redirect(url_for('file_management'))
    else:
        # Regular users can only search
        return redirect(url_for('search_page'))

@app.route('/file_management')
@login_required
def file_management():
    """File management page - for uploaders and admins"""
    if not current_user.can_manage_documents():
        flash("Access denied. Document management privileges required.", "error")
        return redirect(url_for('index'))

    # Ensure "Uncategorized" folder exists (shared folder)
    try:
        uncategorized_folder = Folder.query.filter_by(name="Uncategorized").first()
        if not uncategorized_folder:
            # Create shared uncategorized folder
            uncategorized_folder = Folder(
                name='Uncategorized',
                user_id=current_user.id,  # Track who created it
                description='Default folder for uncategorized documents',
                color='#6b7280'
            )
            db.session.add(uncategorized_folder)
            db.session.commit()
            logging.info(f"Created shared 'Uncategorized' folder")

        # Ensure physical folder exists
        uncategorized_path = os.path.join(PDF_DIR, "Uncategorized")
        os.makedirs(uncategorized_path, exist_ok=True)

    except Exception as e:
        logging.error(f"Error creating default folder: {e}")

    return render_template('manage.html')

# API Routes
@app.route("/api/upload", methods=["POST"])
@login_required
def upload_api():
    """API endpoint for uploading and indexing PDFs"""
    # Check upload permissions
    if not current_user.can_upload():
        return jsonify({"error": "Access denied. Upload privileges required."}), 403

    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field."}), 400

    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files received."}), 400

    # Clear previous progress updates
    global progress_updates
    progress_updates = []

    # Get target folder from form data (once per upload request)
    folder_id = request.form.get('folder_id')
    target_folder = None

    if folder_id:
        target_folder = Folder.query.get(folder_id)
        if not target_folder:
            return jsonify({"error": "Selected folder not found"}), 400
    else:
        # Default to uncategorized folder
        target_folder = Folder.query.filter_by(name="Uncategorized").first()

    # If uncategorized folder doesn't exist, create it
    if not target_folder:
        target_folder = Folder(
            name='Uncategorized',
            user_id=current_user.id,
            description='Default folder for uncategorized documents',
            color='#6b7280'
        )
        db.session.add(target_folder)
        db.session.commit()

    indexed_files = []
    total_start = time.time()

    for file in files:
        filename = secure_filename(file.filename)

        # Determine save path based on target folder
        import re
        safe_folder_name = re.sub(r'[<>:"/\\|?*]', '_', target_folder.name)
        folder_path = os.path.join(PDF_DIR, safe_folder_name)
        os.makedirs(folder_path, exist_ok=True)
        save_path = os.path.join(folder_path, filename)
        folder_name = target_folder.name

        file.save(save_path)

        doc_id = os.path.splitext(filename)[0]
        progress_updates.append(f"Starting indexing: {doc_id}")
        logging.info(f"Starting indexing for {doc_id}")

        start_time = time.time()
        success = index_pdf(save_path, folder_name=folder_name)
        end_time = time.time()

        if success:
            # Save document metadata to database
            try:
                # Get file size
                file_size = os.path.getsize(save_path)

                # Get chunk count from ChromaDB
                chunk_count = 0
                try:
                    from core.search import get_chroma_collection
                    collection = get_chroma_collection()
                    doc_chunks = collection.get(where={"doc_id": doc_id})
                    if doc_chunks and doc_chunks.get('ids'):
                        chunk_count = len(doc_chunks['ids'])
                        logging.info(f"Found {chunk_count} chunks for {doc_id}")
                except Exception as e:
                    logging.warning(f"Could not get chunk count for {doc_id}: {e}")

                # Convert absolute path to relative path for portability
                relative_path = os.path.relpath(save_path, os.path.abspath("."))

                # Check if document already exists (shared documents)
                existing_doc = Document.query.filter_by(doc_id=doc_id).first()
                if existing_doc:
                    # Update existing document
                    existing_doc.filename = filename
                    existing_doc.original_filename = file.filename
                    existing_doc.file_path = relative_path
                    existing_doc.file_size = file_size
                    existing_doc.chunk_count = chunk_count
                    existing_doc.upload_date = datetime.utcnow()
                    existing_doc.folder_id = target_folder.id if target_folder else None
                else:
                    # Create new document record
                    document = Document(
                        doc_id=doc_id,
                        filename=filename,
                        original_filename=file.filename,
                        file_path=relative_path,
                        file_size=file_size,
                        user_id=current_user.id,  # Track who uploaded it
                        folder_id=target_folder.id if target_folder else None
                    )
                    document.chunk_count = chunk_count
                    db.session.add(document)

                db.session.commit()
                logging.info(f"Saved document metadata for {doc_id} with {chunk_count} chunks")
            except Exception as db_error:
                logging.error(f"Error saving document metadata: {db_error}")
                # Continue even if database save fails

            indexed_files.append(doc_id)
            progress_updates.append(f"Finished indexing: {doc_id} in {end_time - start_time:.2f} sec")
            logging.info(f"Finished indexing {doc_id} in {end_time - start_time:.2f} seconds")
        else:
            progress_updates.append(f"Failed to index: {doc_id}")
            logging.error(f"Failed to index {doc_id}")

    total_time = time.time() - total_start
    logging.info(f"Total indexing time for {len(indexed_files)} PDFs: {total_time:.2f} seconds")
    return jsonify({"message": f"Indexed {len(indexed_files)} PDF(s): {', '.join(indexed_files)}"})

@app.route('/api/progress')
def progress_stream():
    """Server-sent events endpoint for progress updates"""
    def generate():
        last_idx = 0
        while True:
            if last_idx < len(progress_updates):
                yield f"data: {progress_updates[last_idx]}\n\n"
                last_idx += 1
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# @app.route("/api/query", methods=["POST"])
# @login_required
# def query_api():
#     """API endpoint for searching indexed documents"""
#     data = request.get_json()
#     query_text = data.get("query")
#     use_original = data.get("use_original", False)

#     if not query_text:
#         return jsonify({"error": "Query text is required."}), 400

#     # If use_original is True, we need to bypass spell correction
#     if use_original:
#         # Import the search function and call it directly without spell correction
#         from core.search import query_knowledge_base_no_correction
#         results = query_knowledge_base_no_correction(query_text, top_k=10)
#     else:
#         results = query_knowledge_base(query_text, top_k=10)

#     return jsonify(results)
@app.route("/api/query", methods=["POST"])
@login_required
def query_api():
    """API endpoint for searching indexed documents"""
    data = request.get_json()
    query_text = data.get("query")
    use_original = data.get("use_original", False)

    # New: Extract pagination parameters
    page = data.get("page", 1)
    per_page = data.get("per_page", 10)

    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    if use_original:
        from core.search import query_knowledge_base_no_correction
        results = query_knowledge_base_no_correction(query_text, top_k=100, page=page, per_page=per_page)
    else:
        from core.search import query_knowledge_base
        results = query_knowledge_base(query_text, top_k=100, page=page, per_page=per_page)

    return jsonify(results)


@app.route("/api/suggestions", methods=["POST"])
@login_required
def get_suggestions():
    """API endpoint for getting search suggestions"""
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query or len(query) < 2:
        return jsonify({"suggestions": []})

    try:
        # Import the suggestions function
        from core.search import get_search_suggestions
        suggestions = get_search_suggestions(query, limit=5)
        return jsonify({"suggestions": suggestions})
    except Exception as e:
        logging.error(f"Error getting suggestions: {e}")
        return jsonify({"suggestions": []})


@app.route("/api/documents")
@login_required
def get_documents():
    """API endpoint to get paginated list of indexed documents"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))

        doc_stats = get_document_list()
        total_docs = len(doc_stats)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_docs = doc_stats[start:end]

        return jsonify({
            "documents": paginated_docs,
            "total": total_docs,
            "page": page,
            "per_page": per_page
        })
    except Exception as e:
        logging.error(f"Error getting document list: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/delete-document", methods=["POST"])
@login_required
def delete_document():
    """API endpoint to delete a document from the vector store - admin only"""
    try:
        # Check permissions
        if not current_user.can_manage_documents():
            return jsonify({"error": "Access denied. Document management privileges required."}), 403

        data = request.get_json()
        doc_id = data.get("doc_id")
        logging.info(f"=== DELETION REQUEST RECEIVED ===")
        logging.info(f"Document ID to delete: {doc_id}")
        logging.info(f"Request data: {data}")

        if not doc_id:
            logging.warning("Delete request missing document ID")
            return jsonify({"error": "Document ID is required"}), 400

        # Get the ChromaDB collection
        collection = get_chroma_collection()

        # Check if document exists in collection
        try:
            doc_check = collection.get(where={"doc_id": doc_id})
            if not doc_check or not doc_check.get('ids'):
                logging.warning(f"Document {doc_id} not found in collection")
                return jsonify({"error": f"Document {doc_id} not found in collection"}), 404

            logging.info(f"Found {len(doc_check['ids'])} chunks for document {doc_id}")
        except Exception as check_error:
            logging.error(f"Error checking document existence: {check_error}")
            return jsonify({"error": f"Error checking document: {str(check_error)}"}), 500

        # Delete document from vector store
        try:
            # Get all IDs for this document
            logging.info(f"Searching for chunks with doc_id: {doc_id}")
            doc_chunks = collection.get(where={"doc_id": doc_id})

            if doc_chunks and 'ids' in doc_chunks and doc_chunks['ids']:
                chunk_ids = doc_chunks['ids']
                logging.info(f"Found {len(chunk_ids)} chunks to delete: {chunk_ids[:5]}..." if len(chunk_ids) > 5 else f"Found chunks to delete: {chunk_ids}")

                # Delete by IDs instead of where clause
                collection.delete(ids=chunk_ids)
                logging.info(f"Successfully deleted {len(chunk_ids)} chunks for document {doc_id} from vector store")

                # Verify deletion
                verify_chunks = collection.get(where={"doc_id": doc_id})
                if verify_chunks and verify_chunks.get('ids'):
                    logging.warning(f"Warning: {len(verify_chunks['ids'])} chunks still remain after deletion!")
                else:
                    logging.info(f"Verified: All chunks for {doc_id} successfully removed from vector store")
            else:
                logging.warning(f"No chunks found for document {doc_id} in vector store")
        except Exception as delete_error:
            logging.error(f"Error deleting from vector store: {delete_error}")
            return jsonify({"error": f"Error deleting from vector store: {str(delete_error)}"}), 500

        # Get file path before deleting database record
        file_path_to_delete = None
        document = Document.query.filter_by(doc_id=doc_id).first()
        if document and document.file_path:
            # Handle both relative and absolute paths for backward compatibility
            if os.path.isabs(document.file_path):
                file_path_to_delete = document.file_path  # Absolute path (legacy)
            else:
                # Relative path - resolve to absolute
                file_path_to_delete = os.path.join(os.path.abspath("."), document.file_path)

            logging.info(f"Will delete file: {file_path_to_delete}")

        # Delete the PDF file using the path from database
        pdf_deletion_success = False
        try:
            logging.info(f"Starting PDF file deletion for {doc_id}")

            if file_path_to_delete and os.path.exists(file_path_to_delete):
                logging.info(f"Deleting primary file path: {file_path_to_delete}")
                os.remove(file_path_to_delete)
                logging.info(f"Successfully deleted PDF file: {file_path_to_delete}")
                pdf_deletion_success = True
            else:
                logging.info(f"Primary file path not found: {file_path_to_delete}")

                # Fallback: try the old path structure
                pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
                logging.info(f"Trying fallback path: {pdf_path}")
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    logging.info(f"Successfully deleted PDF file (fallback): {pdf_path}")
                    pdf_deletion_success = True
                else:
                    logging.info(f"Fallback path not found, searching subdirectories...")

                    # Try searching in subdirectories
                    search_patterns = [
                        os.path.join(PDF_DIR, "**", f"{doc_id}.pdf"),
                        os.path.join(PDF_DIR, "**", f"*{doc_id}*.pdf")
                    ]

                    for pattern in search_patterns:
                        logging.info(f"Searching with pattern: {pattern}")
                        matches = glob.glob(pattern, recursive=True)
                        if matches:
                            logging.info(f"Found {len(matches)} files: {matches}")
                            for match in matches:
                                logging.info(f"Deleting file: {match}")
                                os.remove(match)
                                logging.info(f"Successfully deleted PDF file (search): {match}")
                                pdf_deletion_success = True
                            break

                    if not pdf_deletion_success:
                        logging.warning(f"PDF file not found anywhere for: {doc_id}")

        except Exception as file_error:
            logging.error(f"Error deleting PDF file for {doc_id}: {file_error}")
            logging.error(f"Error type: {type(file_error).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            # Continue even if file deletion fails

        # Delete any cache files for this document
        cache_deletion_success = False
        try:
            logging.info(f"Starting cache file deletion for {doc_id}")
            cache_pattern = os.path.join(CACHE_DIR, f"{doc_id}_*.pkl")
            logging.info(f"Searching for cache files with pattern: {cache_pattern}")
            cache_files = glob.glob(cache_pattern)

            if cache_files:
                logging.info(f"Found {len(cache_files)} cache files to delete: {cache_files}")
                for cache_file in cache_files:
                    logging.info(f"Deleting cache file: {cache_file}")
                    os.remove(cache_file)
                    logging.info(f"Successfully deleted cache file: {cache_file}")
                    cache_deletion_success = True
            else:
                logging.info(f"No cache files found for document {doc_id}")
                cache_deletion_success = True  # No files to delete is success

        except Exception as cache_error:
            logging.error(f"Error deleting cache files for {doc_id}: {cache_error}")
            logging.error(f"Error type: {type(cache_error).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            # Continue even if cache deletion fails

        # Delete document from database
        try:
            document = Document.query.filter_by(doc_id=doc_id).first()
            if document:
                db.session.delete(document)
                db.session.commit()
                logging.info(f"Deleted document metadata from database: {doc_id}")
            else:
                logging.info(f"Document metadata not found in database: {doc_id}")
        except Exception as db_error:
            logging.error(f"Error deleting document from database: {db_error}")
            # Continue even if database deletion fails

        logging.info(f"Successfully deleted document: {doc_id}")
        return jsonify({"success": True, "message": f"Document {doc_id} deleted successfully"})

    except Exception as e:
        logging.error(f"Error deleting document: {e}")
        return jsonify({"error": str(e)}), 500


# Folder Management API Endpoints
@app.route("/api/folders", methods=["GET"])
@login_required
def get_folders():
    """API endpoint to get list of all folders"""
    try:
        # All users can see folders, but only admins can manage them
        folders = Folder.query.order_by(Folder.name).all()
        folder_data = []

        for folder in folders:
            folder_data.append({
                'id': folder.id,
                'name': folder.name,
                'description': folder.description,
                'color': folder.color,
                'document_count': folder.get_document_count(),
                'created_at': folder.created_at.isoformat(),
                'updated_at': folder.updated_at.isoformat()
            })

        return jsonify({"folders": folder_data})
    except Exception as e:
        logging.error(f"Error getting folders: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/folders", methods=["POST"])
@login_required
def create_folder():
    """API endpoint to create a new folder - admin only"""
    try:
        # Check permissions
        if not current_user.can_manage_folders():
            return jsonify({"error": "Access denied. Folder management privileges required."}), 403

        data = request.get_json()
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        color = data.get("color", "#6366f1")

        if not name:
            return jsonify({"error": "Folder name is required"}), 400

        # Sanitize folder name for filesystem
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        if not safe_name or safe_name in ['.', '..']:
            return jsonify({"error": "Invalid folder name"}), 400

        # Check if folder name already exists globally
        existing_folder = Folder.query.filter_by(name=name).first()
        if existing_folder:
            return jsonify({"error": "Folder name already exists"}), 400

        # Create physical folder
        folder_path = os.path.join(PDF_DIR, safe_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"Created physical folder: {folder_path}")
        except Exception as fs_error:
            logging.error(f"Error creating physical folder: {fs_error}")
            return jsonify({"error": "Failed to create physical folder"}), 500

        folder = Folder(
            name=name,
            user_id=current_user.id,
            description=description if description else None,
            color=color
        )

        db.session.add(folder)
        db.session.commit()

        return jsonify({
            "success": True,
            "folder": {
                'id': folder.id,
                'name': folder.name,
                'description': folder.description,
                'color': folder.color,
                'document_count': 0,
                'created_at': folder.created_at.isoformat(),
                'updated_at': folder.updated_at.isoformat()
            }
        })
    except Exception as e:
        logging.error(f"Error creating folder: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/folders/<int:folder_id>", methods=["PUT"])
@login_required
def update_folder(folder_id):
    """API endpoint to update a folder - admin only"""
    try:
        # Check permissions
        if not current_user.can_manage_folders():
            return jsonify({"error": "Access denied. Folder management privileges required."}), 403

        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        data = request.get_json()
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        color = data.get("color")

        if not name:
            return jsonify({"error": "Folder name is required"}), 400

        # Check if folder name already exists globally (excluding current folder)
        existing_folder = Folder.query.filter_by(name=name).filter(Folder.id != folder_id).first()
        if existing_folder:
            return jsonify({"error": "Folder name already exists"}), 400

        folder.name = name
        folder.description = description if description else None
        if color:
            folder.color = color

        db.session.commit()

        return jsonify({
            "success": True,
            "folder": {
                'id': folder.id,
                'name': folder.name,
                'description': folder.description,
                'color': folder.color,
                'document_count': folder.get_document_count(),
                'created_at': folder.created_at.isoformat(),
                'updated_at': folder.updated_at.isoformat()
            }
        })
    except Exception as e:
        logging.error(f"Error updating folder: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/folders/<int:folder_id>", methods=["DELETE"])
@login_required
def delete_folder(folder_id):
    """API endpoint to delete a folder - admin only"""
    try:
        # Check permissions
        if not current_user.can_manage_folders():
            return jsonify({"error": "Access denied. Folder management privileges required."}), 403

        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        # Don't allow deletion of Uncategorized folder
        if folder.name == "Uncategorized":
            return jsonify({"error": "Cannot delete the Uncategorized folder"}), 400

        # Get shared uncategorized folder for moving documents
        uncategorized_folder = Folder.query.filter_by(name="Uncategorized").first()
        if not uncategorized_folder:
            return jsonify({"error": "Uncategorized folder not found"}), 500

        # Move all documents in this folder to Uncategorized (both physically and in database)
        documents_to_move = Document.query.filter_by(folder_id=folder_id).all()

        for document in documents_to_move:
            try:
                # Move physical file
                current_path = document.file_path
                if os.path.exists(current_path):
                    uncategorized_dir = os.path.join(PDF_DIR, "Uncategorized")
                    os.makedirs(uncategorized_dir, exist_ok=True)

                    new_path = os.path.join(uncategorized_dir, document.filename)

                    # Handle filename conflicts
                    counter = 1
                    base_name, ext = os.path.splitext(document.filename)
                    while os.path.exists(new_path):
                        new_filename = f"{base_name}_{counter}{ext}"
                        new_path = os.path.join(uncategorized_dir, new_filename)
                        counter += 1

                    import shutil
                    shutil.move(current_path, new_path)

                    # Update document record
                    document.file_path = new_path
                    document.filename = os.path.basename(new_path)
                    document.folder_id = uncategorized_folder.id

                    # Update vector database metadata
                    try:
                        collection = get_chroma_collection()
                        doc_chunks = collection.get(where={"doc_id": document.doc_id})

                        if doc_chunks and 'ids' in doc_chunks and doc_chunks['ids']:
                            updated_metadatas = []
                            for metadata in doc_chunks['metadatas']:
                                updated_metadata = metadata.copy()
                                updated_metadata['folder_name'] = "Uncategorized"
                                updated_metadata['file_path'] = new_path
                                updated_metadatas.append(updated_metadata)

                            collection.update(
                                ids=doc_chunks['ids'],
                                metadatas=updated_metadatas
                            )
                    except Exception as vector_error:
                        logging.error(f"Error updating vector metadata for {document.doc_id}: {vector_error}")

                    logging.info(f"Moved document {document.filename} to Uncategorized folder")
                else:
                    # File doesn't exist, just update database
                    document.folder_id = uncategorized_folder.id

            except Exception as move_error:
                logging.error(f"Error moving document {document.filename}: {move_error}")
                # Continue with other documents

        # Try to delete the physical folder if it's empty
        try:
            import re
            safe_folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder.name)
            folder_path = os.path.join(PDF_DIR, safe_folder_name)
            if os.path.exists(folder_path):
                os.rmdir(folder_path)  # Only removes if empty
                logging.info(f"Deleted physical folder: {folder_path}")
        except OSError:
            logging.info(f"Physical folder not empty or doesn't exist: {folder.name}")
        except Exception as fs_error:
            logging.error(f"Error deleting physical folder: {fs_error}")

        # Delete folder from database
        db.session.delete(folder)
        db.session.commit()

        return jsonify({"success": True, "message": f"Folder '{folder.name}' deleted successfully"})
    except Exception as e:
        logging.error(f"Error deleting folder: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Enhanced Document Management API Endpoints
@app.route("/api/documents/enhanced", methods=["GET"])
@login_required
def get_documents_enhanced():
    """API endpoint to get enhanced document list with folder information"""
    try:
        # Get query parameters
        folder_id = request.args.get('folder_id', type=int)
        search_query = request.args.get('search', '').strip()
        date_filter = request.args.get('date_filter', '').strip()
        sort_by = request.args.get('sort_by', 'upload_date')
        sort_order = request.args.get('sort_order', 'desc')

        # Debug logging
        logging.info(f"Enhanced documents API - sort_by: {sort_by}, sort_order: {sort_order}, date_filter: {date_filter}")

        # Base query - shared documents for all users
        query = Document.query

        # Filter by folder if specified
        if folder_id:
            query = query.filter_by(folder_id=folder_id)

        # Search filter
        if search_query:
            query = query.filter(
                db.or_(
                    Document.filename.contains(search_query),
                    Document.original_filename.contains(search_query),
                    Document.doc_id.contains(search_query)
                )
            )

        # Date filter
        if date_filter:
            from datetime import datetime, timedelta
            now = datetime.utcnow()

            if date_filter == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Document.upload_date >= start_date)
            elif date_filter == 'week':
                # Start of current week (Monday)
                days_since_monday = now.weekday()
                start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Document.upload_date >= start_date)
            elif date_filter == 'month':
                # Start of current month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Document.upload_date >= start_date)

        # Sorting
        if sort_by == 'name':
            sort_column = Document.filename
        elif sort_by == 'size':
            sort_column = Document.file_size
        elif sort_by == 'upload_date':
            sort_column = Document.upload_date
        else:
            sort_column = Document.upload_date

        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        documents = query.all()

        # Format document data
        document_data = []
        for doc in documents:
            document_data.append({
                'id': doc.id,
                'doc_id': doc.doc_id,
                'filename': doc.filename,
                'original_filename': doc.original_filename,
                'file_size': doc.file_size,
                'file_size_formatted': doc.get_file_size_formatted(),
                'mime_type': doc.mime_type,
                'chunk_count': doc.chunk_count,
                'upload_date': doc.upload_date.isoformat(),
                'last_accessed': doc.last_accessed.isoformat() if doc.last_accessed else None,
                'folder_id': doc.folder_id,
                'folder_name': doc.folder.name if doc.folder else 'Uncategorized'
            })

        return jsonify({"documents": document_data})
    except Exception as e:
        logging.error(f"Error getting enhanced documents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:doc_id>/move", methods=["POST"])
@login_required
def move_document(doc_id):
    """API endpoint to move a document to a different folder"""
    try:
        # Check permissions
        if not current_user.can_manage_documents():
            return jsonify({"error": "Access denied. Document management privileges required."}), 403

        document = Document.query.get(doc_id)
        if not document:
            return jsonify({"error": "Document not found"}), 404

        data = request.get_json()
        folder_id = data.get("folder_id")

        # Get target folder info
        target_folder = None
        target_folder_name = "Uncategorized"
        if folder_id:
            target_folder = Folder.query.filter_by(id=folder_id, user_id=current_user.id).first()
            if not target_folder:
                return jsonify({"error": "Folder not found"}), 404
            target_folder_name = target_folder.name

        # Get current file path
        current_path = document.file_path
        if not os.path.exists(current_path):
            return jsonify({"error": "Document file not found on disk"}), 404

        # Determine new file path
        import re
        safe_folder_name = re.sub(r'[<>:"/\\|?*]', '_', target_folder_name)
        target_dir = os.path.join(PDF_DIR, safe_folder_name)
        os.makedirs(target_dir, exist_ok=True)

        new_path = os.path.join(target_dir, document.filename)

        # Handle file name conflicts
        counter = 1
        base_name, ext = os.path.splitext(document.filename)
        while os.path.exists(new_path) and new_path != current_path:
            new_filename = f"{base_name}_{counter}{ext}"
            new_path = os.path.join(target_dir, new_filename)
            counter += 1

        # Move the physical file
        try:
            if current_path != new_path:
                import shutil
                shutil.move(current_path, new_path)
                logging.info(f"Moved file from {current_path} to {new_path}")

                # Update filename if it was changed due to conflict
                if os.path.basename(new_path) != document.filename:
                    document.filename = os.path.basename(new_path)
        except Exception as move_error:
            logging.error(f"Error moving file: {move_error}")
            return jsonify({"error": "Failed to move file physically"}), 500

        # Update vector database metadata
        try:
            collection = get_chroma_collection()

            # Get all chunks for this document
            doc_chunks = collection.get(where={"doc_id": document.doc_id})

            if doc_chunks and 'ids' in doc_chunks and doc_chunks['ids']:
                # Update metadata for all chunks
                updated_metadatas = []
                for metadata in doc_chunks['metadatas']:
                    updated_metadata = metadata.copy()
                    updated_metadata['folder_name'] = target_folder_name
                    updated_metadata['file_path'] = new_path
                    updated_metadatas.append(updated_metadata)

                # Update the collection with new metadata
                collection.update(
                    ids=doc_chunks['ids'],
                    metadatas=updated_metadatas
                )
                logging.info(f"Updated vector database metadata for {len(doc_chunks['ids'])} chunks")
        except Exception as vector_error:
            logging.error(f"Error updating vector database metadata: {vector_error}")
            # Continue even if vector update fails

        # Update database record
        document.folder_id = folder_id
        document.file_path = new_path
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Document moved to {target_folder_name}"
        })
    except Exception as e:
        logging.error(f"Error moving document: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:doc_id>/reindex", methods=["POST"])
@login_required
def reindex_document(doc_id):
    """API endpoint to reindex a document"""
    try:
        # Check permissions
        if not current_user.can_manage_documents():
            return jsonify({"error": "Access denied. Admin privileges required."}), 403

        document = Document.query.get(doc_id)
        if not document:
            return jsonify({"error": "Document not found"}), 404

        # Check if file still exists
        if not os.path.exists(document.file_path):
            return jsonify({"error": "Document file not found on disk"}), 404

        logging.info(f"Starting reindex for document: {document.doc_id} ({document.filename})")

        # Clear cache and vector database entries for this document before reindexing
        doc_id_str = document.doc_id

        # 1. Delete cache files for this document
        try:
            import glob
            cache_pattern = os.path.join(CACHE_DIR, f"{doc_id_str}_*.pkl")
            cache_files = glob.glob(cache_pattern)
            for cache_file in cache_files:
                os.remove(cache_file)
                logging.info(f"Deleted cache file for reindex: {cache_file}")

            if cache_files:
                logging.info(f"Cleared {len(cache_files)} cache file(s) for {doc_id_str}")
            else:
                logging.info(f"No cache files found for {doc_id_str}")
        except Exception as cache_error:
            logging.warning(f"Error clearing cache for reindex: {cache_error}")
            # Continue even if cache clearing fails

        # 2. Remove existing vector database entries for this document
        try:
            collection = get_chroma_collection()
            existing_chunks = collection.get(where={"doc_id": doc_id_str})

            if existing_chunks['ids']:
                collection.delete(where={"doc_id": doc_id_str})
                logging.info(f"Removed {len(existing_chunks['ids'])} existing chunks from vector database for {doc_id_str}")
            else:
                logging.info(f"No existing chunks found in vector database for {doc_id_str}")
        except Exception as vector_error:
            logging.warning(f"Error removing existing vector entries for reindex: {vector_error}")
            # Continue even if vector cleanup fails

        # 3. Reindex the document (now it will be forced to reprocess since cache is cleared)
        from core.indexer import index_pdf
        folder_name = document.folder.name if document.folder else "Uncategorized"
        success = index_pdf(document.file_path, folder_name=folder_name)

        if success:
            # Update chunk count if needed
            from core.search import get_document_stats
            stats = get_document_stats()
            doc_stats = next((stat for stat in stats if stat[0] == document.doc_id), None)
            if doc_stats:
                old_chunk_count = document.chunk_count
                document.chunk_count = doc_stats[1]
                db.session.commit()
                logging.info(f"Updated chunk count for {document.doc_id}: {old_chunk_count} -> {document.chunk_count}")

            logging.info(f"Successfully completed reindex for document: {document.doc_id}")
            return jsonify({"success": True, "message": f"Document '{document.filename}' reindexed successfully. Cache cleared and document reprocessed."})
        else:
            logging.error(f"Failed to reindex document: {document.doc_id}")
            return jsonify({"error": "Failed to reindex document"}), 500
    except Exception as e:
        logging.error(f"Error reindexing document: {e}")
        return jsonify({"error": str(e)}), 500


# User Management Routes
@app.route("/users")
@login_required
def users():
    """User management page - admin only."""
    if not current_user.can_manage_users():
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for('index'))

    # Get user statistics for the template
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(role='admin').count(),
        'viewer_users': User.query.filter_by(role='viewer').count()
    }

    return render_template('users.html', stats=stats)


@app.route("/api/users", methods=["GET"])
@login_required
def get_users():
    """API endpoint to get all users."""
    if not current_user.can_manage_users():
        return jsonify({"error": "Access denied"}), 403

    try:
        users = User.query.all()
        user_data = []

        for user in users:
            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            })

        # Get statistics
        stats = {
            'total_users': len(users),
            'active_users': len([u for u in users if u.is_active]),
            'admin_users': len([u for u in users if u.role == 'admin']),
            'viewer_users': len([u for u in users if u.role == 'viewer'])
        }

        return jsonify({"users": user_data, "stats": stats})
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
@login_required
def create_user():
    """API endpoint to create a new user."""
    if not current_user.can_manage_users():
        return jsonify({"error": "Access denied"}), 403

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username already exists"}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already exists"}), 400

        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.role = data['role']

        db.session.add(user)
        db.session.commit()

        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    """API endpoint to get a specific user."""
    if not current_user.can_manage_users():
        return jsonify({"error": "Access denied"}), 403

    try:
        user = User.query.get_or_404(user_id)

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }

        return jsonify({"user": user_data})
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    """API endpoint to update a user."""
    if not current_user.can_manage_users():
        return jsonify({"error": "Access denied"}), 403

    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        # Check if username or email already exists (excluding current user)
        if data.get('username') and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({"error": "Username already exists"}), 400
            user.username = data['username']

        if data.get('email') and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({"error": "Email already exists"}), 400
            user.email = data['email']

        # Update other fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'role' in data:
            user.role = data['role']

        # Update password if provided
        if data.get('password'):
            user.set_password(data['password'])

        db.session.commit()

        return jsonify({"success": True, "message": "User updated successfully"})
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
def toggle_user_status(user_id):
    """API endpoint to toggle user active status."""
    if not current_user.can_manage_users():
        return jsonify({"error": "Access denied"}), 403

    try:
        user = User.query.get_or_404(user_id)

        # Prevent deactivating the last admin
        if user.role == 'admin' and user.is_active:
            active_admins = User.query.filter_by(role='admin', is_active=True).count()
            if active_admins <= 1:
                return jsonify({"error": "Cannot deactivate the last admin user"}), 400

        user.is_active = not user.is_active
        db.session.commit()

        status = "activated" if user.is_active else "deactivated"
        return jsonify({"success": True, "message": f"User {status} successfully"})
    except Exception as e:
        logging.error(f"Error toggling user status: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    """API endpoint to delete a user."""
    if not current_user.can_manage_users():
        return jsonify({"error": "Access denied"}), 403

    try:
        user = User.query.get_or_404(user_id)

        # Prevent deleting admin user
        if user.username == 'admin':
            return jsonify({"error": "Cannot delete the admin user"}), 400

        # Prevent deleting the last admin
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({"error": "Cannot delete the last admin user"}), 400

        db.session.delete(user)
        db.session.commit()

        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
