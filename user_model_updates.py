# user_model_updates.py - Database Model Updates for Google OAuth

"""
Add these fields to your existing User model to support Google OAuth.
This is a reference implementation - adapt it to your existing User model.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Example User model with Google OAuth support
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic user information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))  # Make nullable for Google-only users
    
    # Google OAuth fields (ADD THESE TO YOUR EXISTING MODEL)
    google_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    profile_picture = db.Column(db.String(200), nullable=True)
    
    # Account status
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __init__(self, email, name, password=None, google_id=None, profile_picture=None):
        self.email = email
        self.name = name
        self.google_id = google_id
        self.profile_picture = profile_picture
        
        if password:
            self.set_password(password)
        
        # Google users are automatically verified
        if google_id:
            self.is_verified = True
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_google_user(self):
        """Check if user signed up with Google"""
        return self.google_id is not None
    
    def can_login_with_password(self):
        """Check if user can login with password"""
        return self.password_hash is not None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def __repr__(self):
        return f'<User {self.email}>'

# Database migration commands to add Google OAuth fields
# Run these commands in your Flask shell or create a migration file

"""
# If using Flask-Migrate, create a new migration:
flask db migrate -m "Add Google OAuth fields to User model"
flask db upgrade

# Or run these SQL commands directly:
ALTER TABLE user ADD COLUMN google_id VARCHAR(100) UNIQUE;
ALTER TABLE user ADD COLUMN profile_picture VARCHAR(200);
ALTER TABLE user MODIFY COLUMN password_hash VARCHAR(128) NULL;
CREATE INDEX ix_user_google_id ON user (google_id);
"""

# Example of how to create a Google user in your route
def create_or_update_google_user(user_info):
    """
    Create or update a user from Google OAuth data
    """
    # Note: Replace 'app' with your actual Flask app module name
    # from app import db  # Import your db instance
    # For now, using the db instance defined in this module
    
    # Check if user exists by email
    user = User.query.filter_by(email=user_info['email']).first()
    
    if not user:
        # Create new user
        user = User(
            email=user_info['email'],
            name=user_info['name'],
            google_id=user_info['google_id'],
            profile_picture=user_info['picture']
        )
        db.session.add(user)
    else:
        # Update existing user with Google info
        if not user.google_id:
            user.google_id = user_info['google_id']
        
        user.profile_picture = user_info['picture']
        user.is_verified = True
        user.name = user_info['name']  # Update name in case it changed
    
    user.update_last_login()
    db.session.commit()
    
    return user
