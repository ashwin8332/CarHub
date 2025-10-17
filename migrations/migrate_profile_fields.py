#!/usr/bin/env python3
"""
Database Migration Script - Add Profile Fields to User Table
This script adds the new profile fields to the existing user table.
"""

import os
import sys
import sqlite3
from datetime import datetime

def get_db_path():
    """Get the database path."""
    return os.path.join('instance', 'carhub.db')

def backup_database():
    """Create a backup of the current database."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the app once to create the database.")
        return False
    
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Copy database file
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return False

def check_columns_exist(cursor, table_name, column_names):
    """Check if columns already exist in the table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    missing_columns = []
    existing_new_columns = []
    
    for col in column_names:
        if col in existing_columns:
            existing_new_columns.append(col)
        else:
            missing_columns.append(col)
    
    return missing_columns, existing_new_columns

def migrate_user_table():
    """Add new profile fields to the user table."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print("❌ Database file does not exist!")
        return False
    
    # New columns to add
    new_columns = {
        'first_name': 'VARCHAR(100)',
        'last_name': 'VARCHAR(100)', 
        'phone': 'VARCHAR(20)',
        'date_of_birth': 'DATE',
        'gender': 'VARCHAR(20)',
        'address': 'TEXT',
        'city': 'VARCHAR(100)',
        'state': 'VARCHAR(100)',
        'zip_code': 'VARCHAR(20)',
        'country': 'VARCHAR(100)',
        'occupation': 'VARCHAR(200)',
        'bio': 'TEXT',
        'preferred_contact_method': 'VARCHAR(20) DEFAULT "email"',
        'profile_updated_at': 'DATETIME'
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check which columns are missing
        missing_columns, existing_columns = check_columns_exist(cursor, 'user', new_columns.keys())
        
        if existing_columns:
            print(f"✅ These columns already exist: {', '.join(existing_columns)}")
        
        if not missing_columns:
            print("✅ All profile columns already exist in the database!")
            conn.close()
            return True
        
        print(f"📝 Adding {len(missing_columns)} new columns to user table...")
        
        # Add each missing column
        for column_name in missing_columns:
            column_type = new_columns[column_name]
            alter_sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_type}"
            
            try:
                cursor.execute(alter_sql)
                print(f"   ✅ Added column: {column_name}")
            except sqlite3.Error as e:
                print(f"   ❌ Failed to add column {column_name}: {e}")
                conn.rollback()
                conn.close()
                return False
        
        # Commit changes
        conn.commit()
        print("✅ Successfully added all new profile columns!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(user)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"✅ User table now has {len(columns_after)} columns")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main migration function."""
    print("🔄 Starting database migration...")
    print("=" * 50)
    
    # Create instance directory if it doesn't exist
    instance_dir = 'instance'
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"📁 Created directory: {instance_dir}")
    
    # Check if database exists
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("❌ Database not found! Please run the Flask app once to create the database.")
        print("   Run: python app.py")
        return
    
    # Backup database
    if not backup_database():
        print("❌ Migration aborted - could not create backup")
        return
    
    # Perform migration
    if migrate_user_table():
        print("\n" + "=" * 50)
        print("✅ Migration completed successfully!")
        print("🚀 You can now run the Flask app with the enhanced profile features.")
        print("   Run: python app.py")
    else:
        print("\n" + "=" * 50)
        print("❌ Migration failed!")
        print("💡 You can restore from backup if needed.")

if __name__ == "__main__":
    main()
