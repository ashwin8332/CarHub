from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField, FileField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError, Optional
from flask_wtf.file import FileField, FileAllowed
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import secrets
import os
import json
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv

# Google OAuth imports
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

# Load environment variables
load_dotenv()

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration (using environment variables)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME', 'your-email@gmail.com'))

# Google OAuth configuration
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/profiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Make nullable for Google users
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)
    
    # Enhanced profile fields
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    preferred_contact_method = db.Column(db.String(20), default='email')
    profile_updated_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_google_user(self):
        return self.google_id is not None
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        fields = [
            self.first_name, self.last_name, self.phone, self.date_of_birth,
            self.gender, self.address, self.city, self.state, self.zip_code,
            self.country, self.occupation, self.bio
        ]
        completed_fields = sum(1 for field in fields if field)
        return int((completed_fields / len(fields)) * 100)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def __repr__(self):
        return f'<User {self.username}>'

# Payment and Order Models
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Car {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    cancellation_fee = db.Column(db.Float, default=0.0)  # Track cancellation fees
    payment_status = db.Column(db.String(20), default='pending')
    order_status = db.Column(db.String(20), default='pending')  # Track order status
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    billing_name = db.Column(db.String(100), nullable=False)
    billing_email = db.Column(db.String(120), nullable=False)
    billing_phone = db.Column(db.String(20), nullable=False)
    billing_address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    car = db.relationship('Car', backref=db.backref('orders', lazy=True))

    def __repr__(self):
        return f'<Order {self.id}>'

class FinanceApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.String(50))  # Can be string since it comes from URL params
    car_name = db.Column(db.String(200), nullable=False)
    car_price = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    annual_income = db.Column(db.String(50), nullable=False)
    employment_status = db.Column(db.String(50), nullable=False)
    credit_score_range = db.Column(db.String(50))
    address = db.Column(db.Text, nullable=False)
    selected_plan = db.Column(db.String(50), nullable=False)
    application_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('finance_applications', lazy=True))

    def __repr__(self):
        return f'<FinanceApplication {self.id}>'

class UserActivity(db.Model):
    __tablename__ = 'user_activity_log'  # Explicit table name to avoid conflicts
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # login, logout, view_car, order_placed, etc.
    description = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    activity_data = db.Column(db.Text, nullable=True)  # JSON string for additional data (changed from metadata)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy=True, order_by='UserActivity.created_at.desc()'))

    def __repr__(self):
        return f'<UserActivity {self.activity_type} by {self.user_id}>'

class PartOrder(db.Model):
    __tablename__ = 'part_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    part_id = db.Column(db.String(50), nullable=False)  # e.g., 'turbo-001'
    part_name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    order_status = db.Column(db.String(20), default='processing')  # processing, shipped, delivered, cancelled
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    billing_name = db.Column(db.String(100), nullable=False)
    billing_email = db.Column(db.String(120), nullable=False)
    billing_phone = db.Column(db.String(20), nullable=False)
    billing_address = db.Column(db.Text, nullable=False)
    shipping_address = db.Column(db.Text, nullable=True)  # Can be different from billing
    tracking_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('part_orders', lazy=True))

    def __repr__(self):
        return f'<PartOrder {self.id} - {self.part_name}>'

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[
        InputRequired(), 
        Length(min=4, max=20, message="Username must be between 4 and 20 characters")
    ])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[
        InputRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        InputRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        InputRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password2 = PasswordField('Confirm New Password', validators=[
        InputRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

class PaymentForm(FlaskForm):
    billing_name = StringField('Full Name', validators=[
        InputRequired(),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    billing_email = StringField('Email', validators=[InputRequired(), Email()])
    billing_phone = StringField('Phone Number', validators=[
        InputRequired(),
        Length(min=10, max=20, message="Please enter a valid phone number")
    ])
    billing_address = StringField('Address', validators=[
        InputRequired(),
        Length(min=10, max=500, message="Please enter a complete address")
    ])
    payment_method = StringField('Payment Method', validators=[InputRequired()])
    card_number = StringField('Card Number')
    card_expiry = StringField('Expiry Date (MM/YY)')
    card_cvv = StringField('CVV')
    submit = SubmitField('Complete Payment')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        InputRequired(), 
        Length(min=4, max=20, message="Username must be between 4 and 20 characters")
    ])
    email = StringField('Email Address', validators=[Optional()], render_kw={'readonly': True})
    profile_picture = FileField('Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    zip_code = StringField('ZIP Code', validators=[Optional(), Length(max=20)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])
    occupation = StringField('Occupation', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=1000)])
    preferred_contact_method = SelectField('Preferred Contact Method', choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Both')
    ], validators=[Optional()])
    submit = SubmitField('Update Profile')
    
    def validate_username(self, username):
        # Only validate if username has changed
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already exists. Please choose a different one.')

# Helper functions
def log_user_activity(user_id, activity_type, description, metadata=None):
    """Log user activity"""
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '') if request else None,
            activity_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def is_admin(user):
    """Check if user is admin"""
    return user and user.is_authenticated and user.email == 'admin@carhub.com'

def send_email(subject, recipient, template, **kwargs):
    """Send email using Flask-Mail"""
    try:
        msg = Message(subject, recipients=[recipient])
        msg.html = template
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def generate_reset_token(email):
    """Generate password reset token"""
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    """Verify password reset token"""
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Login user with Flask-Login
            login_user(user, remember=form.remember_me.data)
            
            # Log login activity
            log_user_activity(user.id, 'login', f'User {user.username} logged in successfully')
            
            flash('Welcome back! You have been logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            # Log failed login attempt
            if user:
                log_user_activity(user.id, 'login_failed', f'Failed login attempt for user {user.username}')
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/auth/google', methods=['POST'])
def google_auth():
    """Handle Google OAuth authentication"""
    if not GOOGLE_AUTH_AVAILABLE:
        return jsonify({'success': False, 'message': 'Google OAuth is not available'}), 500
    
    try:
        # Get the credential from the request
        data = request.get_json()
        credential = data.get('credential') if data else None
        
        if not credential:
            return jsonify({'success': False, 'message': 'No credential provided'}), 400
        
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credential, 
            google_requests.Request(), 
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
            # Create new user with Google info
            # Generate a username from email
            username = email.split('@')[0]
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                profile_picture=picture,
                is_verified=True  # Google accounts are pre-verified
            )
            db.session.add(user)
        else:
            # Update existing user with Google info
            if not user.google_id:
                user.google_id = google_id
            user.profile_picture = picture
            user.is_verified = True
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log the user in
        login_user(user, remember=True)
        
        return jsonify({
            'success': True,
            'message': 'Successfully signed in with Google',
            'redirect_url': url_for('dashboard')
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid Google token: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Authentication failed: {str(e)}'}), 500

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SignUpForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
        else:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            try:
                db.session.add(user)
                db.session.commit()
                
                flash('Account created successfully! You can now log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while creating your account. Please try again.', 'error')
    
    return render_template('sign_up.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Generate reset token
            token = generate_reset_token(user.email)
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Email template
            email_template = f'''
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #7c4dff; text-align: center;">CarHub Password Reset</h2>
                    <p>Hello {user.username},</p>
                    <p>You have requested to reset your password. Click the link below to reset your password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #7c4dff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                    </div>
                    <p><strong>Note:</strong> This link will expire in 1 hour.</p>
                    <p>If you didn't request this reset, please ignore this email.</p>
                    <p>Best regards,<br>CarHub Team</p>
                </div>
            </body>
            </html>
            '''
            
            if send_email('CarHub - Password Reset Request', user.email, email_template):
                flash('Password reset link has been sent to your email.', 'info')
            else:
                flash('Error sending email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid reset token.', 'error')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

@app.route('/logout')
@login_required
def logout():
    # Log logout activity before logging out
    log_user_activity(current_user.id, 'logout', f'User {current_user.username} logged out')
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/cars')
def cars():
    return render_template('cars.html')

@app.route('/video')
def video():
    return render_template('video_gallery.html')

@app.route('/about', methods=['GET', 'POST'])
def about():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            rating = request.form.get('rating')
            feedback_type = request.form.get('feedback-type')
            message = request.form.get('message')
            
            # Validate required fields
            if not all([name, email, rating, feedback_type, message]):
                flash('Please fill in all required fields.', 'error')
                return render_template('about.html')
            
            # Create email message
            subject = f"New Feedback from {name} - CarHub"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #7c4dff; text-align: center;">New Feedback from CarHub</h2>
                    <hr style="border-color: #7c4dff;">
                    
                    <p><strong>Customer Details:</strong></p>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 5px 0;"><strong>Name:</strong> {name}</li>
                        <li style="padding: 5px 0;"><strong>Email:</strong> {email}</li>
                        <li style="padding: 5px 0;"><strong>Rating:</strong> {rating}/5 ⭐</li>
                        <li style="padding: 5px 0;"><strong>Feedback Type:</strong> {feedback_type.title()}</li>
                    </ul>
                    
                    <p><strong>Message:</strong></p>
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        {message}
                    </div>
                    
                    <hr style="border-color: #ddd;">
                    <p style="color: #666; font-size: 0.9em; text-align: center;">
                        Submitted on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            try:
                msg = Message(
                    subject=subject,
                    recipients=[app.config['MAIL_USERNAME']],  # Send to configured email
                    html=html_body,
                    reply_to=email
                )
                mail.send(msg)
                print(f"Email sent successfully to {app.config['MAIL_USERNAME']}")
            except Exception as email_error:
                print(f"Email sending failed: {email_error}")
                # Continue without failing the form submission
                pass
            
            flash('Thank you for your feedback! We\'ll get back to you soon.', 'success')
            return redirect(url_for('about'))
            
        except Exception as e:
            flash('Sorry, there was an error sending your feedback. Please try again.', 'error')
            print(f"Email error: {e}")
    
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')
        newsletter = request.form.get('newsletter')
        
        # In a real app, you would:
        # 1. Save the message to database
        # 2. Send email notification to admin
        # 3. Send confirmation email to user
        # 4. Add proper validation and error handling
        
        # For now, we'll just flash a success message
        flash('Thank you for your message! We\'ll get back to you within 24 hours.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/inventory')
def inventory():
    # Enhanced car parts inventory data with unique and diverse product names
    inventory_parts = [
        {
            'id': 'turbo-001',
            'name': 'Garrett GT2860RS Turbocharger',
            'category': 'Engine Parts',
            'brand': 'Garrett Motion',
            'part_number': 'GTM-2860RS-001',
            'price': '$2,850',
            'status': 'In Stock',
            'compatibility': 'BMW M3, M4, M5',
            'image': 'parts/turbocharger.jpg',
            'description': 'High-performance ball bearing turbocharger with advanced aerodynamics for maximum efficiency and power output.',
            'warranty': '2 Years',
            'condition': 'New'
        },
        {
            'id': 'brake-002',
            'name': 'Brembo GT Racing Ceramic Pads',
            'category': 'Brake System',
            'brand': 'Brembo',
            'part_number': 'BRM-GTRC-002',
            'price': '$485',
            'status': 'In Stock',
            'compatibility': 'Porsche 911, Cayman',
            'image': 'parts/brake-pads.jpg',
            'description': 'Premium ceramic brake pads designed for track and street performance with minimal dust production.',
            'warranty': '1 Year',
            'condition': 'New'
        },
        {
            'id': 'susp-003',
            'name': 'Bilstein B16 PSS10 Coilovers',
            'category': 'Suspension',
            'brand': 'Bilstein',
            'part_number': 'BIL-B16-PSS10',
            'price': '$1,650',
            'status': 'Low Stock',
            'compatibility': 'Audi A4, A6, S4',
            'image': 'parts/coilover.jpg',
            'description': 'Motorsport-derived coilover suspension system with 10-way adjustable damping.',
            'warranty': '2 Years',
            'condition': 'New'
        },
        {
            'id': 'air-004',
            'name': 'K&N Apollo Cold Air Intake',
            'category': 'Engine Parts',
            'brand': 'K&N Engineering',
            'part_number': 'KN-APOLLO-CAI',
            'price': '$320',
            'status': 'In Stock',
            'compatibility': 'Honda Civic Type R',
            'image': 'parts/air-filter.jpg',
            'description': 'Complete cold air intake system with high-flow filter for increased horsepower and torque.',
            'warranty': '1 Year',
            'condition': 'New'
        },
        {
            'id': 'exh-005',
            'name': 'Akrapovic Evolution Titanium System',
            'category': 'Exhaust',
            'brand': 'Akrapovic',
            'part_number': 'AKR-EVO-TI-V1',
            'price': '$3,200',
            'status': 'Pre-Order',
            'compatibility': 'Lamborghini Huracan',
            'image': 'parts/exhaust-system.jpg',
            'description': 'Full titanium exhaust system with valve control and distinctive Akrapovic sound signature.',
            'warranty': '2 Years',
            'condition': 'New'
        },
        {
            'id': 'trans-006',
            'name': 'ZF 8HP76 Performance Transmission',
            'category': 'Transmission',
            'brand': 'ZF Friedrichshafen',
            'part_number': 'ZF-8HP76-PERF',
            'price': '$8,500',
            'status': 'Out of Stock',
            'compatibility': 'BMW X5, X6, 7 Series',
            'image': 'parts/transmission.jpg',
            'description': 'High-performance 8-speed automatic transmission with sport programming and launch control.',
            'warranty': '3 Years',
            'condition': 'Remanufactured'
        },
        {
            'id': 'ign-007',
            'name': 'NGK Iridium IX Performance Coils',
            'category': 'Electrical',
            'brand': 'NGK Spark Plugs',
            'part_number': 'NGK-IRIX-COIL-SET',
            'price': '$295',
            'status': 'In Stock',
            'compatibility': 'Toyota Supra, Lexus RC F',
            'image': 'parts/ignition-coils.jpg',
            'description': 'Premium iridium ignition coil set for enhanced combustion efficiency and reliability.',
            'warranty': '1 Year',
            'condition': 'New'
        },
        {
            'id': 'hood-008',
            'name': 'Seibon Carbon Fiber Vented Hood',
            'category': 'Body Parts',
            'brand': 'Seibon Carbon',
            'part_number': 'SB-CF-HOOD-GTR',
            'price': '$1,850',
            'status': 'Low Stock',
            'compatibility': 'Nissan GT-R R35',
            'image': 'parts/carbon-hood.jpg',
            'description': 'Lightweight carbon fiber hood with functional heat extraction vents and UV-resistant clear coat.',
            'warranty': '1 Year',
            'condition': 'New'
        },
        {
            'id': 'seat-009',
            'name': 'Recaro Pole Position Racing Seats',
            'category': 'Interior',
            'brand': 'Recaro',
            'part_number': 'REC-POLE-POS-ABE',
            'price': '$2,400',
            'status': 'In Stock',
            'compatibility': 'Universal Fitment',
            'image': 'parts/racing-seats.jpg',
            'description': 'FIA-approved racing seats with advanced side support and premium Dinamica upholstery.',
            'warranty': '2 Years',
            'condition': 'New'
        },
        {
            'id': 'oil-010',
            'name': 'Mobil 1 Extended Performance 0W-20',
            'category': 'Engine Parts',
            'brand': 'Mobil 1',
            'part_number': 'MOB1-EP-0W20-5Q',
            'price': '$85',
            'status': 'In Stock',
            'compatibility': 'Most Modern Engines',
            'image': 'parts/engine-oil.jpg',
            'description': 'Full synthetic motor oil providing up to 20,000 miles of protection with superior thermal stability.',
            'warranty': 'N/A',
            'condition': 'New'
        },
        {
            'id': 'tire-011',
            'name': 'Michelin Pilot Sport Cup 2 R',
            'category': 'Wheels-Tires',
            'brand': 'Michelin',
            'part_number': 'MICH-PSC2R-295',
            'price': '$1,200',
            'status': 'Pre-Order',
            'compatibility': 'Performance Vehicles',
            'image': 'parts/tires.jpg',
            'description': 'Track-focused semi-slick tires with exceptional grip and cornering performance for competitive driving.',
            'warranty': '6 Months',
            'condition': 'New'
        },
        {
            'id': 'fuel-012',
            'name': 'Bosch EV14 High-Flow Injectors',
            'category': 'Engine Parts',
            'brand': 'Bosch',
            'part_number': 'BSH-EV14-1000CC',
            'price': '$650',
            'status': 'Out of Stock',
            'compatibility': 'Mercedes AMG C63',
            'image': 'parts/fuel-injectors.jpg',
            'description': 'High-flow fuel injectors with precision spray pattern for optimized fuel delivery and performance.',
            'warranty': '2 Years',
            'condition': 'New'
        }
    ]
    return render_template('inventory.html', parts=inventory_parts)

@app.route('/part-details/<part_id>')
def part_details(part_id):
    # Log user activity for viewing part details
    if current_user.is_authenticated:
        log_user_activity(
            user_id=current_user.id,
            activity_type='part_view',
            description=f'Viewed part details for {part_id}',
            metadata={'part_id': part_id}
        )
    
    # Enhanced car parts inventory data - matches the inventory route data
    inventory_parts = [
        {
            'id': 'turbo-001',
            'name': 'Garrett GT2860RS Turbocharger',
            'category': 'Engine Parts',
            'brand': 'Garrett Motion',
            'part_number': 'GTM-2860RS-001',
            'price': '$2,850',
            'status': 'In Stock',
            'compatibility': 'BMW M3, M4, M5',
            'image': 'parts/turbocharger.jpg',
            'description': 'High-performance ball bearing turbocharger with advanced aerodynamics for maximum efficiency and power output. Features precision-balanced compressor and turbine wheels.',
            'warranty': '2 Years',
            'condition': 'New',
            'specifications': {
                'Boost Pressure': '1.5 bar',
                'Material': 'Inconel Turbine',
                'Weight': '15.2 kg',
                'Compressor': '60mm'
            },
            'features': [
                'Advanced ceramic ball bearings',
                'Integrated wastegate control',
                'Heat-resistant coating',
                'Precision-balanced assembly',
                'OEM-grade quality'
            ]
        },
        {
            'id': 'brake-002',
            'name': 'Brembo GT Racing Ceramic Pads',
            'category': 'Brake System',
            'brand': 'Brembo',
            'part_number': 'BRM-GTRC-002',
            'price': '$485',
            'status': 'In Stock',
            'compatibility': 'Porsche 911, Cayman',
            'image': 'parts/brake-pads.jpg',
            'description': 'Premium ceramic brake pads designed for track and street performance with minimal dust production and superior heat dissipation.',
            'warranty': '1 Year',
            'condition': 'New',
            'specifications': {
                'Material': 'Carbon Ceramic',
                'Operating Temp': '0-800°C',
                'Friction Coefficient': '0.42',
                'Thickness': '15mm'
            },
            'features': [
                'Low dust formula',
                'Excellent heat dissipation',
                'Consistent pedal feel',
                'Extended pad life',
                'Reduced brake fade'
            ]
        },
        {
            'id': 'susp-003',
            'name': 'Bilstein B16 PSS10 Coilovers',
            'category': 'Suspension',
            'brand': 'Bilstein',
            'part_number': 'BIL-B16-PSS10',
            'price': '$1,650',
            'status': 'Low Stock',
            'compatibility': 'Audi A4, A6, S4',
            'image': 'parts/coilover.jpg',
            'description': 'Motorsport-derived coilover suspension system with 10-way adjustable damping for ultimate handling precision.',
            'warranty': '2 Years',
            'condition': 'New',
            'specifications': {
                'Adjustability': '10-way damping',
                'Spring Rate': 'Progressive',
                'Ride Height': '25-55mm drop',
                'Material': 'Aluminum/Steel'
            },
            'features': [
                '10-way adjustable damping',
                'Height adjustable',
                'Motorsport technology',
                'Progressive spring rates',
                'Lifetime warranty on internals'
            ]
        },
        {
            'id': 'air-004',
            'name': 'K&N Apollo Cold Air Intake',
            'category': 'Engine Parts',
            'brand': 'K&N Engineering',
            'part_number': 'KN-APOLLO-CAI',
            'price': '$320',
            'status': 'In Stock',
            'compatibility': 'Honda Civic Type R',
            'image': 'parts/air-filter.jpg',
            'description': 'Complete cold air intake system with high-flow filter for increased horsepower and torque with improved throttle response.',
            'warranty': '1 Year',
            'condition': 'New',
            'specifications': {
                'Flow Rate': '850 CFM',
                'Filter Type': 'Cotton Gauze',
                'Pipe Diameter': '3.5 inches',
                'Material': 'Aluminum'
            },
            'features': [
                'Increased horsepower',
                'Improved throttle response',
                'Washable and reusable filter',
                'Mandrel-bent aluminum tubing',
                'Easy installation'
            ]
        },
        {
            'id': 'exh-005',
            'name': 'Akrapovic Evolution Titanium System',
            'category': 'Exhaust',
            'brand': 'Akrapovic',
            'part_number': 'AKR-EVO-TI-V1',
            'price': '$3,200',
            'status': 'Pre-Order',
            'compatibility': 'Lamborghini Huracan',
            'image': 'parts/exhaust-system.jpg',
            'description': 'Full titanium exhaust system with valve control and distinctive Akrapovic sound signature for ultimate performance.',
            'warranty': '2 Years',
            'condition': 'New',
            'specifications': {
                'Material': 'Grade 1 Titanium',
                'Weight Reduction': '8.5 kg',
                'Power Gain': '15 HP',
                'Valve Control': 'Electronic'
            },
            'features': [
                'Full titanium construction',
                'Electronic valve control',
                'Weight reduction',
                'Power increase',
                'Distinctive sound'
            ]
        },
        {
            'id': 'trans-006',
            'name': 'ZF 8HP76 Performance Transmission',
            'category': 'Transmission',
            'brand': 'ZF Friedrichshafen',
            'part_number': 'ZF-8HP76-PERF',
            'price': '$8,500',
            'status': 'Out of Stock',
            'compatibility': 'BMW X5, X6, 7 Series',
            'image': 'parts/transmission.jpg',
            'description': 'High-performance 8-speed automatic transmission with sport programming and launch control for enhanced driving dynamics.',
            'warranty': '3 Years',
            'condition': 'Remanufactured',
            'specifications': {
                'Gears': '8 Forward + Reverse',
                'Torque Capacity': '1000 Nm',
                'Weight': '87 kg',
                'Programming': 'Sport/Comfort'
            },
            'features': [
                'Launch control ready',
                'Sport programming',
                'Lightweight design',
                'High torque capacity',
                'Factory remanufactured'
            ]
        },
        {
            'id': 'ign-007',
            'name': 'NGK Iridium IX Performance Coils',
            'category': 'Electrical',
            'brand': 'NGK Spark Plugs',
            'part_number': 'NGK-IRIX-COIL-SET',
            'price': '$295',
            'status': 'In Stock',
            'compatibility': 'Toyota Supra, Lexus RC F',
            'image': 'parts/ignition-coils.jpg',
            'description': 'Premium iridium ignition coil set for enhanced combustion efficiency and reliability with stronger spark energy.',
            'warranty': '1 Year',
            'condition': 'New',
            'specifications': {
                'Electrode': 'Iridium IX',
                'Voltage': '40,000V',
                'Resistance': '5k Ohm',
                'Temperature': '-40 to 150°C'
            },
            'features': [
                'Iridium electrode technology',
                'Enhanced spark energy',
                'Improved fuel efficiency',
                'Longer service life',
                'OEM quality'
            ]
        },
        {
            'id': 'hood-008',
            'name': 'Seibon Carbon Fiber Vented Hood',
            'category': 'Body Parts',
            'brand': 'Seibon Carbon',
            'part_number': 'SB-CF-HOOD-GTR',
            'price': '$1,850',
            'status': 'Low Stock',
            'compatibility': 'Nissan GT-R R35',
            'image': 'parts/carbon-hood.jpg',
            'description': 'Lightweight carbon fiber hood with functional heat extraction vents and UV-resistant clear coat finish.',
            'warranty': '1 Year',
            'condition': 'New',
            'specifications': {
                'Material': '2x2 Twill Carbon Fiber',
                'Weight': '8.5 kg',
                'Weight Reduction': '12 kg vs stock',
                'Finish': 'UV Clear Coat'
            },
            'features': [
                'Functional heat vents',
                'Weight reduction',
                'UV-resistant finish',
                'Perfect fitment',
                'Race-inspired design'
            ]
        },
        {
            'id': 'seat-009',
            'name': 'Recaro Pole Position Racing Seats',
            'category': 'Interior',
            'brand': 'Recaro',
            'part_number': 'REC-POLE-POS-ABE',
            'price': '$2,400',
            'status': 'In Stock',
            'compatibility': 'Universal Fitment',
            'image': 'parts/racing-seats.jpg',
            'description': 'FIA-approved racing seats with advanced side support and premium Dinamica upholstery for maximum comfort and safety.',
            'warranty': '2 Years',
            'condition': 'New',
            'specifications': {
                'Certification': 'FIA 8855-1999',
                'Material': 'Carbon Fiber/Kevlar',
                'Weight': '9.5 kg each',
                'Upholstery': 'Dinamica'
            },
            'features': [
                'FIA approved',
                'Carbon fiber shell',
                'Side impact protection',
                'Premium upholstery',
                'Universal mounting'
            ]
        },
        {
            'id': 'oil-010',
            'name': 'Mobil 1 Extended Performance 0W-20',
            'category': 'Engine Parts',
            'brand': 'Mobil 1',
            'part_number': 'MOB1-EP-0W20-5Q',
            'price': '$85',
            'status': 'In Stock',
            'compatibility': 'Most Modern Engines',
            'image': 'parts/engine-oil.jpg',
            'description': 'Full synthetic motor oil providing up to 20,000 miles of protection with superior thermal stability and engine protection.',
            'warranty': 'N/A',
            'condition': 'New',
            'specifications': {
                'Viscosity': '0W-20',
                'Volume': '5 Quarts',
                'Protection': '20,000 miles',
                'API Rating': 'SP/GF-6A'
            },
            'features': [
                'Extended drain intervals',
                'Superior wear protection',
                'Thermal stability',
                'Fuel economy improvement',
                'Full synthetic formula'
            ]
        },
        {
            'id': 'tire-011',
            'name': 'Michelin Pilot Sport Cup 2 R',
            'category': 'Wheels-Tires',
            'brand': 'Michelin',
            'part_number': 'MICH-PSC2R-295',
            'price': '$1,200',
            'status': 'Pre-Order',
            'compatibility': 'Performance Vehicles',
            'image': 'parts/tires.jpg',
            'description': 'Track-focused semi-slick tires with exceptional grip and cornering performance for competitive driving and track days.',
            'warranty': '6 Months',
            'condition': 'New',
            'specifications': {
                'Size': '295/30R20',
                'Tread': 'Semi-slick',
                'Compound': 'Bi-compound',
                'Load Rating': '101Y'
            },
            'features': [
                'Track-optimized compound',
                'Maximum grip',
                'Exceptional cornering',
                'Professional racing heritage',
                'Set of 4 tires'
            ]
        },
        {
            'id': 'fuel-012',
            'name': 'Bosch EV14 High-Flow Injectors',
            'category': 'Engine Parts',
            'brand': 'Bosch',
            'part_number': 'BSH-EV14-1000CC',
            'price': '$650',
            'status': 'Out of Stock',
            'compatibility': 'Mercedes AMG C63',
            'image': 'parts/fuel-injectors.jpg',
            'description': 'High-flow fuel injectors with precision spray pattern for optimized fuel delivery and enhanced performance in high-output engines.',
            'warranty': '2 Years',
            'condition': 'New',
            'specifications': {
                'Flow Rate': '1000cc/min',
                'Impedance': 'High',
                'Pressure': '3.5 bar',
                'Connector': 'EV14'
            },
            'features': [
                'High flow rate',
                'Precision spray pattern',
                'Optimized fuel delivery',
                'Enhanced performance',
                'Set of 8 injectors'
            ]
        }
    ]
    
    # Find the specific part
    part = None
    for p in inventory_parts:
        if p['id'] == part_id:
            part = p
            break
    
    if not part:
        return render_template('404.html'), 404
    
    return render_template('product_detail.html', product=part)

@app.route('/part-payment/<part_id>', methods=['GET', 'POST'])
@login_required
def part_payment(part_id):
    """Handle payment processing for car parts"""
    
    # Enhanced car parts inventory data - matches the part_details route data
    inventory_parts = [
        {
            'id': 'turbo-001',
            'name': 'Garrett GT2860RS Turbocharger',
            'category': 'Engine Parts',
            'brand': 'Garrett Motion',
            'part_number': 'GTM-2860RS-001',
            'price': '$2,850',
            'status': 'In Stock'
        },
        {
            'id': 'brake-002',
            'name': 'Brembo GT Racing Ceramic Pads',
            'category': 'Brake System',
            'brand': 'Brembo',
            'part_number': 'BRM-GTRC-002',
            'price': '$485',
            'status': 'In Stock'
        },
        {
            'id': 'susp-003',
            'name': 'Bilstein B16 PSS10 Coilovers',
            'category': 'Suspension',
            'brand': 'Bilstein',
            'part_number': 'BIL-B16-PSS10',
            'price': '$1,650',
            'status': 'Low Stock'
        },
        {
            'id': 'air-004',
            'name': 'K&N Apollo Cold Air Intake',
            'category': 'Engine Parts',
            'brand': 'K&N Engineering',
            'part_number': 'KN-APOLLO-CAI',
            'price': '$320',
            'status': 'In Stock'
        },
        {
            'id': 'exh-005',
            'name': 'Akrapovic Evolution Titanium System',
            'category': 'Exhaust',
            'brand': 'Akrapovic',
            'part_number': 'AKR-EVO-TI-V1',
            'price': '$3,200',
            'status': 'Pre-Order'
        },
        {
            'id': 'trans-006',
            'name': 'ZF 8HP76 Performance Transmission',
            'category': 'Transmission',
            'brand': 'ZF Friedrichshafen',
            'part_number': 'ZF-8HP76-PERF',
            'price': '$8,500',
            'status': 'Out of Stock'
        },
        {
            'id': 'ign-007',
            'name': 'NGK Iridium IX Performance Coils',
            'category': 'Electrical',
            'brand': 'NGK Spark Plugs',
            'part_number': 'NGK-IRIX-COIL-SET',
            'price': '$295',
            'status': 'In Stock'
        },
        {
            'id': 'hood-008',
            'name': 'Seibon Carbon Fiber Vented Hood',
            'category': 'Body Parts',
            'brand': 'Seibon Carbon',
            'part_number': 'SB-CF-HOOD-GTR',
            'price': '$1,850',
            'status': 'Low Stock'
        },
        {
            'id': 'seat-009',
            'name': 'Recaro Pole Position Racing Seats',
            'category': 'Interior',
            'brand': 'Recaro',
            'part_number': 'REC-POLE-POS-ABE',
            'price': '$2,400',
            'status': 'In Stock'
        },
        {
            'id': 'oil-010',
            'name': 'Mobil 1 Extended Performance 0W-20',
            'category': 'Engine Parts',
            'brand': 'Mobil 1',
            'part_number': 'MOB1-EP-0W20-5Q',
            'price': '$85',
            'status': 'In Stock'
        },
        {
            'id': 'tire-011',
            'name': 'Michelin Pilot Sport Cup 2 R',
            'category': 'Wheels-Tires',
            'brand': 'Michelin',
            'part_number': 'MICH-PSC2R-295',
            'price': '$1,200',
            'status': 'Pre-Order'
        },
        {
            'id': 'fuel-012',
            'name': 'Bosch EV14 High-Flow Injectors',
            'category': 'Engine Parts',
            'brand': 'Bosch',
            'part_number': 'BSH-EV14-1000CC',
            'price': '$650',
            'status': 'Out of Stock'
        }
    ]
    
    # Find the specific part
    part = None
    for p in inventory_parts:
        if p['id'] == part_id:
            part = p
            break
    
    if not part:
        flash('Part not found.', 'error')
        return redirect(url_for('inventory'))
    
    # Check if part is available
    if part['status'] == 'Out of Stock':
        flash('This part is currently out of stock.', 'error')
        return redirect(url_for('part_details', part_id=part_id))
    
    form = PaymentForm()
    
    # Pre-fill form with user data
    if request.method == 'GET':
        form.billing_name.data = current_user.get_full_name() or current_user.username
        form.billing_email.data = current_user.email
        if current_user.phone:
            form.billing_phone.data = current_user.phone
        if current_user.address:
            form.billing_address.data = current_user.address
    
    if form.validate_on_submit():
        try:
            # Get quantity from form or default to 1
            quantity = int(request.form.get('quantity', 1))
            if quantity < 1:
                quantity = 1
            
            # Parse the price
            price_str = str(part['price']).replace('$', '').replace(',', '')
            try:
                unit_price = float(price_str)
                total_amount = unit_price * quantity
            except:
                unit_price = 0.0
                total_amount = 0.0
            
            # Create new part order
            part_order = PartOrder(
                user_id=current_user.id,
                part_id=part['id'],
                part_name=part['name'],
                part_number=part['part_number'],
                brand=part['brand'],
                category=part['category'],
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount,
                payment_status='completed',
                order_status='processing',
                payment_method=form.payment_method.data,
                transaction_id=f"PART-TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                billing_name=form.billing_name.data,
                billing_email=form.billing_email.data,
                billing_phone=form.billing_phone.data,
                billing_address=form.billing_address.data,
                shipping_address=request.form.get('shipping_address', form.billing_address.data)
            )
            
            db.session.add(part_order)
            db.session.commit()
            
            # Log user activity
            log_user_activity(
                user_id=current_user.id,
                activity_type='part_purchase',
                description=f'Purchased {quantity}x {part["name"]}',
                metadata={'part_id': part['id'], 'quantity': quantity, 'order_id': part_order.id}
            )
            
            flash(f'Payment successful! Your order for {quantity}x {part["name"]} has been confirmed.', 'success')
            return redirect(url_for('part_payment_success', order_id=part_order.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Payment processing failed. Please try again.', 'error')
            print(f"Part payment error: {e}")
    
    return render_template('part_payment.html', form=form, part=part)

@app.route('/part-payment-success/<int:order_id>')
@login_required
def part_payment_success(order_id):
    """Display part order success page"""
    order = PartOrder.query.get_or_404(order_id)
    
    # Ensure the order belongs to the current user
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('part_payment_success.html', order=order)

@app.route('/product-details/<product_id>')
def product_details(product_id):
    
    # Sample inventory data - matches the inventory route data
    inventory_cars = [
        {
            'id': 'lamborghini-revuelto',
            'name': 'Lamborghini Revuelto',
            'year': '2024',
            'price': '$516,000',
            'status': 'Available',
            'mileage': '0 miles',
            'location': 'New York Showroom',
            'color': 'Nero Aldebaran',
            'image': 'lamborghini_revuelto.glb',
            'engine': '6.5L V12 Hybrid',
            'horsepower': '1,001 hp',
            'torque': '725 lb-ft',
            'topSpeed': '217 mph',
            'acceleration': '2.5 seconds (0-60 mph)',
            'transmission': '8-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '11 mpg city / 18 mpg highway',
            'description': 'The Lamborghini Revuelto represents the pinnacle of automotive engineering, combining a naturally aspirated V12 engine with hybrid technology for unprecedented performance.',
            'features': [
                'Carbon fiber monocoque chassis',
                'Advanced aerodynamics package', 
                'Adaptive suspension system',
                'Premium leather interior',
                'Advanced infotainment system',
                'Track-focused driving modes'
            ],
            'gallery': ['lamborghini_revuelto.glb', 'Lamborghini.mp4', 'lamborghini_revuelt.mp4']
        },
        {
            'id': 'bugatti-centodieci',
            'name': 'Bugatti Centodieci',
            'year': '2022',
            'price': '$9,000,000',
            'status': 'Reserved',
            'mileage': '25 miles',
            'location': 'Beverly Hills Showroom',
            'color': 'EB110 Blue',
            'image': 'bugatti_centodieci.glb',
            'engine': '8.0L Quad-Turbo W16',
            'horsepower': '1,577 hp',
            'torque': '1,180 lb-ft',
            'topSpeed': '236 mph',
            'acceleration': '2.4 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '8 mpg city / 14 mpg highway',
            'description': 'The Bugatti Centodieci is an exclusive hypercar celebrating the legendary EB110, featuring unmatched performance and luxury.',
            'features': [
                'Carbon fiber bodywork',
                'Active aerodynamics',
                'Racing-inspired interior',
                'Bespoke luxury appointments',
                'Advanced traction control',
                'Limited production (10 units)'
            ],
            'gallery': ['bugatti_centodieci.glb', 'bugatti_centodieci.mp4']
        },
        {
            'id': 'ferrari-296',
            'name': 'Ferrari 296 GTB',
            'year': '2023',
            'price': '$320,000',
            'status': 'Available',
            'mileage': '0 miles',
            'location': 'Miami Showroom',
            'color': 'Rosso Corsa',
            'image': 'ferrari_296.glb',
            'engine': '3.0L V6 Hybrid',
            'horsepower': '818 hp',
            'torque': '546 lb-ft',
            'topSpeed': '205 mph',
            'acceleration': '2.9 seconds (0-60 mph)',
            'transmission': '8-Speed Dual-Clutch',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '15 mpg city / 22 mpg highway',
            'description': 'The Ferrari 296 GTB combines Ferrari\'s racing heritage with cutting-edge hybrid technology for an extraordinary driving experience.',
            'features': [
                'Carbon fiber construction',
                'Hybrid powertrain',
                'Active aerodynamics',
                'Racing-derived suspension',
                'Premium Alcantara interior',
                'Advanced driver assistance'
            ],
            'gallery': ['ferrari_296.glb', 'Ferrari 296 GTB.mp4', 'Ferrari.mp4']
        },
        {
            'id': 'mclaren-720s',
            'name': 'McLaren 720S',
            'year': '2023',
            'price': '$310,000',
            'status': 'Available',
            'mileage': '12 miles',
            'location': 'Los Angeles Showroom',
            'color': 'Papaya Orange',
            'image': 'mclaren.glb',
            'engine': '4.0L Twin-Turbo V8',
            'horsepower': '710 hp',
            'torque': '568 lb-ft',
            'topSpeed': '212 mph',
            'acceleration': '2.8 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '15 mpg city / 22 mpg highway',
            'description': 'The McLaren 720S delivers track-bred performance with everyday usability, featuring McLaren\'s signature dihedral doors and carbon fiber monocoque.',
            'features': [
                'Carbon fiber MonoCell chassis',
                'Dihedral doors',
                'Active suspension system',
                'Lightweight construction',
                'Premium leather interior',
                'Track telemetry system'
            ],
            'gallery': ['mclaren.glb', 'McLaren.mp4']
        },
        {
            'id': 'porsche-718-cayman-gt4',
            'name': 'Porsche 718 Cayman GT4',
            'year': '2023',
            'price': '$110,000',
            'status': 'Available',
            'mileage': '0 miles',
            'location': 'Chicago Showroom',
            'color': 'Guards Red',
            'image': '2018_porsche_718_cayman_gts.glb',
            'engine': '4.0L Flat-6',
            'horsepower': '414 hp',
            'torque': '309 lb-ft',
            'topSpeed': '188 mph',
            'acceleration': '4.2 seconds (0-60 mph)',
            'transmission': '6-Speed Manual',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '16 mpg city / 24 mpg highway',
            'description': 'The Porsche 718 Cayman GT4 offers pure driving pleasure with its naturally aspirated flat-six engine and precision handling.',
            'features': [
                'Naturally aspirated flat-six',
                'Manual transmission',
                'Sport suspension',
                'Racing-inspired aero',
                'Premium sports interior',
                'Track-focused dynamics'
            ],
            'gallery': ['2018_porsche_718_cayman_gts.glb']
        },
        {
            'id': 'aston-martin-v8-vantage',
            'name': 'Aston Martin V8 Vantage',
            'year': '2023',
            'price': '$150,000',
            'status': 'Sold',
            'mileage': '5 miles',
            'location': 'Dallas Showroom',
            'color': 'British Racing Green',
            'image': 'aston_martin_v8_vantage.glb',
            'engine': '4.0L Twin-Turbo V8',
            'horsepower': '503 hp',
            'torque': '505 lb-ft',
            'topSpeed': '195 mph',
            'acceleration': '3.5 seconds (0-60 mph)',
            'transmission': '8-Speed Automatic',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '16 mpg city / 24 mpg highway',
            'description': 'The Aston Martin V8 Vantage embodies British luxury and performance with its handcrafted interior and powerful V8 engine.',
            'features': [
                'Hand-stitched leather interior',
                'British craftsmanship',
                'Performance-tuned suspension',
                'Premium audio system',
                'Advanced driver aids',
                'Elegant design language'
            ],
            'gallery': ['aston_martin_v8_vantage.glb', 'astonmartin.mp4']
        },
        {
            'id': 'tesla-cybertruck',
            'name': 'Tesla Cybertruck',
            'year': '2024',
            'price': '$100,000',
            'status': 'Pre-Order',
            'mileage': '0 miles',
            'location': 'Austin Showroom',
            'color': 'Stainless Steel',
            'image': 'tesla_cybertruck.glb',
            'engine': 'Electric Motors',
            'horsepower': '845 hp',
            'torque': '10,296 lb-ft',
            'topSpeed': '130 mph',
            'acceleration': '2.6 seconds (0-60 mph)',
            'transmission': 'Single-Speed',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '340 miles range',
            'description': 'The Tesla Cybertruck revolutionizes pickup trucks with its angular design, bulletproof construction, and advanced autopilot features.',
            'features': [
                'Bulletproof exoskeleton',
                'Autopilot capability',
                'Over-the-air updates',
                'Massive towing capacity',
                'Solar panel integration',
                'Advanced battery technology'
            ],
            'gallery': ['tesla_cybertruck.glb']
        },
        {
            'id': 'bmw-m2-g87',
            'name': 'BMW M2 G87',
            'year': '2023',
            'price': '$65,000',
            'status': 'Available',
            'mileage': '8 miles',
            'location': 'Seattle Showroom',
            'color': 'Alpine White',
            'image': 'bmw_m2_g87.glb',
            'engine': '3.0L Twin-Turbo I6',
            'horsepower': '453 hp',
            'torque': '406 lb-ft',
            'topSpeed': '155 mph',
            'acceleration': '4.1 seconds (0-60 mph)',
            'transmission': '8-Speed Automatic',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '18 mpg city / 25 mpg highway',
            'description': 'The BMW M2 G87 delivers pure M performance in a compact package, featuring precise handling and turbocharged power.',
            'features': [
                'M-tuned suspension',
                'Performance brakes',
                'Sport differential',
                'M interior package',
                'Advanced stability control',
                'Track-ready performance'
            ],
            'gallery': ['bmw_m2_g87.glb', 'BMW M2 G87.mp4', 'bmw m2.mp4']
        }
    ]
    
    # Find the specific product
    product = None
    for car in inventory_cars:
        if car['id'] == product_id:
            product = car
            break
    
    if not product:
        return render_template('404.html'), 404
    
    return render_template('product_detail.html', product=product)

@app.route('/car-details/<car_name>')
def car_details(car_name):
    # Log user activity for viewing car details
    if current_user.is_authenticated:
        log_user_activity(
            user_id=current_user.id,
            activity_type='car_view',
            description=f'Viewed car details for {car_name}',
            metadata={'car_name': car_name}
        )
    
    # Sample car data - in a real app, this would come from a database
    car_data = {
        'lamborghini-revuelto': {
            'name': 'Lamborghini Revuelto',
            'model': 'lamborghini_revuelto.glb',
            'year': '2024',
            'price': '$516,000',
            'engine': '6.5L V12 Hybrid',
            'horsepower': '1,001 hp',
            'torque': '725 lb-ft',
            'topSpeed': '217 mph',
            'acceleration': '2.5 seconds (0-60 mph)',
            'transmission': '8-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '11 mpg city / 18 mpg highway',
            'description': 'The Lamborghini Revuelto represents the pinnacle of automotive engineering, combining a naturally aspirated V12 engine with hybrid technology for unprecedented performance.',
            'features': [
                'Carbon fiber monocoque chassis',
                'Advanced aerodynamics package',
                'Adaptive suspension system',
                'Premium leather interior',
                'Advanced infotainment system',
                'Track-focused driving modes'
            ]
        },
        'bugatti-centodieci': {
            'name': 'Bugatti Centodieci',
            'model': 'bugatti_centodieci.glb',
            'year': '2022',
            'price': '$9,000,000',
            'engine': '8.0L Quad-Turbo W16',
            'horsepower': '1,577 hp',
            'torque': '1,180 lb-ft',
            'topSpeed': '236 mph',
            'acceleration': '2.4 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '8 mpg city / 14 mpg highway',
            'description': 'A tribute to the legendary EB110, the Centodieci combines Bugatti\'s rich heritage with cutting-edge technology and unparalleled luxury.',
            'features': [
                'Limited production (10 units)',
                'Carbon fiber bodywork',
                'Michelin Pilot Sport Cup 2 tires',
                'Brembo carbon-ceramic brakes',
                'Exclusive interior appointments',
                'Track telemetry system'
            ]
        },
        'ferrari-296': {
            'name': 'Ferrari 296 GTB',
            'model': 'ferrari_296.glb',
            'year': '2023',
            'price': '$320,000',
            'engine': '2.9L V6 Hybrid Turbo',
            'horsepower': '819 hp',
            'torque': '546 lb-ft',
            'topSpeed': '205 mph',
            'acceleration': '2.9 seconds (0-60 mph)',
            'transmission': '8-Speed Dual-Clutch',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '16 mpg city / 22 mpg highway',
            'description': 'The Ferrari 296 GTB is a groundbreaking mid-rear-engined 2-seater berlinetta that introduces the new 120° V6 engine coupled with a plug-in electric motor.',
            'features': [
                'Hybrid V6 powertrain',
                'Active aerodynamics',
                'Carbon fiber construction',
                'Manettino dial with hybrid modes',
                'F1-derived technology',
                'Customizable interior options'
            ]
        },
        'mclaren-720s': {
            'name': 'McLaren 720S',
            'model': 'mclaren.glb',
            'year': '2023',
            'price': '$310,000',
            'engine': '4.0L Twin-Turbo V8',
            'horsepower': '710 hp',
            'torque': '568 lb-ft',
            'topSpeed': '212 mph',
            'acceleration': '2.8 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '15 mpg city / 22 mpg highway',
            'description': 'The McLaren 720S delivers breathtaking performance with its lightweight carbon fiber construction and advanced aerodynamics.',
            'features': [
                'Carbon fiber MonoCell II chassis',
                'Proactive Chassis Control II',
                'Variable Drift Control',
                'Adaptive suspension',
                'Track telemetry system',
                'Lightweight construction'
            ]
        },
        'porsche-718-cayman-gt4': {
            'name': 'Porsche 718 Cayman GT4',
            'model': 'porsche_718_cayman_gt4.glb',
            'year': '2023',
            'price': '$110,000',
            'engine': '4.0L Naturally Aspirated Flat-6',
            'horsepower': '414 hp',
            'torque': '309 lb-ft',
            'topSpeed': '188 mph',
            'acceleration': '4.2 seconds (0-60 mph)',
            'transmission': '6-Speed Manual',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '18 mpg city / 24 mpg highway',
            'description': 'The Porsche 718 Cayman GT4 represents the perfect balance of track performance and daily usability with its naturally aspirated engine.',
            'features': [
                'Naturally aspirated flat-6 engine',
                'Sport Chrono Package',
                'PASM adaptive suspension',
                'Track-focused aerodynamics',
                'Carbon fiber elements',
                'Racing-inspired interior'
            ]
        },
        'aston-martin-v8-vantage': {
            'name': 'Aston Martin V8 Vantage',
            'model': 'aston_martin_v8_vantage.glb',
            'year': '2023',
            'price': '$150,000',
            'engine': '4.0L Twin-Turbo V8',
            'horsepower': '503 hp',
            'torque': '461 lb-ft',
            'topSpeed': '195 mph',
            'acceleration': '3.5 seconds (0-60 mph)',
            'transmission': '8-Speed Automatic',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '16 mpg city / 24 mpg highway',
            'description': 'The Aston Martin V8 Vantage combines British luxury with exhilarating performance in a beautifully crafted sports car.',
            'features': [
                'Handcrafted luxury interior',
                'Adaptive damping system',
                'Electronic rear differential',
                'Premium leather appointments',
                'Bang & Olufsen sound system',
                'Advanced infotainment'
            ]
        },
        'lamborghini-temerario': {
            'name': 'Lamborghini Temerario',
            'model': 'lamborghini_temerario.glb',
            'year': '2024',
            'price': '$240,000',
            'engine': '4.0L Twin-Turbo V8 Hybrid',
            'horsepower': '907 hp',
            'torque': '627 lb-ft',
            'topSpeed': '210 mph',
            'acceleration': '2.7 seconds (0-60 mph)',
            'transmission': '8-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '14 mpg city / 20 mpg highway',
            'description': 'The Lamborghini Temerario showcases the future of Lamborghini with its hybrid V8 powertrain and cutting-edge technology.',
            'features': [
                'Hybrid V8 powertrain',
                'Active aerodynamics package',
                'Carbon fiber body panels',
                'Advanced traction control',
                'Customizable drive modes',
                'Premium Alcantara interior'
            ]
        },
        'tesla-cybertruck': {
            'name': 'Tesla Cybertruck',
            'model': 'tesla_cybertruck.glb',
            'year': '2024',
            'price': '$100,000',
            'engine': 'Tri-Motor Electric',
            'horsepower': '845 hp',
            'torque': '930 lb-ft',
            'topSpeed': '130 mph',
            'acceleration': '2.8 seconds (0-60 mph)',
            'transmission': 'Single-Speed Direct Drive',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '340 miles range',
            'description': 'The Tesla Cybertruck redefines what a pickup truck can be with its revolutionary design and all-electric powertrain.',
            'features': [
                'Ultra-hard 30X cold-rolled steel',
                'Armor glass windows',
                'Air suspension system',
                'Autopilot capabilities',
                'Solar panel integration ready',
                'Massive towing capacity'
            ]
        },
        'koenigsegg-agera-rs': {
            'name': 'Koenigsegg Agera RS',
            'model': 'koenigsegg_agera.glb',
            'year': '2023',
            'price': '$2,500,000',
            'engine': '5.0L Twin-Turbo V8',
            'horsepower': '1,360 hp',
            'torque': '1,011 lb-ft',
            'topSpeed': '278 mph',
            'acceleration': '2.8 seconds (0-60 mph)',
            'transmission': '7-Speed Automatic',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '12 mpg city / 18 mpg highway',
            'description': 'The Koenigsegg Agera RS represents the ultimate expression of Swedish hypercar engineering with record-breaking performance.',
            'features': [
                'Carbon fiber construction',
                'Active aerodynamics',
                'Track-focused suspension',
                'Lightweight titanium components',
                'Bespoke interior craftsmanship',
                'Advanced telemetry system'
            ]
        },
        'bmw-m2-g87': {
            'name': 'BMW M2 G87',
            'model': 'bmw_m2_g87.glb',
            'year': '2023',
            'price': '$65,000',
            'engine': '3.0L Twin-Turbo Inline-6',
            'horsepower': '453 hp',
            'torque': '406 lb-ft',
            'topSpeed': '177 mph',
            'acceleration': '4.1 seconds (0-60 mph)',
            'transmission': '6-Speed Manual / 8-Speed Auto',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '19 mpg city / 26 mpg highway',
            'description': 'The BMW M2 G87 delivers pure driving excitement with its perfect balance of power, handling, and everyday usability.',
            'features': [
                'M TwinPower Turbo engine',
                'Adaptive M suspension',
                'M differential',
                'Carbon fiber roof',
                'M-specific interior',
                'Track-ready performance'
            ]
        },
        'lamborghini-diablo-sv': {
            'name': '1995 Lamborghini Diablo SV',
            'model': '1995_lamborghini_diablo_sv.glb',
            'year': '1995',
            'price': '$300,000',
            'engine': '5.7L V12',
            'horsepower': '510 hp',
            'torque': '428 lb-ft',
            'topSpeed': '202 mph',
            'acceleration': '4.0 seconds (0-60 mph)',
            'transmission': '5-Speed Manual',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '9 mpg city / 15 mpg highway',
            'description': 'The Lamborghini Diablo SV is a legendary supercar that defined the 1990s with its aggressive styling and raw V12 power.',
            'features': [
                'Naturally aspirated V12 engine',
                'Carbon fiber aerodynamic kit',
                'Adjustable rear wing',
                'Racing-inspired interior',
                'Limited slip differential',
                'Iconic scissor doors'
            ]
        },
        'renault-clio-v6': {
            'name': '2003 Renault Clio V6 Sport',
            'model': '2003_renault_clio_v6_renault_sport.glb',
            'year': '2003',
            'price': '$45,000',
            'engine': '3.0L V6',
            'horsepower': '255 hp',
            'torque': '221 lb-ft',
            'topSpeed': '153 mph',
            'acceleration': '5.8 seconds (0-60 mph)',
            'transmission': '6-Speed Manual',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '18 mpg city / 25 mpg highway',
            'description': 'The Renault Clio V6 is a unique mid-engined hot hatch that combines practicality with exceptional performance.',
            'features': [
                'Mid-mounted V6 engine',
                'Widebody aerodynamic kit',
                'Brembo braking system',
                'Recaro sport seats',
                'Limited production run',
                'Track-focused suspension'
            ]
        },
        'porsche-718-cayman-gts': {
            'name': '2018 Porsche 718 Cayman GTS',
            'model': '2018_porsche_718_cayman_gts.glb',
            'year': '2018',
            'price': '$85,000',
            'engine': '2.5L Turbo Flat-4',
            'horsepower': '365 hp',
            'torque': '309 lb-ft',
            'topSpeed': '180 mph',
            'acceleration': '4.1 seconds (0-60 mph)',
            'transmission': '6-Speed Manual',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '20 mpg city / 28 mpg highway',
            'description': 'The 718 Cayman GTS offers the perfect balance of performance and daily usability with Porsche\'s legendary handling.',
            'features': [
                'Turbocharged flat-4 engine',
                'Sport Chrono Package',
                'PASM adaptive suspension',
                'Sport exhaust system',
                'Alcantara interior trim',
                'GTS-specific styling'
            ]
        },
        'lamborghini-countach': {
            'name': '2022 Lamborghini Countach LPI 800-4',
            'model': '2022_lamborghini_countach_lpi_800-4.glb',
            'year': '2022',
            'price': '$2,650,000',
            'engine': '6.5L V12 Hybrid',
            'horsepower': '803 hp',
            'torque': '531 lb-ft',
            'topSpeed': '221 mph',
            'acceleration': '2.8 seconds (0-60 mph)',
            'transmission': '7-Speed Automatic',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '10 mpg city / 16 mpg highway',
            'description': 'The modern Countach pays homage to the iconic original while delivering cutting-edge hybrid performance.',
            'features': [
                'Hybrid V12 powertrain',
                'Limited production (112 units)',
                'Carbon fiber construction',
                'Retro-futuristic design',
                'Advanced aerodynamics',
                'Exclusive interior materials'
            ]
        },
        'hyundai-ioniq-5n': {
            'name': '2024 Hyundai Ioniq 5 N',
            'model': '2024_hyundai_ioniq_5_n.glb',
            'year': '2024',
            'price': '$67,000',
            'engine': 'Dual Electric Motors',
            'horsepower': '641 hp',
            'torque': '545 lb-ft',
            'topSpeed': '162 mph',
            'acceleration': '3.4 seconds (0-60 mph)',
            'transmission': 'Single-Speed Direct Drive',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '303 miles range',
            'description': 'The Ioniq 5 N combines high-performance electric propulsion with innovative technology and distinctive design.',
            'features': [
                'Dual motor electric drivetrain',
                'N Grin Boost mode',
                'Ultra-fast charging capability',
                'Active aerodynamics',
                'Advanced driver assistance',
                'Sporty N interior package'
            ]
        },
        'lamborghini-huracan-sterrato': {
            'name': '2024 Lamborghini Huracán Sterrato',
            'model': '2024_lamborghini_huracan_sterrato.glb',
            'year': '2024',
            'price': '$265,000',
            'engine': '5.2L V10',
            'horsepower': '602 hp',
            'torque': '413 lb-ft',
            'topSpeed': '162 mph',
            'acceleration': '3.4 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '13 mpg city / 18 mpg highway',
            'description': 'The Huracán Sterrato is the world\'s first super sports car designed for off-road adventures.',
            'features': [
                'Rally-inspired design',
                'Increased ground clearance',
                'All-terrain capabilities',
                'Reinforced underbody protection',
                'Off-road driving modes',
                'Roof-mounted LED light bar'
            ]
        },
        'bentley-mulliner-batur': {
            'name': 'Bentley Mulliner Batur',
            'model': 'bentley_mulliner_batur.glb',
            'year': '2023',
            'price': '$2,000,000',
            'engine': '6.0L Twin-Turbo W12',
            'horsepower': '730 hp',
            'torque': '738 lb-ft',
            'topSpeed': '209 mph',
            'acceleration': '3.7 seconds (0-60 mph)',
            'transmission': '8-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '12 mpg city / 20 mpg highway',
            'description': 'The Bentley Mulliner Batur is a bespoke grand tourer that showcases the future of Bentley design.',
            'features': [
                'Handcrafted Mulliner interior',
                'Carbon fiber bodywork',
                'Bespoke paint finishes',
                'Premium leather appointments',
                'Limited production (18 units)',
                'Advanced chassis technology'
            ]
        },
        'ferrari-monza-sp1': {
            'name': 'Ferrari Monza SP1',
            'model': 'ferrari_monza_sp1.glb',
            'year': '2023',
            'price': '$1,750,000',
            'engine': '6.5L V12',
            'horsepower': '809 hp',
            'torque': '530 lb-ft',
            'topSpeed': '186 mph',
            'acceleration': '2.9 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '12 mpg city / 17 mpg highway',
            'description': 'The Ferrari Monza SP1 is a limited-series speedster that celebrates Ferrari\'s racing heritage.',
            'features': [
                'Single-seat speedster design',
                'Carbon fiber construction',
                'Active aerodynamics',
                'Racing-inspired cockpit',
                'Limited production series',
                'Heritage-inspired styling'
            ]
        },
        'jeep-wrangler-rubicon': {
            'name': 'Jeep Wrangler Rubicon',
            'model': 'jeep_wrangler_rubicon.glb',
            'year': '2023',
            'price': '$55,000',
            'engine': '3.6L V6',
            'horsepower': '285 hp',
            'torque': '260 lb-ft',
            'topSpeed': '112 mph',
            'acceleration': '6.5 seconds (0-60 mph)',
            'transmission': '8-Speed Automatic',
            'drivetrain': '4WD',
            'fuelEconomy': '18 mpg city / 24 mpg highway',
            'description': 'The Jeep Wrangler Rubicon is the most capable off-road vehicle in the Jeep lineup.',
            'features': [
                'Rock-Trac 4WD system',
                'Rubicon rock rails',
                'Electronic front and rear lockers',
                'Disconnecting front sway bar',
                'Skid plates protection',
                'All-terrain tires'
            ]
        },
        'mercedes-maybach': {
            'name': 'Mercedes-Benz Maybach S-Class',
            'model': 'mercedes-benz_maybach_2022.glb',
            'year': '2022',
            'price': '$185,000',
            'engine': '4.0L Twin-Turbo V8',
            'horsepower': '496 hp',
            'torque': '516 lb-ft',
            'topSpeed': '155 mph',
            'acceleration': '4.4 seconds (0-60 mph)',
            'transmission': '9-Speed Automatic',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '17 mpg city / 25 mpg highway',
            'description': 'The Mercedes-Maybach S-Class represents the pinnacle of luxury and automotive craftsmanship.',
            'features': [
                'Executive rear seating',
                'Burmester 4D surround sound',
                'Active body control',
                'Massage seats with heating/cooling',
                'Premium leather and wood trim',
                'Advanced driver assistance'
            ]
        },
        'rolls-royce-ghost': {
            'name': 'Rolls-Royce Ghost',
            'model': 'rolls_royce_ghost.glb',
            'year': '2023',
            'price': '$350,000',
            'engine': '6.75L Twin-Turbo V12',
            'horsepower': '563 hp',
            'torque': '627 lb-ft',
            'topSpeed': '155 mph',
            'acceleration': '4.6 seconds (0-60 mph)',
            'transmission': '8-Speed Automatic',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '14 mpg city / 21 mpg highway',
            'description': 'The Rolls-Royce Ghost embodies the spirit of ecstasy with unparalleled luxury and refinement.',
            'features': [
                'Hand-crafted interior',
                'Whisper-quiet cabin',
                'Starlight headliner',
                'Spirit of Ecstasy ornament',
                'Bespoke customization options',
                'Advanced air suspension'
            ]
        },
        'rolls-royce-spectre': {
            'name': 'Rolls-Royce Spectre',
            'model': 'rolls-royce_spectre.glb',
            'year': '2024',
            'price': '$420,000',
            'engine': 'Dual Electric Motors',
            'horsepower': '577 hp',
            'torque': '664 lb-ft',
            'topSpeed': '155 mph',
            'acceleration': '4.4 seconds (0-60 mph)',
            'transmission': 'Single-Speed Direct Drive',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '291 miles range',
            'description': 'The Rolls-Royce Spectre is the first fully electric Rolls-Royce, combining luxury with sustainable performance.',
            'features': [
                'All-electric powertrain',
                'Ultra-luxury interior',
                'Advanced battery technology',
                'Whisper-silent operation',
                'Bespoke craftsmanship',
                'Cutting-edge infotainment'
            ]
        },
        'ssc-tuatara-striker': {
            'name': 'SSC Tuatara Striker',
            'model': 'ssc_tuatara_striker.glb',
            'year': '2023',
            'price': '$1,900,000',
            'engine': '5.9L Twin-Turbo V8',
            'horsepower': '1,750 hp',
            'torque': '1,280 lb-ft',
            'topSpeed': '295 mph',
            'acceleration': '2.5 seconds (0-60 mph)',
            'transmission': '7-Speed Automated Manual',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '11 mpg city / 16 mpg highway',
            'description': 'The SSC Tuatara Striker is designed to be the fastest production car in the world.',
            'features': [
                'World record top speed',
                'Carbon fiber monocoque',
                'Active aerodynamics',
                'Track-focused suspension',
                'Lightweight construction',
                'Advanced telemetry system'
            ]
        },
        'tesla-model-3': {
            'name': 'Tesla Model 3',
            'model': 'tesla_m3_model.glb',
            'year': '2023',
            'price': '$40,000',
            'engine': 'Electric Motor',
            'horsepower': '283 hp',
            'torque': '317 lb-ft',
            'topSpeed': '140 mph',
            'acceleration': '5.3 seconds (0-60 mph)',
            'transmission': 'Single-Speed Direct Drive',
            'drivetrain': 'Rear-Wheel Drive',
            'fuelEconomy': '272 miles range',
            'description': 'The Tesla Model 3 has revolutionized the electric vehicle market with its combination of performance and efficiency.',
            'features': [
                'Electric powertrain',
                'Autopilot capability',
                'Over-the-air updates',
                'Minimalist interior design',
                'Supercharger network access',
                'Premium sound system'
            ]
        },
        'tata-tiago': {
            'name': 'Tata Tiago',
            'model': 'tata_tiago.glb',
            'year': '2023',
            'price': '$8,000',
            'engine': '1.2L Petrol',
            'horsepower': '86 hp',
            'torque': '113 lb-ft',
            'topSpeed': '93 mph',
            'acceleration': '12.3 seconds (0-60 mph)',
            'transmission': '5-Speed Manual',
            'drivetrain': 'Front-Wheel Drive',
            'fuelEconomy': '23 mpg city / 33 mpg highway',
            'description': 'The Tata Tiago is an affordable and practical compact car designed for urban mobility.',
            'features': [
                'Compact urban design',
                'Fuel-efficient engine',
                'Modern infotainment system',
                'Safety features',
                'Affordable pricing',
                'Easy maneuverability'
            ]
        },
        'mahindra-scorpio': {
            'name': 'Mahindra Scorpio',
            'model': 'mahindra_scorpio.glb',
            'year': '2023',
            'price': '$15,000',
            'engine': '2.2L Turbo Diesel',
            'horsepower': '130 hp',
            'torque': '300 lb-ft',
            'topSpeed': '93 mph',
            'acceleration': '11.5 seconds (0-60 mph)',
            'transmission': '6-Speed Manual',
            'drivetrain': '4WD',
            'fuelEconomy': '16 mpg city / 22 mpg highway',
            'description': 'The Mahindra Scorpio is a rugged SUV built for Indian roads and tough conditions.',
            'features': [
                '4WD capability',
                'High ground clearance',
                'Robust build quality',
                '7-seater configuration',
                'Powerful diesel engine',
                'Off-road capabilities'
            ]
        },
        'maruti-suzuki-xl6': {
            'name': 'Maruti Suzuki XL6',
            'model': 'maruti_suzuki_xl6.glb',
            'year': '2023',
            'price': '$12,000',
            'engine': '1.5L Petrol',
            'horsepower': '103 hp',
            'torque': '138 lb-ft',
            'topSpeed': '99 mph',
            'acceleration': '11.2 seconds (0-60 mph)',
            'transmission': '5-Speed Manual',
            'drivetrain': 'Front-Wheel Drive',
            'fuelEconomy': '21 mpg city / 28 mpg highway',
            'description': 'The Maruti Suzuki XL6 is a premium MPV that combines style, comfort, and practicality.',
            'features': [
                'Premium MPV design',
                'Captain seats in middle row',
                'Smart infotainment system',
                'Efficient petrol engine',
                '6-seater configuration',
                'Modern styling elements'
            ]
        },
        'bugatti-centodieci': {
            'name': 'Bugatti Centodieci',
            'model': '2019_bugatti_centodieci.glb',
            'year': '2022',
            'price': '$9,000,000',
            'engine': '8.0L Quad-Turbo W16',
            'horsepower': '1,577 hp',
            'torque': '1,180 lb-ft',
            'topSpeed': '236 mph',
            'acceleration': '2.4 seconds (0-60 mph)',
            'transmission': '7-Speed Dual-Clutch',
            'drivetrain': 'All-Wheel Drive',
            'fuelEconomy': '8 mpg city / 14 mpg highway',
            'description': 'A tribute to the legendary EB110, the Centodieci combines Bugatti\'s rich heritage with cutting-edge technology and unparalleled luxury.',
            'features': [
                'Limited production (10 units)',
                'Carbon fiber bodywork',
                'Michelin Pilot Sport Cup 2 tires',
                'Brembo carbon-ceramic brakes',
                'Exclusive interior appointments',
                'Track telemetry system'
            ]
        }
    }
    
    car = car_data.get(car_name.lower())
    if not car:
        return render_template('404.html'), 404
    
    return render_template('car_details.html', car=car)

# Payment Routes
@app.route('/buy/<car_name>')
@login_required
def buy_car(car_name):
    """Initiate car purchase process"""
    # Log user activity for buying car
    log_user_activity(
        user_id=current_user.id,
        activity_type='purchase_initiated',
        description=f'Initiated purchase for {car_name}',
        metadata={'car_name': car_name}
    )
    
    # Get car data (in production, this would be from database)
    car_data = {
        'bugatti-centodieci': {'name': 'Bugatti Centodieci', 'price': 9000000},
        'mclaren-720s': {'name': 'McLaren 720S', 'price': 1200000},
        'maruti-suzuki-xl6': {'name': 'Maruti Suzuki XL6', 'price': 18000},
        'bentley-mulliner-batur': {'name': 'Bentley Mulliner Batur', 'price': 1200000},
        'lamborghini-diablo-sv': {'name': 'Lamborghini Diablo SV', 'price': 300000},
        'tesla-model-3': {'name': 'Tesla Model 3', 'price': 40000},
        'tesla-cybertruck': {'name': 'Tesla Cybertruck', 'price': 2000000},
        'tata-tiago': {'name': 'Tata Tiago', 'price': 8000},
        'rolls-royce-spectre': {'name': 'Rolls Royce Spectre', 'price': 1200000},
        'rolls-royce-ghost': {'name': 'Rolls Royce Ghost', 'price': 1200000},
        'porsche-718-cayman-gt4': {'name': 'Porsche 718 Cayman', 'price': 120000},
        'mercedes-maybach': {'name': 'Mercedes Benz Maybach', 'price': 300000},
        'lamborghini-revuelto': {'name': 'Lamborghini Revuelto', 'price': 650000},
        'ferrari-monza-sp1': {'name': 'Ferrari Monza', 'price': 1750000},
        'bmw-m2-g87': {'name': 'BMW M2 G87', 'price': 65000},
        'aston-martin-v8-vantage': {'name': 'Aston Martin V8 Vantage', 'price': 150000},
        'lamborghini-temerario': {'name': 'Lamborghini Temerario', 'price': 400000},
        'hyundai-ioniq-5n': {'name': 'Hyundai Ioniq 5N', 'price': 67000},
        'jeep-wrangler-rubicon': {'name': 'Jeep Wrangler Rubicon', 'price': 45000},
        'mahindra-scorpio': {'name': 'Mahindra Scorpio', 'price': 15000},
    }
    
    car = car_data.get(car_name.lower())
    if not car:
        flash('Car not found.', 'error')
        return redirect(url_for('cars'))
    
    # Store car info in session for payment process
    session['purchase_car'] = {
        'name': car['name'],
        'slug': car_name.lower(),
        'price': car['price']
    }
    
    return redirect(url_for('payment'))

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    """Handle payment processing"""
    # Check if car is selected for purchase
    if 'purchase_car' not in session:
        flash('Please select a car first.', 'error')
        return redirect(url_for('cars'))
    
    car_info = session['purchase_car']
    form = PaymentForm()
    
    # Pre-fill form with user data
    if request.method == 'GET':
        form.billing_name.data = current_user.username
        form.billing_email.data = current_user.email
    
    if form.validate_on_submit():
        try:
            # Find or create the car in database based on slug
            car_slug = car_info.get('slug', '')
            car_db = Car.query.filter_by(slug=car_slug).first()
            
            # If car doesn't exist in database, create it
            if not car_db:
                # Parse price - remove $ and commas
                price_str = str(car_info['price']).replace('$', '').replace(',', '')
                try:
                    price_numeric = float(price_str)
                except:
                    price_numeric = 0.0
                
                car_db = Car(
                    name=car_info['name'],
                    slug=car_slug,
                    price=price_numeric,
                    category='Premium',
                    description=f'{car_info["name"]} - Premium luxury vehicle'
                )
                db.session.add(car_db)
                db.session.flush()  # Get the ID without committing
            
            # Parse the total amount from car_info
            price_str = str(car_info['price']).replace('$', '').replace(',', '')
            try:
                total_amount = float(price_str)
            except:
                total_amount = 0.0
            
            # Create new order with actual car ID
            order = Order(
                user_id=current_user.id,
                car_id=car_db.id,  # Use actual car ID from database
                total_amount=total_amount,
                payment_status='completed',  # In real app, this would be pending until payment confirmation
                payment_method=form.payment_method.data,
                transaction_id=f"TXN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                billing_name=form.billing_name.data,
                billing_email=form.billing_email.data,
                billing_phone=form.billing_phone.data,
                billing_address=form.billing_address.data
            )
            
            db.session.add(order)
            db.session.commit()
            
            # Clear session data
            session.pop('purchase_car', None)
            
            flash(f'Payment successful! Your order for {car_info["name"]} has been confirmed.', 'success')
            return redirect(url_for('payment_success', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Payment processing failed. Please try again.', 'error')
            print(f"Payment error: {e}")
    
    return render_template('payment.html', form=form, car=car_info)

@app.route('/finance', methods=['GET', 'POST'])
@login_required
def finance():
    """Handle finance options and applications"""
    # Get car details from query parameters or session
    car_id = request.args.get('car_id')
    car_name = request.args.get('car_name', 'Selected Vehicle')
    car_price = request.args.get('price', '$0')
    
    # Convert price to numeric for calculations
    car_price_numeric = 0
    if car_price and car_price != '$0':
        try:
            car_price_numeric = float(car_price.replace('$', '').replace(',', ''))
        except:
            car_price_numeric = 0
    
    if request.method == 'POST':
        try:
            # Handle finance application submission
            finance_app = FinanceApplication(
                user_id=current_user.id,
                car_id=car_id or 1,
                car_name=car_name,
                car_price=car_price,
                full_name=request.form.get('full_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                annual_income=request.form.get('annual_income'),
                employment_status=request.form.get('employment_status'),
                credit_score_range=request.form.get('credit_score'),
                address=request.form.get('address'),
                selected_plan=request.form.get('selected_plan'),
                application_status='pending'
            )
            
            db.session.add(finance_app)
            db.session.commit()
            
            # Log user activity for finance application submission
            log_user_activity(
                user_id=current_user.id,
                activity_type='finance_application',
                description=f'Submitted finance application for {car_name}',
                metadata={
                    'car_name': car_name,
                    'car_price': car_price,
                    'selected_plan': request.form.get('selected_plan'),
                    'annual_income': request.form.get('annual_income'),
                    'application_id': finance_app.id
                }
            )
            
            flash('Finance application submitted successfully! We will contact you within 24 hours.', 'success')
            return redirect(url_for('finance_success', application_id=finance_app.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Application submission failed. Please try again.', 'error')
            print(f"Finance application error: {e}")
    
    return render_template('finance.html', 
                         car_id=car_id,
                         car_name=car_name, 
                         car_price=car_price,
                         car_price_numeric=car_price_numeric)

@app.route('/finance-success/<int:application_id>')
@login_required  
def finance_success(application_id):
    """Finance application success page"""
    application = FinanceApplication.query.filter_by(id=application_id, user_id=current_user.id).first()
    if not application:
        flash('Application not found.', 'error')
        return redirect(url_for('cars'))
    
    return render_template('finance_success.html', application=application)

@app.route('/payment-success/<int:order_id>')
@login_required
def payment_success(order_id):
    """Payment success page"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('cars'))
    
    # Log user activity for successful payment
    log_user_activity(
        user_id=current_user.id,
        activity_type='purchase_completed',
        description=f'Successfully completed purchase of order #{order.id}',
        metadata={
            'order_id': order.id,
            'car_name': order.car.name if order.car else 'Unknown',
            'total_amount': float(order.total_amount),
            'payment_method': order.payment_method
        }
    )
    
    return render_template('payment_success.html', order=order)

@app.route('/my-orders')
@login_required
def my_orders():
    """View user's orders - both car orders and part orders"""
    # Get car orders
    car_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Get part orders
    part_orders = PartOrder.query.filter_by(user_id=current_user.id).order_by(PartOrder.created_at.desc()).all()
    
    return render_template('my_orders.html', orders=car_orders, part_orders=part_orders)

@app.route('/cancel-order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order with fine"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('my_orders'))
    
    if order.order_status == 'cancelled':
        flash('Order is already cancelled.', 'warning')
        return redirect(url_for('my_orders'))
    
    if order.order_status not in ['pending']:
        flash('Cannot cancel this order. Please contact support for assistance.', 'error')
        return redirect(url_for('my_orders'))
    
    try:
        # Calculate cancellation fee (20% of order value, minimum $500)
        cancellation_fee = max(500, order.total_amount * 0.20)
        
        # Update order status and apply fine
        order.order_status = 'cancelled'
        order.cancellation_fee = cancellation_fee
        order.updated_at = datetime.utcnow()
        
        # Log the cancellation activity
        log_user_activity(
            user_id=current_user.id,
            activity_type='order_cancelled',
            description=f'Cancelled order #{order.id} with ${cancellation_fee:.2f} fine',
            metadata={
                'order_id': order.id,
                'original_amount': float(order.total_amount),
                'cancellation_fee': float(cancellation_fee),
                'refund_amount': float(order.total_amount - cancellation_fee)
            }
        )
        
        db.session.commit()
        
        flash(f'Order #{order.id} has been cancelled. A cancellation fee of ${cancellation_fee:.2f} has been applied. You will receive a refund for the remaining amount within 3-5 business days.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling order. Please try again or contact support.', 'error')
        print(f"Cancel order error: {e}")
    
    return redirect(url_for('my_orders'))

@app.route('/download-invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    """
    Generate and download a professional invoice PDF for an order.
    
    Features:
    - Company logo and branding (CarHub purple theme)
    - Professional header layout with logo, company name, and contact info
    - Invoice number formatting (INV-000001)
    - Detailed customer and order information
    - Itemized pricing breakdown with tax and service fees
    - Color-coded payment status
    - Terms and conditions section
    - Professional footer with thank you message
    
    The invoice is styled with:
    - Custom colors (#7c4dff purple theme)
    - Multi-column layouts for better readability
    - Proper spacing and alignment
    - Bordered sections and tables
    """
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    if not PDF_AVAILABLE:
        flash('PDF generation is not available. Please install reportlab: pip install reportlab', 'error')
        return redirect(url_for('my_orders'))
    
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.platypus import Image, PageBreak
    from reportlab.pdfgen.canvas import Canvas
    
    # Create PDF with custom page size and margins
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#7c4dff'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#7c4dff'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Add company logo with proper styling - Header Layout with Blue Glow
    try:
        logo_path = os.path.join('static', 'logo.png')
        if os.path.exists(logo_path):
            # Create logo with better sizing
            logo_img = Image(logo_path, width=70, height=70)
            
            # Wrap logo in a table with blue gradient background for glow effect
            logo_with_glow = Table([[logo_img]], colWidths=[0.95*inch], rowHeights=[0.95*inch])
            logo_with_glow.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E3F2FD')),  # Light blue background
                ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#2196F3')),  # Blue border for glow
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),  # Rounded corners
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            # Company name and tagline
            company_header = Paragraph(
                "<b><font size=24 color='#7c4dff'>CarHub</font></b><br/>"
                "<font size=11 color='#666666'>Premium Vehicle Sales & Service</font>",
                ParagraphStyle('CompanyHeader', parent=styles['Normal'], alignment=TA_LEFT)
            )
            
            # Company contact info
            company_contact = Paragraph(
                "<font size=9 color='#666666'>"
                "123 Luxury Auto Lane<br/>"
                "Premium City, PC 12345<br/>"
                "Phone: +1 (555) 123-4567<br/>"
                "Email: info@carhub.com</font>",
                ParagraphStyle('CompanyContact', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=9)
            )
            
            # Create header table with logo and info
            header_data = [[logo_with_glow, company_header, company_contact]]
            header_table = Table(header_data, colWidths=[1.1*inch, 3.15*inch, 2.25*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(header_table)
            
            # Add a line separator
            line_separator = Table([['']], colWidths=[6.5*inch])
            line_separator.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor('#7c4dff')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(line_separator)
            story.append(Spacer(1, 10))
        else:
            print(f"Logo not found at: {logo_path}")
            # Fallback to text-only header
            story.append(Paragraph("CarHub", title_style))
            story.append(Paragraph("Premium Vehicle Sales & Service", subtitle_style))
            story.append(Spacer(1, 10))
    except Exception as e:
        print(f"Logo error: {e}")
        # Fallback to text-only header
        story.append(Paragraph("CarHub", title_style))
        story.append(Paragraph("Premium Vehicle Sales & Service", subtitle_style))
        story.append(Spacer(1, 10))
    
    # Invoice title with border
    invoice_header = [
        [Paragraph("<b>INVOICE</b>", ParagraphStyle('InvoiceHeader', parent=styles['Heading1'], fontSize=24, textColor=colors.white, alignment=TA_CENTER))]
    ]
    invoice_table = Table(invoice_header, colWidths=[6.5*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#7c4dff')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 20))
    
    # Invoice details and customer info side by side
    invoice_details_data = [
        [Paragraph("<b>Invoice Details</b>", heading_style), ''],
        [Paragraph("<b>Invoice Number:</b>", styles['Normal']), Paragraph(f"INV-{order.id:06d}", styles['Normal'])],
        [Paragraph("<b>Invoice Date:</b>", styles['Normal']), Paragraph(order.created_at.strftime('%B %d, %Y'), styles['Normal'])],
        [Paragraph("<b>Transaction ID:</b>", styles['Normal']), Paragraph(order.transaction_id or 'N/A', styles['Normal'])],
        [Paragraph("<b>Payment Status:</b>", styles['Normal']), Paragraph(order.payment_status.title(), ParagraphStyle('Status', parent=styles['Normal'], textColor=colors.HexColor('#28a745') if order.payment_status == 'completed' else colors.HexColor('#ffc107')))],
    ]
    
    customer_details_data = [
        [Paragraph("<b>Bill To</b>", heading_style), ''],
        [Paragraph("<b>Name:</b>", styles['Normal']), Paragraph(order.billing_name, styles['Normal'])],
        [Paragraph("<b>Email:</b>", styles['Normal']), Paragraph(order.billing_email, styles['Normal'])],
        [Paragraph("<b>Phone:</b>", styles['Normal']), Paragraph(order.billing_phone, styles['Normal'])],
        [Paragraph("<b>Address:</b>", styles['Normal']), Paragraph(order.billing_address, styles['Normal'])],
    ]
    
    # Create two column layout
    details_table = Table([[
        Table(invoice_details_data, colWidths=[1.3*inch, 1.9*inch]),
        Table(customer_details_data, colWidths=[1.3*inch, 1.9*inch])
    ]], colWidths=[3.25*inch, 3.25*inch])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 25))
    
    # Line items header
    story.append(Paragraph("<b>Order Details</b>", heading_style))
    story.append(Spacer(1, 10))
    
    # Calculate subtotal, tax, and fees
    subtotal = order.total_amount / 1.1  # Assuming 10% tax/fees included
    tax_amount = subtotal * 0.08  # 8% tax
    service_fee = subtotal * 0.02  # 2% service fee
    
    # Line items table
    line_items_data = [
        [
            Paragraph("<b>Description</b>", ParagraphStyle('TableHeader', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold')),
            Paragraph("<b>Quantity</b>", ParagraphStyle('TableHeader', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>Unit Price</b>", ParagraphStyle('TableHeader', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            Paragraph("<b>Total</b>", ParagraphStyle('TableHeader', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT))
        ],
        [
            Paragraph(f"<b>{order.car.name if order.car else 'Vehicle'}</b><br/><font size=8>Premium automotive vehicle</font>", styles['Normal']),
            Paragraph("1", ParagraphStyle('TableCell', parent=styles['Normal'], alignment=TA_CENTER)),
            Paragraph(f"${subtotal:,.2f}", ParagraphStyle('TableCell', parent=styles['Normal'], alignment=TA_RIGHT)),
            Paragraph(f"${subtotal:,.2f}", ParagraphStyle('TableCell', parent=styles['Normal'], alignment=TA_RIGHT))
        ],
    ]
    
    line_items_table = Table(line_items_data, colWidths=[3.25*inch, 1*inch, 1.25*inch, 1.5*inch])
    line_items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c4dff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    story.append(line_items_table)
    story.append(Spacer(1, 15))
    
    # Payment method info
    payment_method_display = order.payment_method.replace('_', ' ').title() if order.payment_method else 'N/A'
    
    # Summary table (right aligned)
    summary_data = [
        ['Subtotal:', f'${subtotal:,.2f}'],
        ['Tax (8%):', f'${tax_amount:,.2f}'],
        ['Service Fee (2%):', f'${service_fee:,.2f}'],
        ['', ''],  # Spacer row
        [Paragraph('<b>Total Amount:</b>', ParagraphStyle('BoldTotal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12)), 
         Paragraph(f'<b>${order.total_amount:,.2f}</b>', ParagraphStyle('BoldTotal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#7c4dff')))],
        ['', ''],  # Spacer row
        ['Payment Method:', payment_method_display],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 12),
        ('LINEABOVE', (0, 4), (-1, 4), 2, colors.HexColor('#7c4dff')),
        ('LINEBELOW', (0, 4), (-1, 4), 2, colors.HexColor('#7c4dff')),
        ('TOPPADDING', (0, 4), (-1, 4), 10),
        ('BOTTOMPADDING', (0, 4), (-1, 4), 10),
        ('TOPPADDING', (0, 3), (-1, 3), 0),
        ('BOTTOMPADDING', (0, 3), (-1, 3), 0),
        ('TOPPADDING', (0, 5), (-1, 5), 0),
        ('BOTTOMPADDING', (0, 5), (-1, 5), 0),
    ]))
    
    # Align summary to right
    summary_wrapper = Table([[summary_table]], colWidths=[6.5*inch])
    summary_wrapper.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))
    story.append(summary_wrapper)
    story.append(Spacer(1, 30))
    
    # Additional notes section
    notes_style = ParagraphStyle(
        'Notes',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        leading=12
    )
    
    story.append(Paragraph("<b>Notes & Terms:</b>", heading_style))
    notes = Paragraph(
        "• This invoice is a confirmation of your vehicle purchase.<br/>"
        "• All sales are subject to our terms and conditions.<br/>"
        "• Warranty information and registration documents will be provided separately.<br/>"
        "• For any questions or concerns, please contact our customer service team.<br/>"
        "• Payment receipt has been sent to your registered email address.",
        notes_style
    )
    story.append(notes)
    story.append(Spacer(1, 30))
    
    # Footer with border
    footer_text = Paragraph(
        "<b>Thank You For Your Business!</b><br/>"
        "We appreciate your trust in CarHub. Enjoy your premium vehicle experience!<br/><br/>"
        "<font size=8>This is a computer-generated invoice and does not require a signature.<br/>"
        "For support, contact us at support@carhub.com or call +1 (555) 123-4567</font>",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.HexColor('#666666'))
    )
    
    footer_table = Table([[footer_text]], colWidths=[6.5*inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
    ]))
    story.append(footer_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Log invoice download activity
    log_user_activity(
        user_id=current_user.id,
        activity_type='invoice_download',
        description=f'Downloaded invoice for order #{order.id}',
        metadata={'order_id': order.id, 'invoice_number': f'INV-{order.id:06d}'}
    )
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=CarHub_Invoice_{order.id:06d}.pdf'
    
    return response

@app.route('/create-test-order')
@login_required
def create_test_order():
    """Create a test order for demonstration (development only)"""
    # Get a random car
    car = Car.query.first()
    if not car:
        flash('No cars available in database', 'error')
        return redirect(url_for('cars'))
    
    # Create test order
    import random
    import string
    
    test_order = Order(
        user_id=current_user.id,
        car_id=car.id,
        total_amount=car.price * 1.1,  # Including taxes and fees
        payment_status='completed',
        payment_method='credit_card',
        transaction_id=''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        billing_name=current_user.username,
        billing_email=current_user.email,
        billing_phone='+1-555-0123',
        billing_address='123 Test Street, Test City, TC 12345'
    )
    
    db.session.add(test_order)
    db.session.commit()
    
    flash(f'Test order created successfully! Order ID: {test_order.id}', 'success')
    return redirect(url_for('my_orders'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

def save_profile_picture(form_file):
    """Save uploaded profile picture and return filename"""
    if not form_file:
        return None
    
    # Generate secure filename
    filename = secure_filename(form_file.filename)
    
    # Add timestamp to prevent filename conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename = timestamp + filename
    
    # Save file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    form_file.save(file_path)
    
    # Return relative path for database storage
    return f'uploads/profiles/{filename}'

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    
    if request.method == 'GET':
        # Pre-populate form with existing user data
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.date_of_birth.data = current_user.date_of_birth
        form.gender.data = current_user.gender
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.zip_code.data = current_user.zip_code
        form.country.data = current_user.country
        form.occupation.data = current_user.occupation
        form.bio.data = current_user.bio
        form.preferred_contact_method.data = current_user.preferred_contact_method
    
    if form.validate_on_submit():
        try:
            # Handle profile picture upload
            if form.profile_picture.data:
                profile_picture_path = save_profile_picture(form.profile_picture.data)
                if profile_picture_path:
                    current_user.profile_picture = profile_picture_path
            
            # Update user profile
            current_user.username = form.username.data
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone = form.phone.data
            current_user.date_of_birth = form.date_of_birth.data
            current_user.gender = form.gender.data
            current_user.address = form.address.data
            current_user.city = form.city.data
            current_user.state = form.state.data
            current_user.zip_code = form.zip_code.data
            current_user.country = form.country.data
            current_user.occupation = form.occupation.data
            current_user.bio = form.bio.data
            current_user.preferred_contact_method = form.preferred_contact_method.data
            current_user.profile_updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile. Please try again.', 'error')
            print(f"Profile update error: {e}")
    
    return render_template('edit_profile.html', form=form, user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# Chatbot route
@app.route('/chat')
def chat_page():
    """Render the standalone chat page"""
    return render_template('chat.html')

@app.route('/test-chatbot')
def test_chatbot_page():
    """Test page for chatbot functionality"""
    return render_template('test_chatbot.html')

@app.route('/simple-test')
def simple_test():
    """Simple test page"""
    return render_template('simple_test.html')

@app.route('/basic-chat')
def basic_chat():
    """Basic chat test page"""
    return render_template('basic_chat.html')

@app.route('/diagnostic')
def diagnostic():
    """Chatbot diagnostic page"""
    return render_template('diagnostic.html')

# Admin Panel Routes
@app.route('/admin')
@login_required
def admin_panel():
    """Main admin panel - restricted to admin@carhub.com only"""
    if not is_admin(current_user):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get dashboard statistics
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_finance_apps = FinanceApplication.query.count()
    recent_activities = UserActivity.query.order_by(UserActivity.created_at.desc()).limit(10).all()
    
    # Revenue calculation
    completed_orders = Order.query.filter_by(payment_status='completed').all()
    total_revenue = sum(order.total_amount for order in completed_orders)
    
    # Recent users (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_this_week = User.query.filter(User.created_at >= week_ago).count()
    
    stats = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_finance_apps': total_finance_apps,
        'total_revenue': total_revenue,
        'new_users_this_week': new_users_this_week,
        'recent_activities': recent_activities
    }
    
    return render_template('admin_panel.html', stats=stats)

@app.route('/admin/users')
@login_required
def admin_users():
    """Admin users management"""
    if not is_admin(current_user):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_users.html', users=users, search=search)

@app.route('/admin/orders')
@login_required
def admin_orders():
    """Admin orders management"""
    if not is_admin(current_user):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all', type=str)
    
    query = Order.query
    if status_filter != 'all':
        query = query.filter(Order.payment_status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_orders.html', orders=orders, status_filter=status_filter)

@app.route('/admin/activities')
@login_required
def admin_activities():
    """Admin activity logs"""
    if not is_admin(current_user):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    activity_type = request.args.get('type', 'all', type=str)
    user_id = request.args.get('user_id', type=int)
    
    query = UserActivity.query
    if activity_type != 'all':
        query = query.filter(UserActivity.activity_type == activity_type)
    if user_id:
        query = query.filter(UserActivity.user_id == user_id)
    
    activities = query.order_by(UserActivity.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin_activities.html', activities=activities, 
                         activity_type=activity_type, user_id=user_id)

@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    """Admin user detail view"""
    if not is_admin(current_user):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    user_finance_apps = FinanceApplication.query.filter_by(user_id=user_id).order_by(FinanceApplication.created_at.desc()).all()
    user_activities = UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.created_at.desc()).limit(50).all()
    
    return render_template('admin_user_detail.html', 
                         user=user, 
                         orders=user_orders,
                         finance_apps=user_finance_apps,
                         activities=user_activities)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Initialize database
def create_tables():
    """Create database tables"""
    try:
        # Ensure instance directory exists
        if not os.path.exists('instance'):
            os.makedirs('instance')
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Initialize chatbot
try:
    from chatbot import create_chatbot_routes
    chatbot_instance = create_chatbot_routes(app, db, User, Car, Order)
    print("✅ Chatbot initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing chatbot: {e}")
    print("💡 Make sure you have set your OPENAI_API_KEY in your .env file")
        
if __name__ == '__main__':
    with app.app_context():
        # Create tables
        if not os.path.exists('instance'):
            os.makedirs('instance')
        db.create_all()
        print("Database initialized!")
    
    app.run(debug=True)
