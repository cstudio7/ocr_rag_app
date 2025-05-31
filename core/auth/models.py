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
    role = db.Column(db.String(20), nullable=False, default='viewer')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
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

    def update_last_login(self):
        """Update the user's last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def has_permission(self, permission):
        """Check if user has a specific permission based on their role."""
        role_permissions = {
            'admin': ['search', 'upload', 'manage', 'user_management'],
            'editor': ['search', 'upload', 'manage'],
            'uploader': ['search', 'upload'],
            'viewer': ['search']
        }
        return permission in role_permissions.get(self.role, [])

    def can_search(self):
        """Check if user can search documents."""
        return self.has_permission('search')

    def can_upload(self):
        """Check if user can upload documents."""
        return self.has_permission('upload')

    def can_manage(self):
        """Check if user can manage documents."""
        return self.has_permission('manage')

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.has_permission('user_management') or self.is_admin

    def get_role_display(self):
        """Get a human-readable role name."""
        role_names = {
            'admin': 'Administrator',
            'editor': 'Editor',
            'uploader': 'Uploader',
            'viewer': 'Viewer'
        }
        return role_names.get(self.role, 'Unknown')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

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

def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # # Create default admin user if it doesn't exist
        # admin_user = User.query.filter_by(username='admin').first()
        # if not admin_user:
        #     admin_user = User(
        #         username='admin',
        #         email='admin@example.com',
        #         password='admin123',
        #         first_name='Admin',
        #         last_name='User'
        #     )
        #     admin_user.is_admin = True
        #     admin_user.role = 'admin'
        #     db.session.add(admin_user)
        #     db.session.commit()
        #     print("Created default admin user: admin/admin123 (role: admin)") 