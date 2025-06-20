"""
Main Flask application for PDF Knowledge Base.
Provides a web interface for uploading, indexing, and searching PDF documents.
"""
import os
# Set environment variable to avoid tokenizers parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from flask import Flask, request, jsonify, render_template, Response, stream_with_context, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import time
import logging
import glob
from flask_cors import CORS
import json
import datetime
import uuid
from functools import wraps

# Import configuration
from config import (
    PDF_DIR, FLASK_DEBUG, MAX_CONTENT_LENGTH,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE, CACHE_DIR,
    SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    PERMANENT_SESSION_LIFETIME, LOGIN_DISABLED
)

# Import os for path operations
import os
from config import DATABASE_URL

# Import core functionality
from core.indexer import index_pdf, get_chroma_collection
from core.search import query_knowledge_base, get_document_stats, get_document_list

# Import authentication components
from models import db, User, init_db
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
# Add CORS support with more detailed configuration
CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Add your frontend URL
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
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

# Role-based access control decorator
def role_required(roles):
    """
    Decorator for views that require specific roles.
    Usage: @role_required(['admin', 'editor'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            
            # Admin has access to everything
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Check if user has any of the required roles
            if isinstance(roles, list) and current_user.role in roles:
                return f(*args, **kwargs)
            elif isinstance(roles, str) and current_user.role == roles:
                return f(*args, **kwargs)
            
            return jsonify({"error": "You don't have permission to access this resource"}), 403
        return decorated_function
    return decorator

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

# Serve React app for all non-API routes
REACT_BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'react')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Serve React app"""
    if path != "" and os.path.exists(os.path.join(REACT_BUILD_DIR, path)):
        return send_from_directory(REACT_BUILD_DIR, path)
    else:
        return send_from_directory(REACT_BUILD_DIR, 'index.html')

# API Routes
@app.route("/api/upload", methods=["POST"])
@login_required
@role_required(['admin', 'editor'])
def upload_api():
    """API endpoint for uploading and indexing PDFs"""
    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field."}), 400

    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files received."}), 400

    # Clear previous progress updates
    global progress_updates
    progress_updates = []

    indexed_files = []
    total_start = time.time()

    for file in files:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        doc_id = os.path.splitext(filename)[0]
        progress_updates.append(f"Starting indexing: {doc_id}")
        logging.info(f"Starting indexing for {doc_id}")

        start_time = time.time()
        index_pdf(save_path)
        end_time = time.time()

        indexed_files.append(doc_id)
        progress_updates.append(f"Finished indexing: {doc_id} in {end_time - start_time:.2f} sec")
        logging.info(f"Finished indexing {doc_id} in {end_time - start_time:.2f} seconds")

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

@app.route("/api/query", methods=["POST"])
@login_required
def query_api():
    """API endpoint for searching indexed documents"""
    data = request.get_json()
    
    # Debug the incoming data
    print("Received data:", data)
    
    # Check if data is a dictionary and has a 'query' key
    if not isinstance(data, dict) or 'query' not in data:
        return jsonify({"error": "Invalid request format. Expected JSON with 'query' field."}), 400
    
    query_text = data.get("query")
    use_original = data.get("use_original", False)
    
    # Make sure query_text is a string
    if not isinstance(query_text, str):
        return jsonify({"error": "Query text must be a string."}), 400

    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    # If use_original is True, we need to bypass spell correction
    if use_original:
        # Import the search function and call it directly without spell correction
        from core.search import query_knowledge_base_no_correction
        results = query_knowledge_base_no_correction(query_text, top_k=10)
    else:
        # Remove the include_keywords parameter since it's not supported
        results = query_knowledge_base(query_text, top_k=10)

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
    """API endpoint to get list of indexed documents"""
    try:
        doc_stats = get_document_list()
        return jsonify({"documents": doc_stats})
    except Exception as e:
        logging.error(f"Error getting document list: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/delete-document", methods=["POST"])
@login_required
def delete_document():
    """API endpoint to delete a document from the vector store"""
    try:
        data = request.get_json()
        doc_id = data.get("doc_id")

        logging.info(f"Attempting to delete document: {doc_id}")

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
            doc_chunks = collection.get(where={"doc_id": doc_id})
            if doc_chunks and 'ids' in doc_chunks and doc_chunks['ids']:
                # Delete by IDs instead of where clause
                collection.delete(ids=doc_chunks['ids'])
                logging.info(f"Deleted {len(doc_chunks['ids'])} chunks for document {doc_id} from vector store")
            else:
                logging.warning(f"No chunks found for document {doc_id}")
        except Exception as delete_error:
            logging.error(f"Error deleting from vector store: {delete_error}")
            return jsonify({"error": f"Error deleting from vector store: {str(delete_error)}"}), 500

        # Also delete the PDF file if it exists
        try:
            pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                logging.info(f"Deleted PDF file: {pdf_path}")
            else:
                logging.info(f"PDF file not found: {pdf_path}")
        except Exception as file_error:
            logging.error(f"Error deleting PDF file: {file_error}")
            # Continue even if file deletion fails

        # Delete any cache files for this document
        try:
            cache_pattern = os.path.join(CACHE_DIR, f"{doc_id}_*.pkl")
            cache_files = glob.glob(cache_pattern)
            for cache_file in cache_files:
                os.remove(cache_file)
                logging.info(f"Deleted cache file: {cache_file}")

            if not cache_files:
                logging.info(f"No cache files found for document {doc_id}")
        except Exception as cache_error:
            logging.error(f"Error deleting cache files: {cache_error}")
            # Continue even if cache deletion fails

        logging.info(f"Successfully deleted document: {doc_id}")
        return jsonify({"success": True, "message": f"Document {doc_id} deleted successfully"})

    except Exception as e:
        logging.error(f"Error deleting document: {e}")
        return jsonify({"error": str(e)}), 500

# API Authentication Routes
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if login is by username or email
    user = User.query.filter(
        (User.username == username) |
        (User.email == username)
    ).first()
    
    if user and user.check_password(password):
        login_user(user)
        user.update_last_login()
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }), 200
    else:
        return jsonify({"error": "Invalid username/email or password"}), 401

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint for user logout"""
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """API endpoint for user registration"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == data.get('username')) |
        (User.email == data.get('email'))
    ).first()
    
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 400
    
    # Create new user
    try:
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "Registration successful"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """API endpoint to check authentication status"""
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "role": current_user.role,
                "is_admin": current_user.is_admin
            }
        }), 200
    else:
        return jsonify({
            "authenticated": False,
            "user": None
        }), 200

@app.route('/api/documents', methods=['GET'])
@login_required
def api_get_documents():
    """API endpoint to get list of documents"""
    try:
        documents = get_document_list()
        return jsonify({"documents": documents}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/stats', methods=['GET'])
@login_required
def api_get_document_stats():
    """API endpoint to get document statistics"""
    try:
        stats = get_document_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API endpoint for searching documents"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data.get('query')
    limit = data.get('limit', 10)
    
    try:
        results = query_knowledge_base(query, limit)
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """API endpoint for uploading PDFs"""
    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field"}), 400
    
    files = request.files.getlist('pdfs')
    if not files:
        return jsonify({"error": "No files received"}), 400
    
    # Clear previous progress updates
    global progress_updates
    progress_updates = []
    
    indexed_files = []
    total_start = time.time()
    
    for file in files:
        if file.filename == '':
            continue
        
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            # Index the PDF
            try:
                index_pdf(filepath, progress_callback=update_progress)
                indexed_files.append(filename)
            except Exception as e:
                logging.error(f"Error indexing {filename}: {e}")
                return jsonify({"error": f"Error indexing {filename}: {str(e)}"}), 500
    
    total_time = time.time() - total_start
    
    return jsonify({
        "message": f"Successfully indexed {len(indexed_files)} files in {total_time:.2f} seconds",
        "indexed_files": indexed_files
    }), 200

# Add a simple test endpoint
@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint to verify API is working"""
    return jsonify({"message": "API is working!"}), 200

# API Routes for document management
@app.route("/api/documents", methods=["GET"])
def get_documents_api():
    """API endpoint to get all documents with folder information from ChromaDB"""
    try:
        # Get folder filter if any
        folder_id = request.args.get('folder')
        
        # Get the ChromaDB collection
        collection = get_chroma_collection()
        
        # Get all documents from ChromaDB
        all_data = collection.get()
        
        if not all_data or not all_data['ids']:
            logging.warning("No documents found in ChromaDB")
            return jsonify({"documents": [], "doc_count": 0, "chunk_count": 0})
        
        # Group by document ID and collect metadata
        documents = {}
        for i, meta in enumerate(all_data['metadatas']):
            doc_id = meta.get('doc_id')
            if not doc_id:
                continue
                
            # Get folder from metadata or from documents.json
            folder = meta.get('folder', 'uncategorized')
            
            # Skip if filtering by folder and document is not in that folder
            if folder_id and folder_id != "all" and folder != folder_id:
                continue
                
            if doc_id not in documents:
                # Get file size if available
                pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
                file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
                
                documents[doc_id] = {
                    "doc_id": doc_id,
                    "chunk_count": 1,
                    "size": file_size,
                    "upload_date": meta.get('upload_date', datetime.datetime.now().isoformat()),
                    "updated_date": meta.get('updated_at', meta.get('upload_date', datetime.datetime.now().isoformat())),
                    "folder": folder
                }
            else:
                documents[doc_id]["chunk_count"] += 1
        
        # Convert to list for JSON serialization
        doc_list = list(documents.values())
        
        # Get document counts per folder
        folder_counts = {}
        for doc in doc_list:
            folder = doc.get('folder', 'uncategorized')
            if folder in folder_counts:
                folder_counts[folder] += 1
            else:
                folder_counts[folder] = 1
        
        # Log some debug information
        logging.info(f"Returning {len(doc_list)} documents")
        if len(doc_list) > 0:
            logging.info(f"Sample document: {doc_list[0]}")
            logging.info(f"Folder counts: {folder_counts}")
        
        return jsonify({
            "documents": doc_list,
            "doc_count": len(doc_list),
            "chunk_count": len(all_data['ids']),
            "folder_counts": folder_counts
        })
    except Exception as e:
        logging.error(f"Error getting documents: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/delete-document", methods=["POST"])
def delete_document_api():
    """API endpoint to delete a document"""
    try:
        data = request.json
        if not data or "doc_id" not in data:
            return jsonify({"error": "Missing doc_id parameter"}), 400
        
        doc_id = data["doc_id"]
        
        # Get the ChromaDB collection
        collection = get_chroma_collection()
        
        # Delete document from ChromaDB
        collection.delete(where={"doc_id": doc_id})
        
        # Delete PDF file if it exists
        pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        # Delete cache files
        cache_pattern = os.path.join(CACHE_DIR, f"{doc_id}_*.pkl")
        for cache_file in glob.glob(cache_pattern):
            os.remove(cache_file)
        
        return jsonify({"success": True, "message": f"Document {doc_id} deleted successfully"})
    except Exception as e:
        logging.error(f"Error deleting document: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/download-document/<doc_id>", methods=["GET"])
def download_document_api(doc_id):
    """API endpoint to download a document"""
    try:
        # Check if document exists
        pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
        if not os.path.exists(pdf_path):
            return jsonify({"error": f"Document {doc_id} not found"}), 404
        
        # Return the PDF file
        return send_from_directory(
            directory=PDF_DIR,
            path=f"{doc_id}.pdf",
            as_attachment=True,
            download_name=f"{doc_id}.pdf"
        )
    except Exception as e:
        logging.error(f"Error downloading document: {e}")
        return jsonify({"error": str(e)}), 500

# Folder management API endpoints
@app.route("/api/folders", methods=["GET"])
def get_folders_api():
    """API endpoint to get all folders with document counts from ChromaDB"""
    try:
        # Load folders
        folders_file = os.path.join(CACHE_DIR, "folders.json")
        if os.path.exists(folders_file):
            with open(folders_file, 'r') as f:
                folders_data = json.load(f)
                folders = folders_data.get("folders", [])
        else:
            folders = []
            
        # Get the ChromaDB collection
        collection = get_chroma_collection()
        
        # Get all documents from ChromaDB
        all_data = collection.get()
        
        # Count documents per folder
        folder_counts = {}
        if all_data and all_data['metadatas']:
            # Get unique document IDs per folder
            doc_folders = {}
            for meta in all_data['metadatas']:
                doc_id = meta.get('doc_id')
                folder = meta.get('folder', 'uncategorized')
                if doc_id:
                    doc_folders[doc_id] = folder
            
            # Count documents per folder
            for folder in doc_folders.values():
                if folder in folder_counts:
                    folder_counts[folder] += 1
                else:
                    folder_counts[folder] = 1
        
        # Add counts to folder objects
        for folder in folders:
            folder_id = folder.get("id")
            folder["document_count"] = folder_counts.get(folder_id, 0)
        
        return jsonify({"folders": folders, "folder_counts": folder_counts})
    except Exception as e:
        logging.error(f"Error getting folders: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/folders", methods=["POST"])
@login_required
@role_required(['admin', 'editor'])
def create_folder():
    """API endpoint to create a new folder"""
    try:
        data = request.json
        if not data or "name" not in data:
            return jsonify({"error": "Missing folder name"}), 400
        
        folder_name = data["name"].strip()
        if not folder_name:
            return jsonify({"error": "Folder name cannot be empty"}), 400
        
        # Create folders directory if it doesn't exist
        folders_file = os.path.join(CACHE_DIR, "folders.json")
        
        # Read existing folders
        if os.path.exists(folders_file):
            with open(folders_file, 'r') as f:
                data = json.load(f)
                folders = data.get("folders", [])
        else:
            folders = []
        
        # Check if folder with same name already exists
        if any(folder["name"].lower() == folder_name.lower() for folder in folders):
            return jsonify({"error": f"Folder '{folder_name}' already exists"}), 400
        
        # Create new folder
        new_folder = {
            "id": str(uuid.uuid4()),
            "name": folder_name,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        folders.append(new_folder)
        
        # Save folders to file
        with open(folders_file, 'w') as f:
            json.dump({"folders": folders}, f)
        
        # Create physical folder if needed
        folder_path = os.path.join(PDF_DIR, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        return jsonify({"folder": new_folder}), 201
    except Exception as e:
        logging.error(f"Error creating folder: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/folders/<folder_id>", methods=["PUT"])
@login_required
@role_required(['admin', 'editor'])
def update_folder(folder_id):
    """API endpoint to update a folder"""
    try:
        data = request.json
        if not data or "name" not in data:
            return jsonify({"error": "Missing folder name"}), 400
        
        folder_name = data["name"].strip()
        if not folder_name:
            return jsonify({"error": "Folder name cannot be empty"}), 400
        
        # Read existing folders
        folders_file = os.path.join(CACHE_DIR, "folders.json")
        if not os.path.exists(folders_file):
            return jsonify({"error": "Folder not found"}), 404
        
        with open(folders_file, 'r') as f:
            data = json.load(f)
            folders = data.get("folders", [])
        
        # Find folder to update
        folder_index = None
        old_folder_name = None
        for i, folder in enumerate(folders):
            if folder["id"] == folder_id:
                folder_index = i
                old_folder_name = folder["name"]
                break
        
        if folder_index is None:
            return jsonify({"error": "Folder not found"}), 404
        
        # Check if folder with same name already exists
        if any(folder["name"].lower() == folder_name.lower() and folder["id"] != folder_id for folder in folders):
            return jsonify({"error": f"Folder '{folder_name}' already exists"}), 400
        
        # Update folder
        folders[folder_index]["name"] = folder_name
        folders[folder_index]["updated_at"] = datetime.datetime.now().isoformat()
        
        # Save folders to file
        with open(folders_file, 'w') as f:
            json.dump({"folders": folders}, f)
        
        # Rename physical folder if needed
        if old_folder_name:
            old_folder_path = os.path.join(PDF_DIR, old_folder_name)
            new_folder_path = os.path.join(PDF_DIR, folder_name)
            if os.path.exists(old_folder_path) and old_folder_path != new_folder_path:
                os.rename(old_folder_path, new_folder_path)
        
        return jsonify({"folder": folders[folder_index]}), 200
    except Exception as e:
        logging.error(f"Error updating folder: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/folders/<folder_id>", methods=["DELETE"])
@login_required
@role_required(['admin', 'editor'])
def delete_folder(folder_id):
    """API endpoint to delete a folder"""
    try:
        # Read existing folders
        folders_file = os.path.join(CACHE_DIR, "folders.json")
        if not os.path.exists(folders_file):
            return jsonify({"error": "Folder not found"}), 404
        
        with open(folders_file, 'r') as f:
            data = json.load(f)
            folders = data.get("folders", [])
        
        # Find folder to delete
        folder_index = None
        folder_name = None
        for i, folder in enumerate(folders):
            if folder["id"] == folder_id:
                folder_index = i
                folder_name = folder["name"]
                break
        
        if folder_index is None:
            return jsonify({"error": "Folder not found"}), 404
        
        # Don't allow deleting the Uncategorized folder
        if folder_id == "uncategorized":
            return jsonify({"error": "Cannot delete the Uncategorized folder"}), 400
        
        # Delete folder
        deleted_folder = folders.pop(folder_index)
        
        # Save folders to file
        with open(folders_file, 'w') as f:
            json.dump({"folders": folders}, f)
        
        # Move documents to Uncategorized
        # This would require updating document metadata
        
        # Don't delete physical folder to avoid data loss
        # Instead, move contents to Uncategorized
        if folder_name:
            folder_path = os.path.join(PDF_DIR, folder_name)
            uncategorized_path = os.path.join(PDF_DIR, "Uncategorized")
            
            if os.path.exists(folder_path):
                # Create Uncategorized folder if it doesn't exist
                if not os.path.exists(uncategorized_path):
                    os.makedirs(uncategorized_path)
                
                # Move files to Uncategorized
                for filename in os.listdir(folder_path):
                    src_path = os.path.join(folder_path, filename)
                    dst_path = os.path.join(uncategorized_path, filename)
                    if os.path.isfile(src_path):
                        # If file already exists in destination, add a suffix
                        if os.path.exists(dst_path):
                            base, ext = os.path.splitext(filename)
                            dst_path = os.path.join(uncategorized_path, f"{base}_{uuid.uuid4().hex[:8]}{ext}")
                        os.rename(src_path, dst_path)
                
                # Remove empty folder
                try:
                    os.rmdir(folder_path)
                except:
                    pass
        
        return jsonify({"success": True, "deleted": deleted_folder}), 200
    except Exception as e:
        logging.error(f"Error deleting folder: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/documents/move", methods=["POST"])
@login_required
@role_required(['admin', 'editor'])
def move_document():
    """API endpoint to move a document to a different folder by updating ChromaDB metadata"""
    try:
        data = request.get_json()
        
        if not data or 'doc_id' not in data or 'folder_id' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        doc_id = data.get('doc_id')
        folder_id = data.get('folder_id')
        
        logging.info(f"Moving document {doc_id} to folder {folder_id}")
        
        # Get the ChromaDB collection
        collection = get_chroma_collection()
        
        # Get all chunks for this document
        results = collection.get(
            where={"doc_id": doc_id}
        )
        
        if not results or not results['ids']:
            return jsonify({"error": f"Document {doc_id} not found"}), 404
        
        # Update folder information for all chunks
        updated_count = 0
        for i, chunk_id in enumerate(results['ids']):
            metadata = results['metadatas'][i]
            metadata['folder'] = folder_id
            
            # Update metadata in ChromaDB
            collection.update(
                ids=[chunk_id],
                metadatas=[metadata]
            )
            updated_count += 1
        
        logging.info(f"Updated folder for {updated_count} chunks of document {doc_id}")
        
        return jsonify({
            "success": True, 
            "message": f"Document moved successfully ({updated_count} chunks updated)"
        })
    except Exception as e:
        logging.error(f"Error moving document: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/documents-json", methods=["GET"])
def debug_documents_json():
    """Debug endpoint to get the raw documents.json file"""
    try:
        documents_file = os.path.join(CACHE_DIR, "documents.json")
        if os.path.exists(documents_file):
            with open(documents_file, 'r') as f:
                try:
                    docs_data = json.load(f)
                    return jsonify(docs_data)
                except Exception as e:
                    logging.error(f"Error loading document metadata: {e}")
                    return jsonify({"error": f"Error loading document metadata: {str(e)}"}), 500
        else:
            return jsonify({"documents": []}), 200
    except Exception as e:
        logging.error(f"Error getting documents.json: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset-document-folders", methods=["POST"])
def reset_document_folders():
    """Reset document folders based on folder counts"""
    try:
        # Load folders
        folders_file = os.path.join(CACHE_DIR, "folders.json")
        if os.path.exists(folders_file):
            with open(folders_file, 'r') as f:
                folders_data = json.load(f)
                folders = folders_data.get("folders", [])
        else:
            folders = []
        
        # Create a mapping of folder names to IDs
        folder_map = {folder.get("name"): folder.get("id") for folder in folders}
        
        # Load documents
        documents_file = os.path.join(CACHE_DIR, "documents.json")
        if os.path.exists(documents_file):
            with open(documents_file, 'r') as f:
                docs_data = json.load(f)
                documents = docs_data.get("documents", [])
        else:
            documents = []
        
        # Assign documents to folders based on naming patterns
        for doc in documents:
            doc_id = doc.get("doc_id", "")
            
            # Default to uncategorized
            doc["folder"] = "uncategorized"
            
            # Check for Python documents
            if doc_id.startswith("Python_"):
                doc["folder"] = folder_map.get("Python", "uncategorized")
            
            # Check for Software documents
            elif doc_id.startswith("Software_") or doc_id == "Sofatware_Unit-3":
                doc["folder"] = folder_map.get("Software", "uncategorized")
            
            # Check for Big data documents
            elif "Big_Data" in doc_id or "BIG_DATA" in doc_id:
                doc["folder"] = folder_map.get("Big data", "uncategorized")
            
            # Check for Cloud Computing documents
            elif "cloud" in doc_id.lower():
                doc["folder"] = folder_map.get("Cloud Computing", "uncategorized")
            
            # Check for Official documents
            elif "OFFICIAL" in doc_id or doc_id == "Digital_Notes_DA":
                doc["folder"] = folder_map.get("Official", "uncategorized")
        
        # Save updated documents
        with open(documents_file, 'w') as f:
            json.dump({"documents": documents}, f, indent=2)
        
        return jsonify({"success": True, "message": "Document folders reset successfully"})
    except Exception as e:
        logging.error(f"Error resetting document folders: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/documents/assign-folders", methods=["POST"])
def assign_document_folders():
    """Directly assign documents to folders based on provided mapping"""
    try:
        data = request.get_json()
        if not data or "assignments" not in data:
            return jsonify({"error": "Missing assignments data"}), 400
            
        assignments = data["assignments"]
        
        # Load current document metadata
        documents_file = os.path.join(CACHE_DIR, "documents.json")
        if os.path.exists(documents_file):
            with open(documents_file, 'r') as f:
                try:
                    docs_data = json.load(f)
                    documents = docs_data.get("documents", [])
                except Exception as e:
                    logging.error(f"Error loading documents metadata: {e}")
                    documents = []
        else:
            documents = []
            
        # Create a lookup dictionary for faster access
        doc_dict = {doc.get("doc_id"): doc for doc in documents}
        
        # Update folder assignments
        for assignment in assignments:
            doc_id = assignment.get("doc_id")
            folder_id = assignment.get("folder_id")
            
            if doc_id and folder_id:
                if doc_id in doc_dict:
                    # Update existing document
                    doc_dict[doc_id]["folder"] = folder_id
                    logging.info(f"Updated folder for {doc_id} to {folder_id}")
                else:
                    # Add new document entry
                    documents.append({
                        "doc_id": doc_id,
                        "folder": folder_id,
                        "upload_date": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat()
                    })
                    logging.info(f"Added new document {doc_id} with folder {folder_id}")
        
        # Save updated metadata
        with open(documents_file, 'w') as f:
            json.dump({"documents": documents}, f, indent=2)
            
        return jsonify({
            "success": True, 
            "message": f"Updated {len(assignments)} document folder assignments"
        })
    except Exception as e:
        logging.error(f"Error assigning document folders: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/fix-document-folders", methods=["POST"])
def fix_document_folders():
    """Fix document folder assignments by updating metadata in ChromaDB"""
    try:
        # Get the ChromaDB collection
        collection = get_chroma_collection()
        
        # Load folders
        folders_file = os.path.join(CACHE_DIR, "folders.json")
        if os.path.exists(folders_file):
            with open(folders_file, 'r') as f:
                folders_data = json.load(f)
                folders = folders_data.get("folders", [])
        else:
            folders = []
            
        # Create folder ID lookup
        folder_lookup = {}
        for folder in folders:
            folder_name = folder.get("name", "").lower()
            folder_lookup[folder_name] = folder.get("id")
        
        # Get all documents from ChromaDB
        all_data = collection.get()
        
        # Group by document ID
        doc_chunks = {}
        for i, meta in enumerate(all_data['metadatas']):
            doc_id = meta.get('doc_id')
            if doc_id:
                if doc_id not in doc_chunks:
                    doc_chunks[doc_id] = []
                doc_chunks[doc_id].append({
                    'id': all_data['ids'][i],
                    'metadata': meta
                })
        
        # Update folder information for each document
        updated_count = 0
        for doc_id, chunks in doc_chunks.items():
            # Determine folder based on document name
            folder_id = "uncategorized"
            
            # Python documents
            if "python" in doc_id.lower():
                folder_id = folder_lookup.get("python", "uncategorized")
            # Big data documents
            elif "big_data" in doc_id.lower() or "big data" in doc_id.lower():
                folder_id = folder_lookup.get("big data", "uncategorized")
            # Software documents
            elif "software" in doc_id.lower() or "sofatware" in doc_id.lower():
                folder_id = folder_lookup.get("software", "uncategorized")
            # Cloud Computing documents
            elif "cloud" in doc_id.lower():
                folder_id = folder_lookup.get("cloud computing", "uncategorized")
            # Official documents
            elif "official" in doc_id.lower() or doc_id == "Digital_Notes_DA":
                folder_id = folder_lookup.get("official", "uncategorized")
            
            # Update metadata for all chunks of this document
            for chunk in chunks:
                chunk_id = chunk['id']
                metadata = chunk['metadata']
                metadata['folder'] = folder_id
                
                # Update metadata in ChromaDB
                collection.update(
                    ids=[chunk_id],
                    metadatas=[metadata]
                )
                updated_count += 1
        
        return jsonify({
            "success": True, 
            "message": f"Updated folder information for {len(doc_chunks)} documents ({updated_count} chunks)",
            "documents": list(doc_chunks.keys())
        })
    except Exception as e:
        logging.error(f"Error fixing document folders: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/permissions', methods=['GET'])
@login_required
def api_auth_permissions():
    """API endpoint to get current user's permissions"""
    if current_user.is_authenticated:
        return jsonify({
            "role": current_user.role,
            "permissions": {
                "can_view": current_user.can_view(),
                "can_edit": current_user.can_edit(),
                "can_upload": current_user.can_upload(),
                "can_manage": current_user.can_manage(),
                "can_manage_users": current_user.can_manage_users(),
                "is_admin": current_user.is_admin
            }
        }), 200
    else:
        return jsonify({
            "role": None,
            "permissions": {
                "can_view": False,
                "can_edit": False,
                "can_upload": False,
                "can_manage": False,
                "can_manage_users": False,
                "is_admin": False
            }
        }), 401

# User management API endpoints
@app.route('/api/users', methods=['GET'])
@login_required
@role_required('admin')
def get_users():
    """API endpoint to get all users"""
    try:
        users = User.query.all()
        return jsonify({
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_admin": user.is_admin,
                    "is_active": user.is_active,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "created_at": user.created_at.isoformat()
                } for user in users
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    """API endpoint to create a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == data.get('username')) |
        (User.email == data.get('email'))
    ).first()
    
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 400
    
    # Create new user
    try:
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=data.get('role', 'viewer')
        )
        if data.get('role') == 'admin':
            user.is_admin = True
            
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_user(user_id):
    """API endpoint to update a user"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if username or email already exists for another user
    if data.get('username') and data.get('username') != user.username:
        existing_user = User.query.filter_by(username=data.get('username')).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({"error": "Username already exists"}), 400
    
    if data.get('email') and data.get('email') != user.email:
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({"error": "Email already exists"}), 400
    
    # Update user
    try:
        if data.get('username'):
            user.username = data.get('username')
        if data.get('email'):
            user.email = data.get('email')
        if data.get('password'):
            user.set_password(data.get('password'))
        if data.get('first_name'):
            user.first_name = data.get('first_name')
        if data.get('last_name'):
            user.last_name = data.get('last_name')
        if data.get('role'):
            user.role = data.get('role')
            user.is_admin = (data.get('role') == 'admin')
        
        db.session.commit()
        
        return jsonify({
            "message": "User updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat()
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """API endpoint to delete a user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        return jsonify({"error": "You cannot delete your own account"}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)
