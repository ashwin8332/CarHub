#!/usr/bin/env python3
"""
Test OpenRouter API connection
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
    print("\n1. Testing OpenRouter client creation...")
    
    if api_key.startswith('sk-or-'):
        print("🔗 Configuring for OpenRouter")
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "CarHub Chatbot"
            }
        )
        model_name = "openai/gpt-3.5-turbo"
    else:
        print("🔗 Configuring for OpenAI")
        client = openai.OpenAI()
        model_name = "gpt-3.5-turbo"
    
    print("✅ Client created successfully")
    
    print("\n2. Testing API call...")
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "Hello! Say hi back to test the connection."}],
        max_tokens=50
    )
    print("✅ API call successful!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
    # Additional error information
    if hasattr(e, 'response'):
        print(f"Response status: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
