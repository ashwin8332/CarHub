#!/usr/bin/env python3
"""
Database Column Checker - Check if cancellation_fee column exists in Order table
"""

from app import app, db, Order, User, UserActivity

def check_database_columns():
    """Check if the cancellation_fee column exists in the Order table"""
    print("🔍 Checking database columns...")
    
    try:
        # Check Order model columns
        print("\n=== Order Model Columns ===")
        order_columns = Order.__table__.columns.keys()
        print(f"Order columns: {list(order_columns)}")
        
        if 'cancellation_fee' in order_columns:
            print("✅ cancellation_fee column EXISTS!")
            
            # Try to access some orders
            orders = Order.query.limit(3).all()
            print(f"\n📊 Found {len(orders)} orders:")
            for order in orders:
                print(f"  Order {order.id}: user={order.user_id}, status={order.order_status}, total=${order.total_amount}")
                print(f"    cancellation_fee: ${order.cancellation_fee or 0.00}")
        else:
            print("❌ cancellation_fee column does NOT exist!")
            print("Need to add the column to the database.")
            return False
            
        # Check UserActivity columns
        print("\n=== UserActivity Model Columns ===")
        activity_columns = UserActivity.__table__.columns.keys()
        print(f"UserActivity columns: {list(activity_columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():  # Create application context
        success = check_database_columns()
        if not success:
            print("\n🔧 Database migration needed!")
        else:
            print("\n✅ Database is ready!")
