#!/usr/bin/env python3
"""
Google OAuth Test Script for CarHub
This script tests if the Google OAuth integration is working properly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_oauth_setup():
    print("🔍 Testing Google OAuth Setup for CarHub")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("1. Checking environment variables...")
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not google_client_id or google_client_id == 'your-google-client-id.apps.googleusercontent.com':
        print("❌ GOOGLE_CLIENT_ID is not set or using placeholder value")
        print("   Please set your actual Google Client ID in .env file")
        return False
    else:
        print(f"✅ GOOGLE_CLIENT_ID is set: {google_client_id[:20]}...")
    
    if not google_client_secret or google_client_secret == 'your-google-client-secret':
        print("❌ GOOGLE_CLIENT_SECRET is not set or using placeholder value")
        print("   Please set your actual Google Client Secret in .env file")
        return False
    else:
        print("✅ GOOGLE_CLIENT_SECRET is set")
    
    # Test 2: Check Google Auth packages
    print("\n2. Checking Google Auth packages...")
    try:
        import google.oauth2.id_token
        import google.auth.transport.requests
        print("✅ Google Auth packages are installed and importable")
    except ImportError as e:
        print(f"❌ Google Auth packages are missing: {e}")
        print("   Run: pip install google-auth google-auth-oauthlib google-auth-httplib2")
        return False
    
    # Test 3: Check Flask app configuration
    print("\n3. Checking Flask app integration...")
    try:
        from app import app, GOOGLE_AUTH_AVAILABLE
        
        if not GOOGLE_AUTH_AVAILABLE:
            print("❌ Google Auth is not available in Flask app")
            return False
        else:
            print("✅ Google Auth is available in Flask app")
        
        with app.app_context():
            if app.config.get('GOOGLE_CLIENT_ID'):
                print("✅ Google Client ID is configured in Flask app")
            else:
                print("❌ Google Client ID is not configured in Flask app")
                return False
                
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    
    # Test 4: Check database model
    print("\n4. Checking database model...")
    try:
        from app import User, db
        
        # Check if User model has Google OAuth fields
        user_columns = [column.name for column in User.__table__.columns]
        
        if 'google_id' in user_columns:
            print("✅ User model has google_id field")
        else:
            print("❌ User model is missing google_id field")
            return False
            
        if 'profile_picture' in user_columns:
            print("✅ User model has profile_picture field")
        else:
            print("❌ User model is missing profile_picture field")
            return False
            
    except Exception as e:
        print(f"❌ Database model check failed: {e}")
        return False
    
    # Test 5: Check routes
    print("\n5. Checking Flask routes...")
    try:
        from app import app
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))
        
        if '/auth/google' in routes:
            print("✅ Google OAuth route (/auth/google) is registered")
        else:
            print("❌ Google OAuth route (/auth/google) is missing")
            return False
            
    except Exception as e:
        print(f"❌ Route check failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Google OAuth setup looks good.")
    print("\n📋 Next steps:")
    print("1. Set up Google Cloud Console OAuth credentials")
    print("2. Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    print("3. Run the Flask app and test Google Sign-In")
    print("\n🚀 To test the app:")
    print("   python app.py")
    print("   Then visit: http://localhost:5000/login")
    
    return True

def print_setup_instructions():
    print("\n📚 Google Cloud Console Setup Instructions:")
    print("=" * 50)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Go to 'APIs & Services' > 'Credentials'")
    print("4. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
    print("5. Choose 'Web application'")
    print("6. Add these Authorized JavaScript origins:")
    print("   - http://localhost:5000")
    print("   - http://127.0.0.1:5000")
    print("7. Add these Authorized redirect URIs:")
    print("   - http://localhost:5000/auth/google")
    print("   - http://127.0.0.1:5000/auth/google")
    print("8. Copy the Client ID and Client Secret")
    print("9. Update your .env file with the real values")

if __name__ == "__main__":
    success = test_google_oauth_setup()
    
    if not success:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        print_setup_instructions()
        sys.exit(1)
    else:
        print_setup_instructions()
        sys.exit(0)
