from flask import render_template
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta

class PasswordResetManager:
    def __init__(self, app, mail, db, User):
        self.app = app
        self.mail = mail
        self.db = db
        self.User = User
        self.otp_store = {}  # Store OTPs with expiration time
        
    def generate_otp(self, length=6):
        """Generate a numeric OTP of specified length"""
        return ''.join(random.choices(string.digits, k=length))
    
    def store_otp(self, email, otp):
        """Store OTP with expiration time (10 minutes)"""
        expiration = datetime.now() + timedelta(minutes=10)
        self.otp_store[email] = {
            'otp': otp,
            'expiration': expiration
        }
    
    def verify_otp(self, email, otp):
        """Verify if OTP is valid and not expired"""
        if email not in self.otp_store:
            return False
        
        stored_data = self.otp_store[email]
        if datetime.now() > stored_data['expiration']:
            del self.otp_store[email]  # Clear expired OTP
            return False
        
        if stored_data['otp'] == otp:
            del self.otp_store[email]  # Clear used OTP
            return True
            
        return False
    
    def verify_mail_config(self):
        """Verify mail configuration"""
        required_configs = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD']
        for config in required_configs:
            if not self.app.config.get(config):
                print(f"Missing required configuration: {config}")
                return False
        return True

    def send_password_reset_email(self, email):
        """Send password reset email with OTP"""
        # Verify configuration first
        if not self.verify_mail_config():
            print("Invalid mail configuration")
            return False

        user = self.User.query.filter_by(email=email).first()
        if not user:
            print(f"User not found: {email}")
            return False
            
        # Generate and store OTP
        otp = self.generate_otp()
        self.store_otp(email, otp)
        
        # Create email message
        try:
            from datetime import datetime  # Add this import
            
            msg = Message('Password Reset Request - CarHub',
                         sender=self.app.config['MAIL_DEFAULT_SENDER'],
                         recipients=[email])
                         
            msg.html = render_template(
                'email/reset_password.html',
                user=user,
                otp=otp,
                now=datetime.now()  # Pass the current datetime
            )
        except Exception as e:
            print(f"Error creating message: {str(e)}")
            return False
        
        try:
            # Print configuration for debugging
            print("\nMail Configuration:")
            print(f"Server: {self.app.config['MAIL_SERVER']}")
            print(f"Port: {self.app.config['MAIL_PORT']}")
            print(f"Use TLS: {self.app.config.get('MAIL_USE_TLS', False)}")
            print(f"Use SSL: {self.app.config.get('MAIL_USE_SSL', False)}")
            print(f"Username: {self.app.config['MAIL_USERNAME']}")
            print(f"Sender: {self.app.config['MAIL_DEFAULT_SENDER']}")
            
            # Verify credentials format
            password = self.app.config['MAIL_PASSWORD']
            if ' ' in password:
                print("Warning: Mail password contains spaces - removing spaces")
                # Update the password without spaces
                self.app.config['MAIL_PASSWORD'] = password.replace(" ", "")
                
            if not password:
                print("Error: Mail password is empty")
                return False
                
            if len(password) != 16:
                print(f"Warning: Mail password length is {len(password)} (expected 16 for Gmail App Password)")
            
            # Try direct SMTP method if flask-mail fails
            print("\nAttempting to send email...")
            try:
                self.mail.send(msg)
                print("Email sent successfully via Flask-Mail!")
                return True
            except Exception as mail_error:
                print(f"Flask-Mail error: {str(mail_error)}")
                print("Trying alternate direct SMTP method...")
                
                # Fall back to direct SMTP
                import smtplib
                import ssl
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                message = MIMEMultipart('alternative')
                message['Subject'] = msg.subject
                message['From'] = msg.sender
                message['To'] = ", ".join(msg.recipients)
                message.attach(MIMEText(msg.html, 'html'))
                
                # Try SSL connection first (more reliable with Gmail)
                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(self.app.config['MAIL_SERVER'], 465, context=context) as server:
                        server.login(self.app.config['MAIL_USERNAME'], self.app.config['MAIL_PASSWORD'])
                        server.send_message(message)
                        print("Email sent successfully via direct SSL connection!")
                        return True
                except Exception as ssl_error:
                    print(f"SSL connection failed: {str(ssl_error)}")
                    
                    # Fall back to TLS as last resort
                    try:
                        with smtplib.SMTP(self.app.config['MAIL_SERVER'], 587) as server:
                            server.ehlo()
                            server.starttls(context=context)
                            server.ehlo()
                            server.login(self.app.config['MAIL_USERNAME'], self.app.config['MAIL_PASSWORD'])
                            server.send_message(message)
                            print("Email sent successfully via direct TLS connection!")
                            return True
                    except Exception as tls_error:
                        print(f"TLS connection failed: {str(tls_error)}")
                        raise tls_error
                
            print("Email sent successfully!")
            return True
        except Exception as e:
            print(f"\nDetailed error sending email: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())
            
            # Additional Gmail-specific error hints
            if "Username and Password not accepted" in str(e):
                print("\nPossible solutions:")
                print("1. Verify 2-Step Verification is enabled in your Google Account")
                print("2. Generate a new App Password in Google Account settings")
                print("3. Check for any Google security alerts about blocked sign-in attempts")
            return False
            
    def reset_password(self, email, otp, new_password):
        """Reset user password after OTP verification"""
        if not self.verify_otp(email, otp):
            return False, "Invalid or expired OTP"
            
        user = self.User.query.filter_by(email=email).first()
        if not user:
            return False, "User not found"
            
        try:
            user.set_password(new_password)
            self.db.session.commit()
            return True, "Password reset successful"
        except Exception as e:
            self.db.session.rollback()
            return False, f"Error resetting password: {str(e)}"