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

# Import configuration
from config import (
    PDF_DIR, FLASK_DEBUG, MAX_CONTENT_LENGTH,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE, CACHE_DIR,
    SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    PERMANENT_SESSION_LIFETIME, LOGIN_DISABLED
)

# Import core functionality
from core.indexer import index_pdf, get_chroma_collection
from core.search import query_knowledge_base, get_document_list, reindex_document

from core.auth.models import db, User, init_db
from core.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm, ProfileForm
from core.auth.decorators import (
    permission_required, role_required, admin_required,
    upload_required, manage_required, search_required
)

# Define permission-based decorators
admin_required = role_required('admin')
upload_required = permission_required('upload')
search_required = permission_required('search')
manage_required = permission_required('manage')

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
    flash('Public registration is disabled. Please contact an administrator to create an account.', 'info')
    return redirect(url_for('login'))

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
@upload_required
def upload_page():
    """Page for uploading and indexing PDFs"""
    return render_template('upload.html')

@app.route('/search')
@search_required
def search_page():
    """Page for searching indexed documents"""
    return render_template('search.html')

@app.route('/manage')
@manage_required
def manage_page():
    """Page for managing indexed documents"""
    return render_template('manage.html')

@app.route('/users')
@admin_required
def users_page():
    """Page for managing users (admin only)"""
    return render_template('users.html')

# API Routes
@app.route("/api/upload", methods=["POST"])
@upload_required
def upload_api():
    """API endpoint for uploading and indexing PDFs"""
    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field."}), 400

    files = request.files.getlist("pdfs")
    category = request.form.get('category', 'Uncategorized')

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
        progress_updates.append(f"Starting indexing: {doc_id} (Category: {category})")
        logging.info(f"Starting indexing for {doc_id} with category: {category}")

        start_time = time.time()
        
        # Pass a callback for progress updates
        def progress_callback(message):
            progress_updates.append(message)
            logging.info(message)
        
        # Pass category and callback to index_pdf function
        index_pdf(save_path, category=category, progress_callback=progress_callback)
        end_time = time.time()

        indexed_files.append(doc_id)
        progress_updates.append(f"Finished indexing: {doc_id} in {end_time - start_time:.2f} sec")
        logging.info(f"Finished indexing {doc_id} in {end_time - start_time:.2f} seconds")

    total_time = time.time() - total_start
    logging.info(f"Total indexing time for {len(indexed_files)} PDFs: {total_time:.2f} seconds")
    return jsonify({
        "message": f"Indexed {len(indexed_files)} PDF(s) in category '{category}': {', '.join(indexed_files)}",
        "category": category
    })

@app.route('/api/progress')
def progress_stream():
    """Server-sent events endpoint for progress updates"""
    def generate():
        last_idx = 0
        while True:
            if last_idx < len(progress_updates):
                # Send the progress update
                yield f"data: {progress_updates[last_idx]}\n\n"
                last_idx += 1
                
                # If this was the last update and it contains "Finished indexing", end the stream
                if last_idx == len(progress_updates) and "Finished indexing" in progress_updates[last_idx - 1]:
                    break
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route("/api/query", methods=["POST"])
@search_required
def query_api():
    """API endpoint for searching indexed documents"""
    data = request.get_json()
    query_text = data.get("query")
    use_original = data.get("use_original", False)

    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    # If use_original is True, we need to bypass spell correction
    if use_original:
        # Import the search function and call it directly without spell correction
        from core.search import query_knowledge_base_no_correction
        results = query_knowledge_base_no_correction(query_text, top_k=10)
    else:
        results = query_knowledge_base(query_text, top_k=10)

    return jsonify(results)

@app.route("/api/suggestions", methods=["POST"])
@search_required
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
@manage_required
def get_documents():
    """API endpoint to get list of indexed documents"""
    try:
        doc_stats = get_document_list()
        return jsonify({"documents": doc_stats})
    except Exception as e:
        logging.error(f"Error getting document list: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/delete-document", methods=["POST"])
@manage_required
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

@app.route("/api/reindex-document", methods=["POST"])
@manage_required
def reindex_document_api():
    """API endpoint to re-index a document"""
    try:
        data = request.get_json()
        doc_id = data.get("doc_id")

        logging.info(f"Attempting to re-index document: {doc_id}")

        if not doc_id:
            logging.warning("Re-index request missing document ID")
            return jsonify({"error": "Document ID is required"}), 400

        # Re-index the document
        result = reindex_document(doc_id)

        if result.get('success'):
            logging.info(f"Successfully re-indexed document: {doc_id}")
            return jsonify({
                "success": True,
                "message": result.get('message'),
                "chunks_created": result.get('chunks_created', 0)
            })
        else:
            logging.error(f"Failed to re-index document {doc_id}: {result.get('error')}")
            return jsonify({"error": result.get('error')}), 500

    except Exception as e:
        logging.error(f"Error in re-index API: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/api/users")
@admin_required
def get_users():
    """API endpoint to get list of users (admin only)"""
    try:
        users = User.query.all()
        user_list = []

        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })

        return jsonify({"users": user_list})
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    """API endpoint to delete a user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting shabreen user
        if user.username == 'shabreen':
            return jsonify({"error": "Cannot delete main admin user"}), 403
        
        # Prevent deleting yourself
        if user.id == current_user.id:
            return jsonify({"error": "Cannot delete your own account"}), 403
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"success": True, "message": f"User {user.username} deleted successfully"})
    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    """API endpoint to toggle user active status (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deactivating shabreen user
        if user.username == 'shabreen':
            return jsonify({"error": "Cannot deactivate main admin user"}), 403
        
        # Prevent deactivating yourself
        if user.id == current_user.id:
            return jsonify({"error": "Cannot deactivate your own account"}), 403
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"User {user.username} {'activated' if user.is_active else 'deactivated'} successfully",
            "is_active": user.is_active
        })
    except Exception as e:
        logging.error(f"Error toggling user status: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    """API endpoint to update user details (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Prevent changing admin username
        if user.username == 'shabreen' and data.get('username') != 'shabreen':
            return jsonify({"error": "Cannot change main admin username"}), 403
        
        # Update basic info
        if 'username' in data and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({"error": "Username already exists"}), 400
            user.username = data['username']
            
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({"error": "Email already exists"}), 400
            user.email = data['email']
            
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
            
        # Update role
        if 'role' in data and data['role'] in ['admin', 'editor', 'uploader', 'viewer']:
            # Prevent changing shabreen's role
            if user.username == 'shabreen' and data['role'] != 'admin':
                return jsonify({"error": "Cannot change main admin role"}), 403
            user.role = data['role']
            user.is_admin = (data['role'] == 'admin')
            
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"User {user.username} updated successfully",
            "user": {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/users", methods=["POST"])
@admin_required
def create_user():
    """API endpoint to create a new user (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Check if username exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username already exists"}), 400
            
        # Check if email exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already exists"}), 400
            
        # Validate role
        if data['role'] not in ['admin', 'editor', 'uploader', 'viewer']:
            return jsonify({"error": "Invalid role"}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.role = data['role']
        user.is_admin = (data['role'] == 'admin')
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"User {user.username} created successfully",
            "user": {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)
