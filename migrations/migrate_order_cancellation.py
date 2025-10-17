#!/usr/bin/env python3
"""
Database Migration Script - Add cancellation_fee column to Order table
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add cancellation_fee column to Order table"""
    print("🔧 Starting database migration...")
    
    # Database file path
    db_path = "instance/carhub.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    # Create backup first
    backup_path = f"instance/carhub.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️ Could not create backup: {e}")
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute('PRAGMA table_info([order])')
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cancellation_fee' in columns:
            print("✅ cancellation_fee column already exists!")
            return True
        
        # Add cancellation_fee column
        print("Adding cancellation_fee column...")
        cursor.execute("""
            ALTER TABLE [order] 
            ADD COLUMN cancellation_fee DECIMAL(10, 2) DEFAULT 0.00
        """)
        
        # Also add order_status column if it doesn't exist
        if 'order_status' not in columns:
            print("Adding order_status column...")
            cursor.execute("""
                ALTER TABLE [order] 
                ADD COLUMN order_status VARCHAR(20) DEFAULT 'pending'
            """)
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
        # Verify the migration
        cursor.execute('PRAGMA table_info([order])')
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📊 Updated columns: {new_columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 Migration completed! You can now use the order cancellation feature.")
    else:
        print("\n💥 Migration failed! Please check the error and try again.")
