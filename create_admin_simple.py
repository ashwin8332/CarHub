#!/usr/bin/env python3
"""
Simple admin user creator that doesn't start Flask app
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

# Database path
db_path = 'instance/carhub.db'

def create_admin_user():
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the Flask app first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if admin user exists
        cursor.execute("SELECT id FROM user WHERE email = ?", ('admin@carhub.com',))
        if cursor.fetchone():
            print("✅ Admin user already exists!")
            return
        
        # Create admin user
        hashed_password = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO user (username, email, password, is_verified) 
            VALUES (?, ?, ?, ?)
        """, ('admin', 'admin@carhub.com', hashed_password, True))
        
        conn.commit()
        print("✅ Admin user created successfully!")
        print("Email: admin@carhub.com")
        print("Password: admin123")
        print("\nYou can now login and access the admin panel dropdown!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_admin_user()
