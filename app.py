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
import time
from datetime import datetime, timedelta
from io import BytesIO
from dotenv import load_dotenv

# Google OAuth imports
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

# Load environment variables from config folder
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

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
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_DEBUG'] = True  # Enable debug mode for more detailed logs
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
# Remove any spaces from password (common copy-paste error with app passwords)
mail_password = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_PASSWORD'] = mail_password.replace(' ', '') if mail_password else mail_password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False
# Ensure default sender is set properly
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

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    condition = db.Column(db.String(20), default='New')
    warranty = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Part {self.name}>'

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
    submit = SubmitField('Send OTP')

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
def forgot_password_legacy():
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
                flash('Password reset OTP has been sent to your email.', 'info')
            else:
                flash('Error sending email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset OTP has been sent.', 'info')
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password_legacy'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid reset token.', 'error')
        return redirect(url_for('forgot_password_legacy'))
    
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

@app.route('/parts/<int:part_id>')
def part_detail(part_id):
    # Get the part from the database
    part = Part.query.get_or_404(part_id)
    
    # Log user activity for viewing part details
    if current_user.is_authenticated:
        log_user_activity(
            user_id=current_user.id,
            activity_type='part_view',
            description=f'Viewed part details for {part.name}',
            metadata={'part_id': part_id, 'part_name': part.name}
        )
        
    return render_template('part_detail.html', product=part)

@app.route('/inventory')
def inventory():
    # Get parameter to determine what to display
    display_type = request.args.get('type', 'cars')
    
    if display_type == 'parts':
        # Get all parts from the database
        parts = Part.query.all()
        
        # Create a list of parts with their details
        parts_list = []
        for part in parts:
            part_detail = {
                'id': part.id,
                'name': part.name,
                'price': part.price,
                'image': f'parts/{part.image}',
                'brand': part.brand,
                'type': 'part'
            }
            parts_list.append(part_detail)
            
        return render_template('inventory.html', items=parts_list, display_type='parts')
    else:
        # Sample inventory data - in a real app, this would come from a database
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
                'image': 'lamborghini_revuelto.glb'
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
            'image': 'bugatti_centodieci.glb'
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
            'image': 'ferrari_296.glb'
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
            'image': 'mclaren.glb'
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
            'image': 'porsche_718_cayman_gt4.glb'
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
            'image': 'aston_martin_v8_vantage.glb'
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
            'image': 'tesla_cybertruck.glb'
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
            'image': 'bmw_m2_g87.glb'
        }
    ]
        # Convert to format consistent with parts list
        car_list = []
        for car in inventory_cars:
            car_detail = {
                'id': car['id'],
                'name': car['name'],
                'price': car['price'],
                'image': car['image'],
                'brand': car.get('name', '').split(' ')[0],  # Extract brand from name
                'type': 'car'
            }
            car_list.append(car_detail)
            
        return render_template('inventory.html', items=car_list, display_type='cars')

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
        form.billing_name.data = current_user.first_name + " " + current_user.last_name if current_user.first_name and current_user.last_name else current_user.username
        form.billing_email.data = current_user.email
        form.billing_phone.data = current_user.phone if hasattr(current_user, 'phone') else ''
        form.billing_address.data = current_user.address if hasattr(current_user, 'address') else ''

    if request.method == 'POST':
        # Manually get the payment_method from form data to handle custom validation
        payment_method = request.form.get('payment_method')
        if payment_method:
            form.payment_method.data = payment_method
        
        if form.validate_on_submit():
            try:
                # Resolve car from database using slug stored in session
                car_slug = car_info.get('slug')
                car_obj = None
                if car_slug:
                    car_obj = Car.query.filter_by(slug=car_slug).first()

                if car_obj is None:
                    app.logger.error(f"No car found with slug {car_slug}")
                    flash("Could not find the selected car. Please try again.", "error")
                    return redirect(url_for('cars'))

                # Calculate total amount including fees (10% for tax and processing)
                total_amount = car_obj.price * 1.1 if car_obj else float(car_info.get('price', 0)) * 1.1

                # Create a new order with pending payment status
                order = Order(
                    user_id=current_user.id,
                    car_id=car_obj.id,
                    total_amount=total_amount,
                    payment_status='pending',
                    payment_method=form.payment_method.data,
                    transaction_id=None,
                    billing_name=form.billing_name.data,
                    billing_email=form.billing_email.data,
                    billing_phone=form.billing_phone.data,
                    billing_address=form.billing_address.data
                )

                db.session.add(order)
                db.session.commit()

                # Process the payment (this is a safe, simulated processor for development)
                success, txn_id, message = process_payment(form, order)

                if success:
                    order.payment_status = 'completed'
                    order.transaction_id = txn_id or f"TXN_{secrets.token_hex(8)}"
                    order.order_status = 'processing'
                    db.session.commit()

                    # Log the successful payment
                    log_user_activity(
                        user_id=current_user.id,
                        activity_type='payment_successful',
                        description=f'Successfully processed payment for {car_obj.name}',
                        metadata={
                            'order_id': order.id,
                            'car_id': car_obj.id,
                            'amount': float(total_amount),
                            'payment_method': form.payment_method.data
                        }
                    )

                    # Clear session data after successful payment
                    session.pop('purchase_car', None)

                    flash(f'Payment successful! Your order for {car_info["name"]} has been confirmed.', 'success')
                    return redirect(url_for('payment_success', order_id=order.id))
                else:
                    order.payment_status = 'failed'
                    db.session.commit()
                    
                    # Log the failed payment
                    log_user_activity(
                        user_id=current_user.id,
                        activity_type='payment_failed',
                        description=f'Payment failed for {car_obj.name}: {message}',
                        metadata={
                            'order_id': order.id,
                            'car_id': car_obj.id,
                            'amount': float(total_amount),
                            'payment_method': form.payment_method.data,
                            'error': message
                        }
                    )
                    
                    flash(f'Payment failed: {message}', 'error')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Payment error: {str(e)}")
                flash('Payment processing failed. Please try again.', 'error')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')

    return render_template('payment.html', form=form, car=car_info)


def process_payment(form: PaymentForm, order: Order):
    """Simulate a payment gateway interaction.

    Rules:
    - For 'credit_card' method, lightly validate card fields and return success if basic checks pass.
    - For 'paypal' or other methods, simulate success with appropriate delays.
    - This function does NOT perform any real network calls or charge cards.

    Returns tuple (success: bool, transaction_id: Optional[str], message: str)
    """
    try:
        method = (form.payment_method.data or '').lower()
        app.logger.info(f"Processing payment for order {order.id} with method {method}")

        # Basic allowed methods
        allowed = {'credit_card', 'paypal', 'bank_transfer', 'cash'}
        if method not in allowed:
            app.logger.error(f"Unsupported payment method: {method}")
            return False, None, 'Unsupported payment method.'

        # For development, we'll add a small delay to simulate network latency
        time.sleep(1.5)

        # If credit card, do validation
        if method == 'credit_card':
            card = (form.card_number.data or '').replace(' ', '')
            exp = (form.card_expiry.data or '').strip()
            cvv = (form.card_cvv.data or '').strip()

            if not card:
                return False, None, 'Card number is required.'
            if not exp:
                return False, None, 'Expiration date is required.'
            if not cvv:
                return False, None, 'CVV is required.'

            if not (card.isdigit() and 12 <= len(card) <= 19):
                return False, None, 'Invalid card number. Must be 12-19 digits.'
            if not (cvv.isdigit() and 3 <= len(cvv) <= 4):
                return False, None, 'Invalid CVV. Must be 3-4 digits.'
            
            # Basic expiry validation (MM/YY format)
            if not exp or '/' not in exp:
                return False, None, 'Invalid expiry date format. Use MM/YY.'
            
            try:
                month, year = exp.split('/')
                month = int(month)
                year = int('20' + year) if len(year) == 2 else int(year)
                
                if not (1 <= month <= 12):
                    return False, None, 'Invalid month in expiry date.'
                
                # Check if card is expired
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                if year < current_year or (year == current_year and month < current_month):
                    return False, None, 'Card has expired.'
            except ValueError:
                return False, None, 'Invalid expiry date format.'

            # Do Luhn algorithm validation (basic checksum for card numbers)
            if not is_valid_card_number(card):
                # For testing, we'll still accept cards that fail checksum
                app.logger.warning(f"Card number failed checksum: {card[:6]}...{card[-4:]}")
                # But we'll warn in logs without failing the payment

            # Simulate rejection for specific test values
            if card.endswith('0000'):
                return False, None, 'Card declined by issuer.'

            # Simulate approval for development/testing
            txn = f"CC_{secrets.token_hex(12)}"
            return True, txn, 'Approved'

        # Simulate success for PayPal
        if method == 'paypal':
            # Add slightly more delay for PayPal to simulate redirect
            time.sleep(0.5)
            txn = f"PP_{secrets.token_hex(12)}"
            return True, txn, 'PayPal payment approved'

        # Simulate bank transfer
        if method == 'bank_transfer':
            txn = f"BT_{secrets.token_hex(12)}"
            return True, txn, 'Bank transfer confirmed'
        
        # Simulate cash
        if method == 'cash':
            txn = f"CASH_{secrets.token_hex(8)}"
            return True, txn, 'Cash payment recorded'

        # Fallback for any other method
        txn = f"{method.upper()}_{secrets.token_hex(10)}"
        return True, txn, 'Payment approved'

    except Exception as e:
        app.logger.error(f"Payment processing error: {str(e)}")
        return False, None, f'Processing error: {str(e)}'

def is_valid_card_number(card_number):
    """
    Validate a card number using the Luhn algorithm.
    This is a basic checksum used by credit card companies.
    """
    digits = [int(d) for d in card_number if d.isdigit()]
    checksum = 0
    
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:  # Odd positions (from right to left)
            doubled = digit * 2
            checksum += doubled if doubled < 10 else doubled - 9
        else:  # Even positions
            checksum += digit
            
    return checksum % 10 == 0

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
    """View user's orders"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

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
    """Download invoice PDF for an order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    if not PDF_AVAILABLE:
        flash('PDF generation is not available. Please install reportlab: pip install reportlab', 'error')
        return redirect(url_for('my_orders'))
    
    # Create PDF
    buffer = BytesIO()
    
    # Set up the document with margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=36, 
        rightMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    
    # Get the width and height of the page
    width, height = A4
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Custom title style with CarHub colors
    title_style = styles['Title'].clone('CarHubTitle')
    title_style.fontName = 'Helvetica-Bold'
    title_style.fontSize = 24
    title_style.leading = 30
    title_style.alignment = 1  # Centered
    title_style.textColor = colors.HexColor('#7c4dff')  # Primary purple color
    
    # Custom header style
    header_style = styles['Heading2'].clone('CarHubHeader')
    header_style.fontName = 'Helvetica-Bold'
    header_style.fontSize = 14
    header_style.textColor = colors.HexColor('#23235b')  # Dark blue
    
    # Custom normal text style
    normal_style = styles['Normal'].clone('CarHubNormal')
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 10
    normal_style.leading = 12
    
    # Custom bold text style
    bold_style = styles['Normal'].clone('CarHubBold')
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 10
    bold_style.leading = 12
    
    # Generate invoice number (combination of order ID and timestamp)
    invoice_number = f"INV-{order.id}-{order.created_at.strftime('%Y%m%d')}"
    
    # Create story container for Flowables
    story = []
    
    # Create custom drawing function for the first page
    def add_first_page_elements(canvas, doc):
        # Save canvas state
        canvas.saveState()
        
        # Add watermark if paid
        if order.payment_status.lower() == 'paid':
            watermark_path = os.path.join(app.root_path, 'static', 'paid_watermark.png')
            if os.path.exists(watermark_path):
                # Position the watermark in the center of the page with transparency
                canvas.saveState()
                canvas.setFillAlpha(0.15)  # Set transparency
                canvas.drawImage(watermark_path, width/2 - 100, height/2 - 100, 
                                width=200, height=200, preserveAspectRatio=True)
                canvas.restoreState()
        
        # Add logo in top left corner
        logo_path = os.path.join(app.root_path, 'static', 'logo.png')
        if os.path.exists(logo_path):
            # Position logo at top left
            canvas.drawImage(logo_path, 36, height - 90, width=120, height=60, preserveAspectRatio=True)
        
        # Add company info in top right with enhanced styling
        company_info = [
            "CarHub Premium Auto",
            "123 Luxury Drive",
            "Automotive City, AC 98765",
            "support@carhub.com",
            "+1 (555) 123-4567",
            "www.carhub.com"
        ]
        
        # Draw a light background for company info
        canvas.setFillColor(colors.HexColor('#f8f9fa'))
        canvas.roundRect(width - 210, height - 100, 180, 80, 5, fill=1, stroke=0)
        
        text_obj = canvas.beginText(width - 200, height - 50)
        text_obj.setFont("Helvetica-Bold", 10)
        text_obj.setFillColor(colors.HexColor('#23235b'))
        text_obj.textLine(company_info[0])  # Company name in bold
        text_obj.setFont("Helvetica", 9)
        for line in company_info[1:]:
            text_obj.textLine(line)
        canvas.drawText(text_obj)
        
        # Add a decorative divider line below the header
        canvas.setStrokeColor(colors.HexColor('#7c4dff'))
        canvas.setLineWidth(2)
        canvas.line(36, height - 100, width - 36, height - 100)
        
        # Add a subtle shadow line
        canvas.setStrokeColor(colors.HexColor('#e6e6fa'))
        canvas.setLineWidth(1)
        canvas.line(36, height - 102, width - 36, height - 102)
        
        # Add invoice title with enhanced styling
        canvas.saveState()
        # Draw background for invoice title
        canvas.setFillColor(colors.HexColor('#f0f0ff'))
        canvas.roundRect(width/2 - 150, height - 145, 300, 30, 10, fill=1, stroke=0)
        
        canvas.setFont("Helvetica-Bold", 18)
        canvas.setFillColor(colors.HexColor('#23235b'))
        canvas.drawCentredString(width/2, height - 130, f"INVOICE #{invoice_number}")
        canvas.restoreState()
        
        # Generate QR code data - in a real implementation you'd use the qrcode library
        qr_data = f"INVOICE:{invoice_number}|ORDER:{order.id}|DATE:{order.created_at.strftime('%Y-%m-%d')}"
        
        # Draw a border around the QR code area
        canvas.setStrokeColor(colors.HexColor('#7c4dff'))
        canvas.roundRect(width - 100, 30, 60, 70, 5, fill=0, stroke=1)
        
        # Add QR code for invoice verification (simulated as a square with internal pattern)
        canvas.setFillColor(colors.black)
        canvas.rect(width - 90, 40, 50, 50, fill=0)
        
        # Add some patterns to simulate a QR code (this is just for visual effect)
        canvas.setFillColor(colors.black)
        for i in range(3):
            for j in range(3):
                if (i + j) % 2 == 0:  # Checker pattern
                    canvas.rect(width - 90 + i*16, 40 + j*16, 16, 16, fill=1)
        
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(width - 65, 30, "Scan to verify invoice")
        
        # Add footer with improved styling
        # Draw background for footer
        canvas.setFillColor(colors.HexColor('#f8f9fa'))
        canvas.roundRect(36, 30, width - 72, 50, 5, fill=1, stroke=0)
        
        # Add terms & conditions
        terms_text = canvas.beginText(46, 70)
        terms_text.setFont("Helvetica-Bold", 9)
        terms_text.setFillColor(colors.HexColor('#23235b'))
        terms_text.textLine("Terms & Conditions:")
        terms_text.setFont("Helvetica", 8)
        terms_text.setFillColor(colors.black)
        terms_text.textLine("Payment is due within 30 days. CarHub reserves ownership until full payment.")
        terms_text.textLine("For questions about this invoice, contact our customer support.")
        canvas.drawText(terms_text)
        
        # Add page number with decorative element
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 36, 36, f"Page {doc.page}")
        
        # Add decorative element to page number
        canvas.setStrokeColor(colors.HexColor('#7c4dff'))
        canvas.line(width - 80, 34, width - 36, 34)
        
        # Restore canvas state
        canvas.restoreState()
    
    # Add spacer for logo area
    story.append(Spacer(1, 140))
    
    # Add date and customer info in two-column layout
    customer_data = [
        ["BILL TO:", "INVOICE DETAILS:"],
        [order.billing_name, f"Invoice Date: {order.created_at.strftime('%B %d, %Y')}"],
        [order.billing_address or "N/A", f"Due Date: {(order.created_at + timedelta(days=30)).strftime('%B %d, %Y')}"],
        [order.billing_email, f"Order ID: #{order.id}"],
        [order.billing_phone or "N/A", f"Transaction ID: {order.transaction_id}"]
    ]
    
    customer_table = Table(customer_data, colWidths=[doc.width/2 - 20, doc.width/2 - 20])
    customer_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, 1), (-1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#23235b')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(customer_table)
    story.append(Spacer(1, 20))
    
    # Add vehicle info section with enhanced styling
    # Create a styled header with background
    vehicle_header = Paragraph("VEHICLE DETAILS", header_style)
    header_background = Table([[vehicle_header]], colWidths=[doc.width])
    header_background.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f0ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(header_background)
    story.append(Spacer(1, 10))
    
    # Create vehicle info table
    vehicle_info = []
    
    # Header row
    vehicle_info.append(["ITEM", "DESCRIPTION", "PRICE"])
    
    # Vehicle row with enhanced details
    if order.car:
        # Extract more details from the car if available
        car_details = [
            f"Make/Model: {order.car.name}",
            f"VIN: {order.car.vin if hasattr(order.car, 'vin') else 'Not Available'}",
            f"Color: {order.car.color if hasattr(order.car, 'color') else 'Standard'}"
        ]
        
        # Add year and engine details if available
        if hasattr(order.car, 'year'):
            car_details.insert(1, f"Year: {order.car.year}")
        
        if hasattr(order.car, 'engine'):
            car_details.append(f"Engine: {order.car.engine}")
        
        if hasattr(order.car, 'transmission'):
            car_details.append(f"Transmission: {order.car.transmission}")
            
        vehicle_info.append([
            "Premium Vehicle",
            "\n".join(car_details),
            f"${order.car.price:,.2f}" if hasattr(order.car, 'price') else "N/A"
        ])
    else:
        vehicle_info.append(["Vehicle", "Information Not Available", "N/A"])
    
    # Add fees and taxes
    base_price = order.car.price if order.car and hasattr(order.car, 'price') else (order.total_amount / 1.1)
    
    # Add delivery fee if applicable
    if hasattr(order, 'delivery_fee') and order.delivery_fee:
        delivery_fee = order.delivery_fee
    else:
        delivery_fee = base_price * 0.01  # Default 1% delivery fee
        
    vehicle_info.append(["Delivery Fee", "Vehicle delivery and handling", f"${delivery_fee:,.2f}"])
    vehicle_info.append(["Processing Fee", "Documentation and registration", f"${base_price * 0.02:,.2f}"])
    vehicle_info.append(["Tax", "Sales tax (8%)", f"${base_price * 0.08:,.2f}"])
    
    # Add subtotal line
    vehicle_info.append(["", "Subtotal", f"${base_price + delivery_fee + (base_price * 0.02) + (base_price * 0.08):,.2f}"])
    
    # Style the vehicle table
    vehicle_table = Table(vehicle_info, colWidths=[doc.width * 0.2, doc.width * 0.5, doc.width * 0.2])
    vehicle_table_style = TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c4dff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Vehicle row styling
        ('FONT', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Right align all prices
        
        # Alternate row colors
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#f8f9fa')),
        
        # All cell borders
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#7c4dff')),
        
        # Subtotal row styling
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONT', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6e6fa')),
        ('SPAN', (0, -1), (-2, -1)),  # Span the first two columns
        ('ALIGN', (-2, -1), (-2, -1), 'RIGHT'),  # Right align "Subtotal" text
    ])
    
    # Apply the style to the table and add to story
    vehicle_table.setStyle(vehicle_table_style)
    story.append(vehicle_table)
    story.append(Spacer(1, 20))
    
    # Create payment status indicator with color-coded badge
    status_color = colors.HexColor('#4CAF50') if order.payment_status.lower() == 'paid' else colors.HexColor('#FF9800')
    
    # Add payment summary header
    payment_header = Paragraph("PAYMENT SUMMARY", header_style)
    story.append(payment_header)
    story.append(Spacer(1, 10))
    
    # Create payment info with enhanced styling
    payment_data = [
        ["Payment Date:", order.created_at.strftime('%B %d, %Y')],
        ["Transaction ID:", order.transaction_id if hasattr(order, 'transaction_id') and order.transaction_id else "N/A"],
        ["Payment Method:", order.payment_method.replace('_', ' ').title()],
        ["Payment Status:", ""]  # Empty cell for custom status badge
    ]
    
    # Create the payment table
    payment_table = Table(payment_data, colWidths=[doc.width * 0.3, doc.width * 0.6])
    
    # Style the payment table
    payment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#23235b')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    
    story.append(payment_table)
    
    # Create a separate styled status badge
    status_text = order.payment_status.upper()
    status_table = Table([["", status_text]], colWidths=[10, doc.width * 0.3])
    status_table.setStyle(TableStyle([
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('BACKGROUND', (1, 0), (1, 0), status_color),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
        ('TOPPADDING', (1, 0), (1, 0), 6),
        ('BOTTOMPADDING', (1, 0), (1, 0), 6),
    ]))
    
    story.append(Spacer(1, -30))  # Negative spacer to position the badge at the right location
    story.append(status_table)
    story.append(Spacer(1, 20))
    
    # Create total amount section with gradient background
    total_info = [
        ["TOTAL AMOUNT DUE:", f"${order.total_amount:,.2f}"]
    ]
    
    # Apply different styling based on payment status
    if order.payment_status.lower() == 'paid':
        total_info[0][0] = "TOTAL AMOUNT PAID:"
    
    total_table = Table(total_info, colWidths=[doc.width * 0.5, doc.width * 0.4])
    total_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 16),  # Larger font for total amount
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#23235b')),  # Dark background
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),  # White text
        ('TOPPADDING', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
        ('BOX', (0, 0), (1, 0), 2, colors.HexColor('#7c4dff')),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 30))
    
    # Create a styled box for the thank you message
    thank_you_paragraphs = [
        Paragraph("<b>Thank you for choosing CarHub Premium Auto!</b>", bold_style),
        Spacer(1, 5),
        Paragraph("We value your business and look forward to serving you again. Your satisfaction is our top priority.", normal_style),
        Spacer(1, 10),
        Paragraph("For any questions or concerns regarding this invoice, please contact our customer service team at <b>support@carhub.com</b> or call us at <b>+1 (555) 123-4567</b>.", normal_style)
    ]
    
    # Create a table for the thank you message with background
    thank_you_content = [[p] for p in thank_you_paragraphs]
    thank_you_table = Table(thank_you_content, colWidths=[doc.width - 80])
    thank_you_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#23235b')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e6e6fa')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    story.append(thank_you_table)
    
    # Add a promotional message if appropriate
    if order.payment_status.lower() == 'paid':
        story.append(Spacer(1, 20))
        promo_text = "As a valued customer, enjoy 10% off your next premium vehicle service by using code: <b>CARHUB10</b>"
        promo_para = Paragraph(promo_text, normal_style)
        promo_table = Table([[promo_para]], colWidths=[doc.width - 80])
        promo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#e6e6fa')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#7c4dff')),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        story.append(promo_table)
    
    # Build the PDF with our custom header/footer
    doc.build(story, onFirstPage=add_first_page_elements, onLaterPages=add_first_page_elements)
    buffer.seek(0)
    
    # Log invoice download
    log_user_activity(
        user_id=current_user.id,
        activity_type='invoice_downloaded',
        description=f'Downloaded invoice for order #{order.id}',
        metadata={
            'order_id': order.id,
            'invoice_number': invoice_number,
        }
    )
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=carhub_invoice_{order.id}.pdf'
    
    return response
    
    # Add vehicle info section with enhanced styling
    # Create a styled header with background
    vehicle_header = Paragraph("VEHICLE DETAILS", header_style)
    header_background = Table([[vehicle_header]], colWidths=[doc.width])
    header_background.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f0ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    
    story.append(header_background)
    story.append(Spacer(1, 10))
    
    # Create vehicle info table
    vehicle_info = []
    
    # Header row
    vehicle_info.append(["ITEM", "DESCRIPTION", "PRICE"])
    
    # Vehicle row with enhanced details
    if order.car:
        # Extract more details from the car if available
        car_details = [
            f"Make/Model: {order.car.name}",
            f"VIN: {order.car.vin if hasattr(order.car, 'vin') else 'Not Available'}",
            f"Color: {order.car.color if hasattr(order.car, 'color') else 'Standard'}"
        ]
        
        # Add year and engine details if available
        if hasattr(order.car, 'year'):
            car_details.insert(1, f"Year: {order.car.year}")
        
        if hasattr(order.car, 'engine'):
            car_details.append(f"Engine: {order.car.engine}")
        
        if hasattr(order.car, 'transmission'):
            car_details.append(f"Transmission: {order.car.transmission}")
            
        vehicle_info.append([
            "Premium Vehicle",
            "\n".join(car_details),
            f"${order.car.price:,.2f}" if hasattr(order.car, 'price') else "N/A"
        ])
    else:
        vehicle_info.append(["Vehicle", "Information Not Available", "N/A"])
    
    # Add fees and taxes
    base_price = order.car.price if order.car and hasattr(order.car, 'price') else (order.total_amount / 1.1)
    
    # Add delivery fee if applicable
    if hasattr(order, 'delivery_fee') and order.delivery_fee:
        delivery_fee = order.delivery_fee
    else:
        delivery_fee = base_price * 0.01  # Default 1% delivery fee
        
    vehicle_info.append(["Delivery Fee", "Vehicle delivery and handling", f"${delivery_fee:,.2f}"])
    vehicle_info.append(["Processing Fee", "Documentation and registration", f"${base_price * 0.02:,.2f}"])
    vehicle_info.append(["Tax", "Sales tax (8%)", f"${base_price * 0.08:,.2f}"])
    
    # Add subtotal line
    vehicle_info.append(["", "Subtotal", f"${base_price + delivery_fee + (base_price * 0.02) + (base_price * 0.08):,.2f}"])
    
    # Style the vehicle table
    vehicle_table = Table(vehicle_info, colWidths=[doc.width * 0.2, doc.width * 0.5, doc.width * 0.2])
    vehicle_table_style = TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c4dff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Vehicle row styling
        ('FONT', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Right align all prices
        
        # Alternate row colors
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#f8f9fa')),
        
        # All cell borders
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#7c4dff')),
        
        # Subtotal row styling
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONT', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6e6fa')),
        ('SPAN', (0, -1), (-2, -1)),  # Span the first two columns
        ('ALIGN', (-2, -1), (-2, -1), 'RIGHT'),  # Right align "Subtotal" text
    ])
    
    vehicle_table.setStyle(vehicle_table_style)
    story.append(vehicle_table)
    story.append(Spacer(1, 20))
    
    # Create payment status indicator with color-coded badge
    status_color = colors.HexColor('#4CAF50') if order.payment_status.lower() == 'paid' else colors.HexColor('#FF9800')
    
    # Add payment summary header
    payment_header = Paragraph("PAYMENT SUMMARY", header_style)
    story.append(payment_header)
    story.append(Spacer(1, 10))
    
    # Create payment info with enhanced styling
    payment_data = [
        ["Payment Date:", order.created_at.strftime('%B %d, %Y')],
        ["Transaction ID:", order.transaction_id if hasattr(order, 'transaction_id') and order.transaction_id else "N/A"],
        ["Payment Method:", order.payment_method.replace('_', ' ').title()],
        ["Payment Status:", ""]  # Empty cell for custom status badge
    ]
    
    # Create the payment table
    payment_table = Table(payment_data, colWidths=[doc.width * 0.3, doc.width * 0.6])
    
    # Style the payment table
    payment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#23235b')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    
    story.append(payment_table)
    
    # Create a separate styled status badge
    status_text = order.payment_status.upper()
    status_table = Table([["", status_text]], colWidths=[10, doc.width * 0.3])
    status_table.setStyle(TableStyle([
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('BACKGROUND', (1, 0), (1, 0), status_color),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
        ('TOPPADDING', (1, 0), (1, 0), 6),
        ('BOTTOMPADDING', (1, 0), (1, 0), 6),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    
    story.append(Spacer(1, -30))  # Negative spacer to position the badge at the right location
    story.append(status_table)
    story.append(Spacer(1, 20))
    
    # Create total amount section with gradient background
    total_info = [
        ["TOTAL AMOUNT DUE:", f"${order.total_amount:,.2f}"]
    ]
    
    # Apply different styling based on payment status
    if order.payment_status.lower() == 'paid':
        total_info[0][0] = "TOTAL AMOUNT PAID:"
    
    total_table = Table(total_info, colWidths=[doc.width * 0.5, doc.width * 0.4])
    total_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 16),  # Larger font for total amount
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#23235b')),  # Dark background
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),  # White text
        ('TOPPADDING', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
        ('BOX', (0, 0), (1, 0), 2, colors.HexColor('#7c4dff')),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 30))
    
    # Create a styled box for the thank you message
    thank_you_paragraphs = [
        Paragraph("<b>Thank you for choosing CarHub Premium Auto!</b>", bold_style),
        Spacer(1, 5),
        Paragraph("We value your business and look forward to serving you again. Your satisfaction is our top priority.", normal_style),
        Spacer(1, 10),
        Paragraph("For any questions or concerns regarding this invoice, please contact our customer service team at <b>support@carhub.com</b> or call us at <b>+1 (555) 123-4567</b>.", normal_style)
    ]
    
    # Create a table for the thank you message with background
    thank_you_content = [[p] for p in thank_you_paragraphs]
    thank_you_table = Table(thank_you_content, colWidths=[doc.width - 80])
    thank_you_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#23235b')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e6e6fa')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    story.append(thank_you_table)
    
    # Add a promotional message if appropriate
    if order.payment_status.lower() == 'paid':
        story.append(Spacer(1, 20))
        promo_text = "As a valued customer, enjoy 10% off your next premium vehicle service by using code: <b>CARHUB10</b>"
        promo_para = Paragraph(promo_text, normal_style)
        promo_table = Table([[promo_para]], colWidths=[doc.width - 80])
        promo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#e6e6fa')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#7c4dff')),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        story.append(promo_table)
    
    # Build the PDF with our custom header/footer
    doc.build(story, onFirstPage=add_first_page_elements, onLaterPages=add_first_page_elements)
    buffer.seek(0)
    
    # Log invoice download
    log_user_activity(
        user_id=current_user.id,
        activity_type='invoice_downloaded',
        description=f'Downloaded invoice for order #{order.id}',
        metadata={
            'order_id': order.id,
            'invoice_number': invoice_number,
        }
    )
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=carhub_invoice_{order.id}.pdf'
    
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

# Initialize password reset system
try:
    from password_reset import PasswordResetManager
    from password_reset_routes import init_password_reset_routes
    password_reset_manager = PasswordResetManager(app, mail, db, User)
    init_password_reset_routes(app, password_reset_manager)
    print("✅ Password reset system initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing password reset system: {e}")
    print("💡 Make sure your email settings are configured in .env file")
        
def create_sample_parts():
    """Create sample parts data if none exists"""
    if Part.query.count() == 0:
        sample_parts = [
            {
                'name': 'Premium Brake Pads',
                'description': 'High-performance ceramic brake pads designed for superior stopping power and durability. These premium pads produce minimal noise and dust, and are suitable for a wide range of vehicles including luxury and performance models.',
                'price': '$89.99',
                'image': 'brake-pads.jpg',
                'brand': 'StopTech',
                'category': 'Braking System',
                'condition': 'New',
                'warranty': '2 Years'
            },
            {
                'name': 'Synthetic Engine Oil',
                'description': 'Full synthetic motor oil that provides exceptional performance and protection. Formulated to reduce engine wear, improve fuel efficiency, and maintain performance in extreme temperatures.',
                'price': '$45.99',
                'image': 'engine-oil.jpg',
                'brand': 'Mobil',
                'category': 'Fluids & Chemicals',
                'condition': 'New',
                'warranty': '1 Year'
            },
            {
                'name': 'High-Flow Air Filter',
                'description': 'Performance air filter that increases airflow to your engine while providing excellent filtration. This washable and reusable filter improves horsepower, acceleration, and fuel efficiency.',
                'price': '$59.99',
                'image': 'air-filter.jpg',
                'brand': 'K&N',
                'category': 'Engine Components',
                'condition': 'New',
                'warranty': '10 Years'
            },
            {
                'name': 'Iridium Spark Plugs',
                'description': 'Premium iridium spark plugs designed for maximum performance and longevity. These plugs provide better fuel efficiency, smoother idle, and more reliable starts even in cold weather.',
                'price': '$129.99',
                'image': 'spark-plugs.jpg',
                'brand': 'NGK',
                'category': 'Ignition',
                'condition': 'New',
                'warranty': '5 Years'
            }
        ]
        
        for part_data in sample_parts:
            part = Part(**part_data)
            db.session.add(part)
        
        db.session.commit()
        print("Sample parts added to database")

if __name__ == '__main__':
    with app.app_context():
        # Create tables
        if not os.path.exists('instance'):
            os.makedirs('instance')
        db.create_all()
        
        # Add sample data
        create_sample_parts()
        
        print("Database initialized!")
    
    app.run(debug=True)
