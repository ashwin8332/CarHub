# CarHub - Database-Connected Web Application

## Overview
Your CarHub application now includes a complete authentication system with database connectivity, featuring:

✅ **User Registration & Login System**
✅ **Password Reset via Email**
✅ **Database Integration with SQLAlchemy**
✅ **Enhanced Homepage with Customer Reviews**
✅ **Video Background Sections**
✅ **Secure Form Validation**

## Features Implemented

### 1. Authentication System
- **Sign Up**: New user registration with email validation
- **Login**: Secure user authentication with session management
- **Forgot Password**: Email-based password reset functionality
- **Password Security**: Hashed passwords using Werkzeug

### 2. Database Integration
- **SQLite Database**: Lightweight database for user management
- **User Model**: Complete user schema with authentication fields
- **Session Management**: Secure user sessions across pages

### 3. Enhanced Homepage
- **Customer Reviews Section**: Real customer testimonials with ratings
- **Video Backgrounds**: Dynamic video sections for different services
- **Responsive Design**: Mobile-friendly layout
- **Modern UI**: Space-themed color scheme with smooth animations

### 4. Payment System
- **Secure Checkout**: Complete payment processing workflow
- **Multiple Payment Methods**: Credit Card, PayPal, Bank Transfer
- **Order Tracking**: Order history and status tracking
- **Payment Validation**: Client and server-side validation
- **Transaction Records**: Detailed payment records and receipts

## Setup Instructions

### 1. Dependencies
All required packages are installed:
```bash
pip install -r requirements.txt
```

### 2. Running the Application
```bash
python app.py
```
The application will be available at: http://127.0.0.1:5000

### 3. Email Configuration (Optional)
To enable password reset emails, update these settings in `app.py`:

```python
# Email configuration (lines 21-27 in app.py)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'your-app-password'     # Your app password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
```

### 4. Database Location
- Database file: `carhub.db` (created automatically)
- User data is stored securely with hashed passwords

### 5. Testing the Payment System
To test the payment system, you can run the payment flow test script:
```bash
python scripts/test_payment_flow.py
```

**Testing with different payment methods:**
- **Credit Card**: Use any of these test card numbers for successful payments:
  - Visa: 4532015112830366
  - Mastercard: 5425233430109903
  - Amex: 371449635398431
  - Any card ending with "0000" will be rejected for testing purposes
- **PayPal**: Simply select PayPal as the payment method
- **Bank Transfer**: Select Bank Transfer option for simulated transfers

## File Structure
```
carhub1/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── instance/
│   └── carhub.db          # SQLite database (auto-created)
├── scripts/               # Helper scripts
│   └── test_payment_flow.py  # Payment testing script
├── static/                # CSS, images, videos
│   ├── style.css
│   ├── logo.png
│   └── *.mp4 videos, .glb 3D models
└── templates/             # HTML templates
    ├── base.html          # Base template with navigation
    ├── index.html         # Enhanced homepage
    ├── login.html         # User login page
    ├── sign_up.html       # User registration
    ├── forgot_password.html
    ├── reset_password.html
    ├── cars.html          # Car listing page
    ├── car_details.html   # Individual car page
    ├── payment.html       # Payment processing page
    ├── payment_success.html  # Payment confirmation
    └── my_orders.html     # Order history page
```

## Key Features Details

### Authentication Flow
1. **Registration**: Users create accounts with email/password
2. **Login**: Secure authentication with session storage
3. **Password Reset**: Token-based email verification system
4. **Session Management**: Automatic login/logout handling

### Homepage Enhancements
- **Customer Reviews**: Grid layout with star ratings and avatars
- **Statistics**: Customer satisfaction metrics
- **Video Sections**: Background videos for different services
- **Responsive Design**: Works on all device sizes

### Security Features
- **Password Hashing**: Secure password storage
- **CSRF Protection**: Form security with Flask-WTF
- **Input Validation**: Server-side form validation
- **Session Security**: Secure session management

### Payment System Details
- **Checkout Flow**: Seamless flow from car selection to payment confirmation
- **Payment Methods**: Support for multiple payment methods
- **Client-Side Validation**: Real-time form validation with JavaScript
- **Server-Side Processing**: Secure payment processing with transaction IDs
- **Card Validation**: Implementation of Luhn algorithm for card number validation
- **Order Management**: Full order lifecycle from creation to completion
- **Payment Success Page**: Detailed confirmation with order information

## Testing the Application

1. **Visit the homepage**: http://127.0.0.1:5000
2. **Create an account**: Click "Sign Up" and register
3. **Login**: Use your credentials to log in
4. **Test password reset**: Try the "Forgot Password" feature
5. **Explore features**: Browse the enhanced homepage sections

## Next Steps

1. **Customize Email Settings**: Add your SMTP configuration for password reset
2. **Add More Features**: Expand the car inventory system
3. **Deploy**: Consider deploying to a cloud platform
4. **Database Backup**: Implement regular database backups

## Support

The application is fully functional with:
- Database connectivity ✅
- User authentication ✅
- Password reset system ✅
- Enhanced UI/UX ✅
- Mobile responsiveness ✅

Your CarHub application is ready for use and further development!
