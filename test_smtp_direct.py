import os
from dotenv import load_dotenv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_direct():
    # Load environment variables from config folder
    load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
    
    # Email settings
    smtp_server = "smtp.gmail.com"
    port = 465  # For SSL
    sender_email = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD').replace(" ", "")  # Remove any spaces
    receiver_email = sender_email  # Send to self for testing
    
    # Create message
    message = MIMEMultipart()
    message["Subject"] = "Test Email - Direct SMTP"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    body = "This is a test email sent using direct SMTP over SSL."
    message.attach(MIMEText(body, "plain"))
    
    print(f"\nSettings being used:")
    print(f"SMTP Server: {smtp_server}")
    print(f"Port: {port}")
    print(f"Username: {sender_email}")
    print(f"Password length: {len(password)}")
    
    try:
        print("\nCreating SSL context...")
        context = ssl.create_default_context()
        
        print("Connecting to SMTP server...")
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            print("Connected successfully")
            
            print("Attempting login...")
            server.login(sender_email, password)
            print("Login successful!")
            
            print("Sending email...")
            server.send_message(message)
            print("Email sent successfully!")
            
        return True
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        if "Username and Password not accepted" in str(e):
            print("\nAuthentication failed. Please check:")
            print("1. Make sure 2-Step Verification is enabled in your Google Account")
            print("2. Generate a new App Password specifically for this application")
            print("3. Check that the App Password is entered correctly (16 characters, no spaces)")
        return False

if __name__ == "__main__":
    test_smtp_direct()