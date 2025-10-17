#!/usr/bin/env python3
"""
Database Migration Script for Google OAuth Fields
This script adds the necessary fields to support Google OAuth authentication
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_database():
    print("🔄 Migrating database for Google OAuth support...")
    
    db_path = 'instance/carhub.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run your Flask app first to create the database.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current table schema
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Current user table columns: {columns}")
        
        # Add google_id column if it doesn't exist
        if 'google_id' not in columns:
            print("➕ Adding google_id column...")
            cursor.execute("ALTER TABLE user ADD COLUMN google_id VARCHAR(100)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_google_id ON user (google_id)")
            print("✅ Added google_id column")
        else:
            print("✅ google_id column already exists")
        
        # Add profile_picture column if it doesn't exist
        if 'profile_picture' not in columns:
            print("➕ Adding profile_picture column...")
            cursor.execute("ALTER TABLE user ADD COLUMN profile_picture VARCHAR(200)")
            print("✅ Added profile_picture column")
        else:
            print("✅ profile_picture column already exists")
        
        # Make password_hash nullable for Google users (this requires recreating table)
        # For now, we'll just note this - SQLite doesn't support changing column constraints easily
        
        # Commit changes
        conn.commit()
        print("💾 Database migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(user)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated user table columns: {new_columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_database_connection():
    """Test if we can connect to and query the database"""
    try:
        from app import app, db, User
        
        with app.app_context():
            # Try to query users
            user_count = User.query.count()
            print(f"📊 Database connection successful. Found {user_count} users.")
            
            # Test creating a sample Google user (don't actually save)
            test_user = User(
                username="test_google_user",
                email="test@gmail.com",
                google_id="test_google_id_12345",
                profile_picture="https://example.com/profile.jpg",
                is_verified=True
            )
            print("✅ Google user model creation test passed")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Google OAuth database migration")
    print("=" * 50)
    
    # First, migrate the database
    if migrate_database():
        print("\n🔍 Testing database connection...")
        if test_database_connection():
            print("\n🎉 Database migration and testing completed successfully!")
            print("\n📋 Next steps:")
            print("1. Set up Google Cloud Console OAuth credentials")
            print("2. Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
            print("3. Run: python test_google_oauth.py")
        else:
            print("\n⚠️ Migration succeeded but database test failed")
            print("Please check your Flask app configuration")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
