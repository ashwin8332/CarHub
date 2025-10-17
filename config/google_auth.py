# google_auth.py - Google OAuth Implementation for CarHub

from flask import request, jsonify, redirect, url_for, current_app
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_login import login_user
import os
from datetime import datetime

def verify_google_token(credential):
    """
    Verify Google ID token and return user information
    """
    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            current_app.config['GOOGLE_CLIENT_ID']
        )
        
        # Extract user information
        user_info = {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo['name'],
            'picture': idinfo.get('picture', ''),
            'email_verified': idinfo.get('email_verified', False)
        }
        
        return user_info, None
        
    except ValueError as e:
        return None, f"Invalid Google token: {str(e)}"
    except Exception as e:
        return None, f"Token verification failed: {str(e)}"

def handle_google_auth():
    """
    Handle Google OAuth authentication
    Add this route to your main Flask app
    """
    try:
        # Get the credential from the request
        data = request.get_json()
        credential = data.get('credential') if data else None
        
        if not credential:
            return jsonify({'success': False, 'message': 'No credential provided'}), 400
        
        # Verify the Google ID token
        user_info, error = verify_google_token(credential)
        
        if error:
            return jsonify({'success': False, 'message': error}), 400
        
        # Import your User model here
        # from your_models import User, db
        
        # Check if user exists in your database
        # user = User.query.filter_by(email=user_info['email']).first()
        
        # Uncomment and modify this section based on your User model:
        """
        if not user:
            # Create new user
            user = User(
                email=user_info['email'],
                name=user_info['name'],
                google_id=user_info['google_id'],
                profile_picture=user_info['picture'],
                is_verified=True,  # Google accounts are pre-verified
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update existing user's Google ID if not set
            if not user.google_id:
                user.google_id = user_info['google_id']
                user.profile_picture = user_info['picture']
                user.is_verified = True
                db.session.commit()
        
        # Log the user in
        login_user(user, remember=True)
        """
        
        return jsonify({
            'success': True,
            'message': 'Successfully signed in with Google',
            'redirect_url': url_for('dashboard')  # Change this to your desired redirect
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration helper
def setup_google_config(app):
    """
    Setup Google OAuth configuration
    Call this in your app initialization
    """
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not app.config['GOOGLE_CLIENT_ID']:
        print("Warning: GOOGLE_CLIENT_ID not found in environment variables")
    
    return app.config['GOOGLE_CLIENT_ID'] is not None
