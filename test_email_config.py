import os
from dotenv import load_dotenv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables from config folder
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

def test_smtp_connection():
    print("Testing SMTP Connection...")
    
    # Get credentials from environment
    smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    port = int(os.getenv('MAIL_PORT', 587))
    sender_email = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    print(f"\nConfiguration:")
    print(f"Server: {smtp_server}")
    print(f"Port: {port}")
    print(f"Username: {sender_email}")
    
    # Create message
    message = MIMEMultipart()
    message["Subject"] = "CarHub Email Test"
    message["From"] = sender_email
    message["To"] = sender_email
    
    text = """
    This is a test email to verify SMTP configuration.
    If you receive this, the email configuration is working correctly.
    """
    
    message.attach(MIMEText(text, "plain"))
    
    try:
        print("\nAttempting to connect to SMTP server...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, port) as server:
            print("Connected to SMTP server")
            server.ehlo()
            print("EHLO successful")
            
            print("Starting TLS connection...")
            server.starttls(context=context)
            print("TLS connection successful")
            
            server.ehlo()
            print("Second EHLO successful")
            
            print("Attempting login...")
            server.login(sender_email, password)
            print("Login successful")
            
            print("Sending test email...")
            server.send_message(message)
            print("Test email sent successfully!")
            
        return True
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        if isinstance(e, smtplib.SMTPAuthenticationError):
            print("\nAuthentication failed. Please check:")
            print("1. 2-Step Verification is enabled")
            print("2. App Password is correct (16 characters)")
            print("3. No spaces in the App Password")
        elif isinstance(e, smtplib.SMTPConnectError):
            print("\nConnection error. Please check:")
            print("1. Your internet connection")
            print("2. If port 587 is blocked by firewall")
            print("3. Try using port 465 with SSL instead")
        return False

if __name__ == "__main__":
    test_smtp_connection()