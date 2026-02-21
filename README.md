# 🚗 CarHub - Premium Automotive Web Application

## 📋 Table of Contents
1. [Overview](#-overview)
2. [Features](#-features)
3. [Demo Accounts](#-demo-accounts)
4. [Installation Guide](#-installation-guide)
5. [Project Structure](#-project-structure)
6. [Tech Stack](#-tech-stack)
7. [Configuration](#-configuration)
8. [Authentication](#-authentication)
9. [Order Management](#-order-management)
10. [Payment System](#-payment-system)
11. [AI Chatbot](#-ai-chatbot)
12. [Troubleshooting](#-troubleshooting)
13. [Developer Documentation](#-developer-documentation)
14. [Development Workflow](#-development-workflow)
15. [Future Roadmap](#-future-roadmap)

## 🚀 Overview

CarHub is a comprehensive automotive platform built with Flask that combines a beautiful UI with powerful functionality. The application offers a complete solution for car dealerships with features like user authentication, inventory management, order processing, payment integration, and AI-powered customer support.

### Core Features

✅ **Premium UI/UX with Video Backgrounds**
✅ **User Authentication with Email & Google OAuth**
✅ **Complete Database Integration**
✅ **AI-Powered Chatbot Assistant**
✅ **Order Management & Invoicing**
✅ **Payment Processing**
✅ **Admin Panel**
✅ **3D Car Models**

## 🌟 Features

### Authentication System
- **Multi-method Authentication**: Email/password and Google OAuth
- **User Registration**: Email validation and verification
- **Password Management**: Secure reset via email
- **Profile Management**: User dashboards and settings

### Premium UI Experience
- **Dynamic Video Backgrounds**: Luxury car videos on key pages
- **3D Car Models**: Interactive 3D models for vehicle exploration
- **Responsive Design**: Mobile-friendly on all pages
- **Space-themed Design**: Modern dark UI with premium feel

### Product Catalog
- **Vehicle Showcase**: Comprehensive car listings with filters
- **Detailed Views**: Complete vehicle specifications
- **3D Models**: Interactive 3D vehicle exploration
- **Video Gallery**: High-quality car videos

### Order Management
- **Shopping Cart**: Add and manage vehicle selections
- **Order Tracking**: Real-time order status updates
- **PDF Invoices**: Generate and download professional invoices
- **Order History**: Complete purchase records
- **Cancellation System**: Order cancellation with fee calculation

### Payment System
- **Multiple Payment Methods**: Credit card, financing options
- **Secure Processing**: PCI-compliant payment forms
- **Payment Confirmation**: Success page with order details
- **Financial Applications**: Vehicle financing options

### AI Assistant
- **Smart Chatbot**: OpenAI-powered virtual assistant
- **Vehicle Recommendations**: Personalized car suggestions
- **FAQ Handling**: Instant answers to common questions
- **Context-aware**: Remembers conversation history
- **User-specific Responses**: Personalized for logged-in users

### Admin Features
- **User Management**: View and edit user accounts
- **Order Oversight**: Monitor all transactions
- **Inventory Control**: Manage vehicle listings
- **Activity Logs**: Track user and system actions

## 👤 Demo Accounts

### Admin Account
- **Email**: admin@carhub.com
- **Password**: admin123

### Test User Account
- **Email**: test@example.com
- **Password**: password123
- **Username**: testuser

## 🛠️ Installation Guide

### Prerequisites

Before starting, ensure you have the following installed:

- Python 3.9+ (recommended 3.11+)
- pip (Python package manager)
- Git
- A text editor or IDE (VSCode recommended)

### Step 1: Clone the Repository
```bash
# Clone the repository
git clone https://github.com/yourusername/carhub.git

# Navigate to the project directory
cd carhub
```

### Step 2: Set Up a Virtual Environment

It's recommended to use a virtual environment to avoid package conflicts.

#### On Windows:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your configuration:
```bash
# Security
SECRET_KEY=your_generated_secret_key

# Email Configuration (Optional - for password reset emails)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Google OAuth Configuration (Optional)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI Configuration (Required for Chatbot)
OPENAI_API_KEY=your-openai-api-key
```

#### Generate a Secret Key:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output to your `.env` file as the SECRET_KEY.

### Step 5: Initialize the Database

The application will automatically create the database on first run, but you can initialize it explicitly:

```bash
python app.py
```

### Step 6: Run the Development Server

```bash
python app.py
```

The application will be available at: http://127.0.0.1:5000

### Step 7: Create an Admin Account (Optional)

You can use the provided test accounts, or create a new admin account:

```bash
# Start Python interactive shell
python

# In the Python shell:
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        username='admin',
        email='your-admin-email@example.com',
        password_hash=generate_password_hash('your-secure-password'),
        role='admin',
        is_verified=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin account created successfully!")

# Exit the Python shell
exit()
```

## 📁 Project Structure

```
carhub1/
├── app.py                  # Main Flask application
├── chatbot.py              # AI chatbot implementation
├── google_auth.py          # Google OAuth integration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── instance/
│   └── carhub.db           # SQLite database (auto-created)
├── static/                 # Static assets
│   ├── style.css           # Main stylesheet
│   ├── theme.css           # Theme styling
│   ├── *.glb               # 3D car models
│   ├── *.mp4               # Video backgrounds
│   └── logo.png            # Site logo
└── templates/              # HTML templates
    ├── base.html           # Base template with navigation
    ├── index.html          # Homepage
    ├── login.html          # Authentication pages
    ├── cars.html           # Vehicle catalog
    └── ...                 # Other page templates
```

## 💻 Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite
- **Authentication**: Flask-Login, Google OAuth
- **Email**: Flask-Mail
- **Forms**: Flask-WTF
- **AI Integration**: OpenAI API
- **3D Rendering**: Three.js
- **PDF Generation**: ReportLab

## ⚙️ Configuration

### Email Configuration
For password reset functionality, configure your email settings in `.env`:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

For Gmail, use an App Password (requires 2FA enabled).

### Google OAuth Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Identity API
3. Create OAuth credentials (Web application)
4. Add authorized origins and redirect URIs:
   - http://localhost:5000
   - http://127.0.0.1:5000
   - http://localhost:5000/auth/google
   - http://127.0.0.1:5000/auth/google
5. Add credentials to `.env`:
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### OpenAI Configuration
For AI chatbot functionality:

```bash
OPENAI_API_KEY=your-openai-api-key
```

Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys).

## 🔐 Authentication

The application offers dual authentication methods:

### Email/Password Authentication
- User registration with email validation
- Secure password storage (Werkzeug hashing)
- Password reset via email
- Remember-me functionality

### Google OAuth Integration
- One-click sign in with Google
- Automatic account creation for new users
- Profile picture integration
- Email verification through Google

## 📊 Order Management

### Order Lifecycle
1. User selects a vehicle
2. Completes payment form
3. Order is created with "pending" status
4. Upon payment, status changes to "completed"
5. User can view order in dashboard
6. PDF invoice can be downloaded

### Order Cancellation
- Available for pending orders
- 20% cancellation fee (minimum $500)
- Cancellation logged in activity records
- Status updated to "cancelled"

## 💳 Payment System

### Payment Methods
- Credit/Debit Card
- Financing Application

### Payment Processing
- Secure form with validation
- Order creation and status tracking
- Success confirmation page
- Email notification (when configured)

## 🤖 AI Chatbot

### Features
- **Advanced AI**: OpenAI-powered conversational assistant
- **Floating Interface**: Available on all pages
- **Knowledge Base**: Complete CarHub information
- **Personalization**: User-specific responses
- **Car Recommendations**: Suggests vehicles based on preferences
- **Quick Actions**: Common query shortcuts

### Activation
The chatbot can run in two modes:

#### Fallback Mode (No API Key)
Works immediately with predefined responses

#### Full AI Mode
Requires OpenAI API key in `.env` file

## 🔧 Troubleshooting

### Common Issues

#### Authentication Problems
- Ensure `.env` contains valid SECRET_KEY
- For Google OAuth, verify credentials and authorized domains
- Check email configuration for password reset functionality

#### Email Configuration
- For Gmail, use App Password (not regular password)
- Enable 2FA on your Google account
- Verify SMTP settings for your email provider

#### OpenAI API Issues
- Verify API key format and validity
- Check for sufficient credits in OpenAI account
- Test the chatbot functionality directly through the interface

#### Database Problems
- Ensure instance directory exists and is writable
- If database errors occur, try deleting the database file and restarting:
  ```bash
  rm instance/carhub.db
  python app.py
  ```

#### Import Errors
- Verify that all packages are installed:
  ```bash
  pip install -r requirements.txt
  ```
- Check Python version compatibility

#### Google OAuth Problems
- Verify credentials and authorized domains
- Check for typos in client ID and secret

### Getting Help

If you encounter issues:
1. Check the Flask terminal output for errors
2. Look in the browser console for frontend issues
3. Verify all environment variables are set correctly
4. Consult the CarHub development team

---

## � Developer Documentation

### Project Architecture

#### Core Components

1. **Flask Web Application (`app.py`)**
   - Main application entry point
   - Route definitions and handlers
   - User authentication logic
   - Database models
   - Form validation

2. **AI Chatbot (`chatbot.py`)**
   - OpenAI integration
   - Knowledge base management
   - Conversational logic
   - Car recommendation engine

3. **Authentication (`google_auth.py`)**
   - Google OAuth integration
   - User account management

4. **Database (`instance/carhub.db`)**
   - SQLite database with SQLAlchemy ORM
   - User, Car, Order, and other models

5. **Templates (`templates/`)**
   - HTML templates with Jinja2 templating
   - Modular components

6. **Static Assets (`static/`)**
   - CSS styling
   - JavaScript functionality
   - Media files (videos, 3D models)

### Database Schema

#### User Model
- id (Primary Key)
- username
- email (Unique)
- password_hash
- google_id (Optional)
- profile_picture (Optional)
- is_verified (Boolean)
- role (admin/user)
- Other profile fields

#### Car Model
- id (Primary Key)
- name
- brand
- model
- year
- price
- category
- description
- image_path
- model_path (3D model)
- video_path

#### Order Model
- id (Primary Key)
- user_id (Foreign Key)
- car_id (Foreign Key)
- status (pending/completed/cancelled)
- price
- payment_method
- created_at
- cancellation_fee (Optional)

#### Other Models
- FinanceApplication
- UserActivity
- Parts
- Reviews

### Route Structure

#### Main Pages
- `/` - Homepage
- `/cars` - Car listing
- `/about` - About page
- `/services` - Services page
- `/contact` - Contact page
- `/inventory` - Inventory page

#### Authentication
- `/login` - User login
- `/sign_up` - User registration
- `/logout` - User logout
- `/forgot_password` - Password recovery
- `/reset_password/<token>` - Password reset
- `/auth/google` - Google OAuth

#### Car Details
- `/car-details/<car_name>` - Detailed car view
- `/part-details/<part_id>` - Detailed part view
- `/product-details/<product_id>` - Product details

#### User Dashboard
- `/profile` - User profile
- `/dashboard` - User dashboard
- `/edit_profile` - Edit user profile
- `/my_orders` - User orders

#### Payment & Checkout
- `/buy/<car_name>` - Initiate purchase
- `/payment` - Payment processing
- `/payment-success/<int:order_id>` - Payment confirmation
- `/finance` - Financing application
- `/finance-success/<int:application_id>` - Finance approval
- `/download-invoice/<int:order_id>` - Invoice PDF generation

#### Admin Routes
- `/admin_panel` - Admin dashboard
- `/admin_users` - User management
- `/admin_orders` - Order management
- `/admin_activities` - Activity logs

#### API Endpoints
- `/api/chat` - Chatbot conversation
- `/api/chat/recommendations` - Car recommendations
- `/api/chat/car-details/<car_name>` - Car information

### Implementation Details

#### Authentication System
- Password hashing with Werkzeug
- Login session management with Flask-Login
- Password reset via secure tokens
- Google OAuth integration with google-auth

#### Email System
- Flask-Mail integration
- HTML email templates
- Token-based verification
- Error handling

#### Order Processing
- Multi-step checkout flow
- Status tracking
- Cancellation logic with fee calculation
- PDF invoice generation with ReportLab

#### AI Chatbot
- OpenAI API integration
- Context-aware conversations
- Fallback responses when API unavailable
- User-specific personalization

#### 3D Model Rendering
- Three.js integration
- GLB model format
- Camera controls and lighting
- Mobile optimization

### Security Measures

#### Authentication Security
- Password hashing
- CSRF protection
- Secure session cookies
- OAuth token validation

#### Data Protection
- Input validation and sanitization
- SQL injection prevention via ORM
- XSS protection
- Sensitive data encryption

#### Access Control
- Role-based permissions
- Route protection with login_required
- User ownership validation

### Frontend Architecture

#### CSS Structure
- Base styling (`style.css`)
- Theme components (`theme.css`)
- Responsive design
- Dark mode support

#### JavaScript Components
- Form validation
- 3D model viewer
- Chatbot interface
- Theme toggling

#### Media Management
- Video backgrounds
- 3D models
- Responsive images
- Lazy loading

## 🛠️ Development Workflow

### Local Setup
1. Clone repository
2. Install dependencies
3. Configure environment variables
4. Initialize database
5. Start development server

### Running Tests
```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest tests/test_authentication.py
```

### Code Style
Follow PEP 8 guidelines for Python code. Consider using linters:

```bash
# Install flake8
pip install flake8

# Run flake8
flake8 .
```

### Making Changes
1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 🚀 Future Roadmap

### Planned Features
- Payment gateway integration
- Multi-language support
- Enhanced admin analytics
- Mobile app integration

### Technical Improvements
- Migration to PostgreSQL
- API rate limiting
- Front-end framework integration
- Containerization with Docker

### Performance Enhancements
- Image optimization pipeline
- Server-side rendering
- Database indexing
- Query optimization

## 📝 License

© 2025 CarHub. All rights reserved.

---

**CarHub** - Your Premium Automotive Experience 🚗✨
=======
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
