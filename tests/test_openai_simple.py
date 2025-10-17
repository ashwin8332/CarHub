#!/usr/bin/env python3
"""
Simple OpenAI test
"""

import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:20] + '...' if api_key else 'None'}")

# Set environment variable
if api_key:
    os.environ['OPENAI_API_KEY'] = api_key

try:
    # Try different initialization methods
    print("\n1. Testing basic initialization...")
    client = openai.OpenAI()
    print("✅ Basic initialization successful")
    
    print("\n2. Testing API call...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("✅ API call successful")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
    # Try with explicit api_key parameter
    try:
        print("\n3. Testing with explicit API key...")
        client = openai.OpenAI(api_key=api_key)
        print("✅ Explicit API key initialization successful")
    except Exception as e2:
        print(f"❌ Explicit API key error: {e2}")
