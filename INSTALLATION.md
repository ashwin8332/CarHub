# 🚗 CarHub - Installation Guide

This guide will help you set up the CarHub application on your local machine.

## Prerequisites

Before starting, ensure you have the following installed:

- Python 3.9+ (recommended 3.11+)
- pip (Python package manager)
- Git
- A text editor or IDE (VSCode recommended)

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/carhub.git

# Navigate to the project directory
cd carhub
```

## Step 2: Set Up a Virtual Environment

It's recommended to use a virtual environment to avoid package conflicts.

### On Windows:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

### On macOS/Linux:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

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

### Generate a Secret Key:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output to your `.env` file as the SECRET_KEY.

## Step 5: Initialize the Database

The application will automatically create the database on first run, but you can initialize it explicitly:

```bash
python app.py
```

## Step 6: Run the Development Server

```bash
python app.py
```

The application will be available at: http://127.0.0.1:5000

## Step 7: Create an Admin Account (Optional)

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

## Optional Configurations

### 1. Email Configuration for Gmail

If using Gmail for password reset emails:

1. Enable 2-Step Verification in your Google account
2. Generate an App Password:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Under "Signing in to Google", select "App passwords"
   - Select "Mail" and "Other" (Type "CarHub")
   - Use the generated password in your `.env` file

### 2. Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Create OAuth client ID (Web application)
5. Set authorized redirect URIs:
   - http://localhost:5000/auth/google
   - http://127.0.0.1:5000/auth/google
6. Add client ID and secret to your `.env` file

### 3. OpenAI API Setup

1. Create an account at [OpenAI](https://platform.openai.com/)
2. Go to API keys section
3. Generate a new API key
4. Add the key to your `.env` file

## Troubleshooting

### Common Issues

#### Database Errors
- Ensure the `instance` directory exists and is writable
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

#### Email Configuration
- Gmail requires an App Password, not your regular password
- Verify SMTP settings are correct

#### OpenAI API Issues
- Check API key format and validity
- Ensure you have sufficient credits in your OpenAI account

#### Google OAuth Problems
- Verify credentials and authorized domains
- Check for typos in client ID and secret

### Getting Help

If you encounter issues:
1. Check the Flask terminal output for errors
2. Look in the browser console for frontend issues
3. Verify all environment variables are set correctly
4. Consult the CarHub development team

## Development Workflow

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

## Conclusion

You should now have a working installation of the CarHub application on your local machine. If you encounter any issues or have questions, please contact the development team.

Happy coding!✨
