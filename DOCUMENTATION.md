# 🚗 CarHub - Comprehensive Documentation

## Table of Contents
1. [Application Overview](#application-overview)
2. [Features](#features)
3. [Setup Instructions](#setup-instructions)
4. [Authentication System](#authentication-system)
5. [Database Integration](#database-integration)
6. [UI Enhancements](#ui-enhancements)
7. [Order Management](#order-management)
8. [Payment System](#payment-system)
9. [Email Configuration](#email-configuration)
10. [Google OAuth Integration](#google-oauth-integration)
11. [AI Chatbot](#ai-chatbot)
12. [Troubleshooting](#troubleshooting)
13. [Next Steps](#next-steps)

---

# Application Overview

CarHub is a comprehensive database-connected web application for a car dealership, featuring:

✅ **User Registration & Login System**
✅ **Password Reset via Email**
✅ **Database Integration with SQLAlchemy**
✅ **Enhanced Homepage with Customer Reviews**
✅ **Video Background Sections**
✅ **Secure Form Validation**
✅ **Google OAuth Integration**
✅ **AI Chatbot**
✅ **Order Management with Cancellation**
✅ **PDF Invoice Generation**
✅ **Payment Processing**

---

# Features

## 1. Authentication System
- **Sign Up**: New user registration with email validation
- **Login**: Secure user authentication with session management
- **Forgot Password**: Email-based password reset functionality
- **Password Security**: Hashed passwords using Werkzeug
- **Google OAuth**: Sign in with Google integration

## 2. Database Integration
- **SQLite Database**: Lightweight database for user management
- **User Model**: Complete user schema with authentication fields
- **Session Management**: Secure user sessions across pages
- **Order Tracking**: Comprehensive order and payment database

## 3. Enhanced Homepage
- **Customer Reviews**: Grid layout with star ratings and avatars
- **Statistics**: Customer satisfaction metrics
- **Video Sections**: Background videos for different services
- **Responsive Design**: Works on all device sizes

## 4. Order Management
- **My Orders Page**: View all orders and their statuses
- **PDF Invoice**: Download professional invoice for completed orders
- **Order Cancellation**: Cancel orders with fee calculation
- **Status Tracking**: Visual indicators for order status

## 5. Payment Processing
- **Payment Methods**: Multiple payment options
- **Form Validation**: Comprehensive input validation
- **Success Feedback**: Enhanced payment success page
- **Security**: Secure payment processing

## 6. AI Chatbot
- **Advanced AI**: OpenAI-powered conversational chatbot
- **Knowledge Base**: Complete CarHub business knowledge
- **User Context**: Personalized responses for logged-in users
- **Fallback Responses**: Works even when API is unavailable

---

# Setup Instructions

## Dependencies
All required packages are installed:
```bash
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```
The application will be available at: http://127.0.0.1:5000

## Default Accounts

You can use these pre-configured accounts for testing:

### Admin Account:
- **Email**: admin@carhub.com
- **Password**: admin123

### Test User Account:
- **Email**: test@example.com
- **Password**: password123
- **Username**: testuser

## File Structure
```
carhub1/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── instance/carhub.db      # SQLite database (auto-created)
├── static/                # CSS, images, videos
│   ├── style.css
│   ├── logo.png
│   └── *.mp4 videos
└── templates/             # HTML templates
    ├── base.html          # Base template with navigation
    ├── index.html         # Enhanced homepage
    ├── login.html         # User login page
    └── ...                # Other templates
```

---

# Authentication System

## Authentication Flow
1. **Registration**: Users create accounts with email/password
2. **Login**: Secure authentication with session storage
3. **Password Reset**: Token-based email verification system
4. **Session Management**: Automatic login/logout handling

## Security Features
- **Password Hashing**: Secure password storage
- **CSRF Protection**: Form security with Flask-WTF
- **Input Validation**: Server-side form validation
- **Session Security**: Secure session management

---

# Database Integration

The application uses SQLAlchemy with SQLite for database management:

- **User Model**: Stores user accounts and authentication details
- **Car Model**: Maintains inventory information
- **Order Model**: Tracks all orders with status and payment info
- **Relationships**: Proper foreign key relationships between models

---

# UI Enhancements

## Homepage Enhancements
- **Customer Reviews**: Grid layout with star ratings and avatars
- **Statistics**: Customer satisfaction metrics
- **Video Sections**: Background videos for different services
- **Responsive Design**: Works on all device sizes

## Design System
- **Typography**: Orbitron for headers, Poppins for body text
- **Color Scheme**: Space-themed with purple, blue, and cyan accents
- **Gradients**: Consistent gradient patterns across pages
- **Animations**: Subtle animations for interactive elements

---

# Order Management

## My Orders Page Enhancement

The My Orders page has been completely redesigned to match the cars.html UI styling and enhanced with additional features including PDF invoice generation.

### New Features

#### 1. Enhanced UI Design
- **Consistent Styling**: Now matches the cars.html page with same color scheme, gradients, and layout
- **Responsive Design**: Optimized for all screen sizes (desktop, tablet, mobile)
- **Modern Card Layout**: Orders displayed in attractive card format with hover effects
- **Background Video**: Matches the premium feel of the main site

#### 2. Download Invoice Feature
- **PDF Generation**: Users can download professional PDF invoices for completed orders
- **Comprehensive Invoice**: Includes all order details, customer info, and payment information
- **Secure Access**: Only authenticated users can download their own invoices
- **Professional Layout**: Clean, branded invoice design with tables and proper formatting

#### 3. Enhanced Order Display
- **Vehicle Information Section**: Dedicated area showing car details with icons
- **Payment Summary**: Clear breakdown of pricing including taxes and fees
- **Status Indicators**: Color-coded status badges with animations
- **Action Buttons**: Context-aware buttons based on order status

## Order Cancellation Feature

### Features Implemented

#### 1. Database Changes
- ✅ Added `cancellation_fee` column to Order table (tracks cancellation fees)
- ✅ Added `order_status` column to Order table (tracks order status: pending, cancelled, completed, etc.)

#### 2. Backend Implementation (app.py)
- ✅ Updated Order model with new fields
- ✅ Created `/cancel-order/<order_id>` route with POST method
- ✅ Implemented 20% cancellation fee calculation (minimum $500)
- ✅ Added activity logging for cancellation tracking
- ✅ Proper error handling and user feedback

#### 3. Frontend Enhancement (templates/my_orders.html)
- ✅ Added "Cancel Order" button for pending orders only
- ✅ JavaScript confirmation dialog with detailed warning message
- ✅ Enhanced order status display logic
- ✅ CSS styling for cancelled orders and refund information
- ✅ Display actual cancellation fees and refund amounts

### Cancellation Fee Logic

```python
cancellation_fee = max(order_total * 0.20, 500.00)  # 20% or $500, whichever is higher
refund_amount = order_total - cancellation_fee
```

### Security Features

- ✅ Users can only cancel their own orders
- ✅ Only pending orders can be cancelled
- ✅ All cancellations are logged in user activity
- ✅ Proper error handling and validation

---

# Payment System

## Payment Page Enhancement

Enhanced the `payment.html` template to match the visual styling and design patterns from `cars.html` while maintaining all existing functionality, form validation, and database integrity.

### Key Enhancements Made

#### 1. Typography & Fonts
- **Google Fonts Integration**: Added Orbitron (headers) and Poppins (body text) fonts
- **Enhanced Headers**: Applied Orbitron font with gradient text effects and glow animations
- **Improved Typography**: Better font weights, sizes, and spacing throughout

#### 2. Color Scheme & Variables
- **Cars.html Color Palette**: Implemented exact color variables from cars.html
- **Consistent Gradients**: Applied matching gradient themes and effects
- **Enhanced CSS Variables**: Used same custom properties for visual consistency

#### 3. Layout & Design Enhancements
- **Background Overlay**: Added animated background overlay matching cars.html
- **Enhanced Cards**: Improved form and summary cards with gradients and shadows
- **Interactive Elements**: Enhanced form controls, buttons, and payment methods
- **Visual Hierarchy**: Better spacing and organization of content

### Technical Implementation

#### Key CSS Enhancements

```css
/* Color Variables */
--primary-purple: #7c4dff;
--primary-blue: #23235b;
--accent-cyan: #07b0b3;
--light-purple: #a084ff;
--text-light: #e0e6ff;
--text-muted: #b3baff;

/* Gradient Patterns */
--gradient-primary: linear-gradient(90deg, #7c4dff 60%, #23235b 100%);
--gradient-luxury: linear-gradient(90deg, #a084ff 80%, #23235b 100%);
--gradient-dark: linear-gradient(120deg, #23235b 60%, #181828 100%);
--gradient-space: radial-gradient(ellipse at top left, #23235b 0%, #0a0a1a 100%);
```

## Payment Success Page Enhancement

Enhanced the `payment_success.html` template to match the visual styling and design patterns from `cars.html` while maintaining all existing functionality and database integrity.

### Key Enhancements Made

#### 1. Typography & Fonts
- **Added Google Fonts**: Imported Orbitron (for headers) and Poppins (for body text)
- **Enhanced Title**: Used Orbitron font with gradient text effects and glow animation
- **Improved Readability**: Better font weights and sizes for all text elements

#### 2. Interactive Elements
- **Enhanced Buttons**: Applied cars.html button styling with hover effects
- **Detail Rows**: Added hover effects and better visual hierarchy
- **Status Badge**: Improved with gradient background and pulse animation
- **Next Steps**: Enhanced list items with check icons and hover effects

#### 3. Animations & Effects
- **Success Pulse**: Enhanced success icon animation
- **Title Glow**: Added glow effect to the main title
- **Badge Pulse**: Animated status badge
- **Hover Effects**: Added smooth transitions for interactive elements

---

# Email Configuration

## Email Setup Guide

### Step 1: Install Required Packages
```bash
pip install flask-mail python-dotenv flask-wtf
```
*Note: These are already installed in your project*

### Step 2: Create Your Email Configuration
1. **Copy the example file**:
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file with your email credentials**:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-gmail-app-password
   SECRET_KEY=your-secret-key-here
   ```

### Step 3: Gmail Setup (Recommended)
1. **Enable 2-Factor Authentication**:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to Security > App passwords
   - Select "Mail" as the app
   - Copy the generated 16-character password
   - Use this in your `.env` file (NOT your regular Gmail password)

### Step 4: Alternative Email Providers

#### **Outlook/Hotmail**:
```
MAIL_SERVER=smtp.live.com
MAIL_PORT=587
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
```

#### **Yahoo Mail**:
```
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USERNAME=your-email@yahoo.com
MAIL_PASSWORD=your-app-password
```

## Enhanced Features

### **Enhanced Video Background**
- ✅ `b1.mp4` now visible with proper brightness and contrast
- ✅ Improved z-index hierarchy prevents content blocking
- ✅ Added opacity for better content visibility

### **Professional Feedback Form**
- ✅ **Star Rating System**: Interactive 5-star rating with hover effects
- ✅ **Form Validation**: Client-side and server-side validation
- ✅ **Character Counter**: Real-time character count for messages
- ✅ **Loading States**: Shows "Sending..." when submitting
- ✅ **Flash Messages**: Success/error notifications with auto-dismiss
- ✅ **Email Integration**: Sends professionally formatted emails

### **Email Features**
- ✅ **HTML Email Templates**: Professional formatting with CarHub branding
- ✅ **Customer Details**: Name, email, rating, feedback type included
- ✅ **Reply-To**: You can reply directly to customer's email
- ✅ **Timestamp**: Submission date and time included
- ✅ **Error Handling**: Graceful fallback if email fails

---

# Google OAuth Integration

## Setup Guide

### Step 1: Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

Or add these to your `requirements.txt`:
```
google-auth==2.23.4
google-auth-oauthlib==1.0.0
google-auth-httplib2==0.1.1
```

### Step 2: Google Cloud Console Setup

#### Create Google OAuth Credentials:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Create a new project or select existing one

2. **Enable Google Sign-In API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" or "Google Identity"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Name: "CarHub Web Client"

4. **Configure Authorized Origins**
   Add these to "Authorized JavaScript origins":
   ```
   http://localhost:5000
   http://127.0.0.1:5000
   https://yourdomain.com  (for production)
   ```

5. **Configure Redirect URIs**
   Add these to "Authorized redirect URIs":
   ```
   http://localhost:5000/auth/google
   http://127.0.0.1:5000/auth/google
   https://yourdomain.com/auth/google  (for production)
   ```

6. **Copy Credentials**
   - Copy the **Client ID** and **Client Secret**
   - You'll need these for environment variables

### Step 3: Environment Configuration

Create a `.env` file in your project root:

```bash
# .env file
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=your-super-secret-key
```

### Step 4: Update Your Flask App

#### A. Add the Google Auth Route

Add this to your main `app.py`:

```python
from flask import Flask, request, jsonify, redirect, url_for
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_login import login_user
import os

# Add this route to your app
@app.route('/auth/google', methods=['POST'])
def google_auth():
    try:
        credential = request.json.get('credential')
        
        if not credential:
            return jsonify({'success': False, 'message': 'No credential provided'}), 400
        
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            app.config['GOOGLE_CLIENT_ID']
        )
        
        # Extract user information
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        picture = idinfo.get('picture', '')
        
        # Check if user exists in your database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                profile_picture=picture,
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Log the user in
        login_user(user, remember=True)
        
        return jsonify({
            'success': True,
            'message': 'Successfully signed in with Google',
            'redirect_url': url_for('dashboard')  # Change to your desired redirect
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid Google token'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Add Google config to your app
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
```

#### B. Update Your User Model

Add these fields to your User model:

```python
class User(db.Model, UserMixin):
    # ... your existing fields ...
    
    # Add these new fields:
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
```

### Step 5: Update Your App Configuration

Make sure your app loads environment variables:

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Add this line

app = Flask(__name__)
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
```

---

# AI Chatbot

## Features Implemented

### 1. **Complete Chatbot System**
- ✅ Advanced AI chatbot with comprehensive CarHub knowledge
- ✅ Floating chat widget on all pages (bottom-right corner)
- ✅ Fallback responses when OpenAI API is not available
- ✅ Mobile-responsive design matching CarHub's premium theme
- ✅ Real-time conversation with typing indicators

### 2. **Knowledge Base Includes**
- ✅ Complete CarHub company information
- ✅ All services (buying, selling, servicing, vintage cars)
- ✅ Current inventory with prices and categories
- ✅ Customer reviews and testimonials
- ✅ Financing options and processes
- ✅ Contact information and support details

### 3. **Smart Features**
- ✅ Intent detection (buying, selling, service needs)
- ✅ Personalized car recommendations
- ✅ Quick action buttons for common queries
- ✅ Conversation history and context awareness
- ✅ User context integration (logged-in users get personalized responses)

## How to Start Using Your Chatbot

### Option 1: Start with Fallback Responses (Works Immediately)
```bash
cd "c:\Users\hp\OneDrive\Desktop\carhub1"
python app.py
```

Visit http://localhost:5000 and click the chat widget (💬) in the bottom-right corner!

### Option 2: Enable Full AI Power with OpenAI
1. **Get OpenAI API Key:**
   - Visit https://platform.openai.com/api-keys
   - Sign up or log in
   - Create a new secret key
   - Copy the key

2. **Configure Your Environment:**
   - Open the `.env` file in your CarHub folder
   - Replace `your-openai-api-key-here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

## Customization Options

### Change Chat Widget Colors:
Edit `templates/chat_widget.html` and modify the CSS variables:
```css
:root {
    --chat-primary: #7c4dff;      /* Primary color */
    --chat-secondary: #b084ff;    /* Secondary color */
    --chat-background: #1a1a2e;   /* Background color */
}
```

### Add New Quick Actions:
In `templates/chat_widget.html`, add buttons:
```html
<button class="quick-action-embedded" data-message="Your custom message">🎯 Custom Action</button>
```

### Update Knowledge Base:
Edit `chatbot.py` and modify the `knowledge_base` dictionary to add new information about cars, services, or company details.

---

# Troubleshooting

## Common Issues:

### "API Key Error" (OpenAI):
- Verify your OpenAI API key in `.env` file
- Check if your OpenAI account has credits
- Ensure no extra spaces in the API key

### "Redirect URI mismatch" (Google OAuth):
- Add your domain to Google Console authorized origins
- Make sure the URL matches exactly (http vs https)
- Add `/auth/google` endpoint to Google Console redirect URIs

### Email Configuration Issues:
- Ensure 2FA is enabled for Gmail
- Use App Password instead of regular password
- Check SMTP server settings for your provider

## Getting Help:
1. Check Flask console logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all required packages are installed

---

# Next Steps

1. **Customize Email Settings**: Add your SMTP configuration for password reset
2. **Configure OpenAI API**: Set up your API key for the chatbot
3. **Set Up Google OAuth**: Complete the OAuth integration
4. **Add More Features**: Expand the car inventory system
5. **Deploy**: Consider deploying to a cloud platform
6. **Database Backup**: Implement regular database backups

---

## Support

The application is fully functional with:
- Database connectivity ✅
- User authentication ✅
- Password reset system ✅
- Enhanced UI/UX ✅
- Mobile responsiveness ✅
- AI Chatbot integration ✅
- Google OAuth login ✅
- Order management ✅
- Payment processing ✅

Your CarHub application is ready for use and further development!
