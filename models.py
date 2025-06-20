"""
Database models for the PDF Knowledge Base application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.String(20), default='viewer', nullable=False)  # 'admin', 'editor', 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, username, email, password, first_name=None, last_name=None, role='viewer'):
        """Initialize a new user."""
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        if role == 'admin':
            self.is_admin = True
    
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
    
    def update_last_login(self):
        """Update the user's last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
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

    # Add role-based permission methods
    def has_role(self, role):
        """Check if user has the specified role."""
        if self.is_admin:
            return True  # Admin has all roles
        return self.role == role
    
    def can_view(self):
        """Check if user can view documents."""
        return True  # All users can view
    
    def can_edit(self):
        """Check if user can edit documents."""
        return self.is_admin or self.role in ['editor', 'admin']
    
    def can_upload(self):
        """Check if user can upload documents."""
        return self.is_admin or self.role in ['editor', 'admin']
    
    def can_manage(self):
        """Check if user can manage documents and folders."""
        return self.is_admin or self.role in ['editor', 'admin']
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.is_admin

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
                last_name='User',
                role='admin'
            )
            admin_user.is_admin = True
            db.session.add(admin_user)
            
            # Create Shabeen Jahan admin account
            shabeen_admin = User(
                username='shabeen',
                email='user@example.com',
                password='change-me',
                first_name='Shabeen',
                last_name='Jahan',
                role='admin'
            )
            shabeen_admin.is_admin = True
            db.session.add(shabeen_admin)
            
            # Create default editor user
            editor_user = User(
                username='editor',
                email='editor@example.com',
                password='editor123',
                first_name='Editor',
                last_name='User',
                role='editor'
            )
            db.session.add(editor_user)
            
            # Create default viewer user
            viewer_user = User(
                username='viewer',
                email='viewer@example.com',
                password='viewer123',
                first_name='Viewer',
                last_name='User',
                role='viewer'
            )
            db.session.add(viewer_user)
            
            db.session.commit()
            print("Created default users: admin/admin123, shabeen/shabeen123, editor/editor123, viewer/viewer123")
