"""
Database models for the PDF Knowledge Base application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), default='viewer', nullable=False)  # viewer, uploader, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, username, email, password, first_name=None, last_name=None):
        """Initialize a new user."""
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def get_display_name(self):
        """Get the user's display name (alias for get_full_name)."""
        return self.get_full_name()
    
    def update_last_login(self):
        """Update the user's last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def can_upload(self):
        """Check if user can upload documents."""
        return self.role in ['uploader', 'admin']

    def can_manage_documents(self):
        """Check if user can delete/manage documents."""
        return self.role in ['uploader', 'admin']

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == 'admin'

    def can_manage_folders(self):
        """Check if user can create/manage folders."""
        return self.role in ['uploader', 'admin']

    def can_search(self):
        """Check if user can search documents."""
        return True  # All users can search

    @property
    def is_admin(self):
        """Compatibility property for existing code."""
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'
    
    # Flask-Login required methods
    def get_id(self):
        """Return the user ID as a string."""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True
    
    @property
    def is_anonymous(self):
        """Return True if the user is anonymous."""
        return False


class Folder(db.Model):
    """Folder model for organizing documents."""

    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#6366f1', nullable=False)  # Hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('folders', lazy=True, cascade='all, delete-orphan'))
    documents = db.relationship('Document', backref='folder', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, user_id, description=None, color='#6366f1'):
        """Initialize a new folder."""
        self.name = name
        self.user_id = user_id
        self.description = description
        self.color = color

    def get_document_count(self):
        """Get the number of documents in this folder."""
        return len(self.documents)

    def __repr__(self):
        return f'<Folder {self.name}>'


class Document(db.Model):
    """Document model for tracking uploaded files."""

    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.String(255), unique=True, nullable=False, index=True)  # ChromaDB document ID
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100), default='application/pdf', nullable=False)
    chunk_count = db.Column(db.Integer, default=0, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)  # Can be uncategorized

    # Relationships
    user = db.relationship('User', backref=db.backref('documents', lazy=True))

    def __init__(self, doc_id, filename, original_filename, file_path, file_size, user_id, folder_id=None):
        """Initialize a new document."""
        self.doc_id = doc_id
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.file_size = file_size
        self.user_id = user_id
        self.folder_id = folder_id

    def get_file_size_formatted(self):
        """Get formatted file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<Document {self.doc_id}>'


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            admin_user.role = 'admin'  # Set role instead of is_admin
            db.session.add(admin_user)
            db.session.commit()
            print("Created default admin user: admin/admin123")

            # Create default "Uncategorized" folder for admin user
            uncategorized_folder = Folder(
                name='Uncategorized',
                user_id=admin_user.id,
                description='Default folder for uncategorized documents',
                color='#6b7280'
            )
            db.session.add(uncategorized_folder)
            db.session.commit()
            print("Created default 'Uncategorized' folder")
