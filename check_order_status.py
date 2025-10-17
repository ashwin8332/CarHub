#!/usr/bin/env python3
"""
Check order statuses to debug cancel button issue
"""

from app import app, Order

def check_order_statuses():
    with app.app_context():
        orders = Order.query.all()
        print(f"Found {len(orders)} orders:")
        print("-" * 60)
        
        for order in orders:
            print(f"Order {order.id}:")
            print(f"  - payment_status: '{order.payment_status}'")
            print(f"  - order_status: '{order.order_status}'")
            print(f"  - user_id: {order.user_id}")
            print(f"  - total_amount: ${order.total_amount}")
            print(f"  - cancellation_fee: ${order.cancellation_fee or 0}")
            print("-" * 40)

if __name__ == "__main__":
    check_order_statuses()
