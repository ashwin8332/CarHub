import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import ssl

def test_gmail_connection():
    # Load environment variables from config folder
    load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
    
    # Get mail credentials
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    if not username or not password:
        print("❌ Email credentials are not set in .env file")
        return False
    
    print(f"Testing connection with:")
    print(f"- Username: {username}")
    print(f"- Password: {'*' * len(password)} ({len(password)} characters)")
    
    # Create message
    message = MIMEMultipart()
    message["Subject"] = "CarHub Test - Gmail Authentication"
    message["From"] = username
    message["To"] = username  # Send to self
    
    # Add body
    body = "This is a test email to verify Gmail authentication is working."
    message.attach(MIMEText(body, "plain"))
    
    # Try both methods - TLS and SSL
    methods = [
        {"name": "TLS (port 587)", "port": 587, "use_ssl": False},
        {"name": "SSL (port 465)", "port": 465, "use_ssl": True}
    ]
    
    for method in methods:
        print(f"\n🔄 Trying {method['name']}...")
        try:
            if method["use_ssl"]:
                # SSL connection
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", method["port"], context=context) as server:
                    print("✅ Connected to SMTP server with SSL")
                    server.login(username, password)
                    print("✅ Login successful")
                    server.send_message(message)
                    print("✅ Test email sent successfully!")
                    return True
            else:
                # TLS connection
                with smtplib.SMTP("smtp.gmail.com", method["port"]) as server:
                    print("✅ Connected to SMTP server")
                    server.starttls()
                    print("✅ TLS connection established")
                    server.login(username, password)
                    print("✅ Login successful")
                    server.send_message(message)
                    print("✅ Test email sent successfully!")
                    return True
                    
        except Exception as e:
            print(f"❌ Error with {method['name']}: {str(e)}")
            print("\nPossible issues:")
            print("1. The App Password might be incorrect or expired")
            print("2. 2-Step Verification might not be enabled on your Google account")
            print("3. Less secure app access might be blocked")
    
    print("\n❌ All connection methods failed.")
    print("\nTo fix this issue:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Ensure 2-Step Verification is ON")
    print("3. Generate a new App Password:")
    print("   - Go to App passwords (under 'Signing in to Google')")
    print("   - Select 'Mail' and 'Other (Custom name)'")
    print("   - Enter 'CarHub'")
    print("   - Copy the generated 16-character password")
    print("   - Update MAIL_PASSWORD in your .env file")
    return False

if __name__ == "__main__":
    test_gmail_connection()