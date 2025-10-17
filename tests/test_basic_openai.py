#!/usr/bin/env python3
"""
Most basic OpenAI test possible
"""

import os

# Set API key directly
OPENAI_API_KEY = ""  # Add your OpenAI API key here

print("Testing OpenAI import...")
try:
    import openai
    print(f"✅ OpenAI imported successfully, version: {openai.__version__}")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

print("\nTesting client creation...")
try:
    # Try the most basic initialization
    client = openai.OpenAI()
    print("✅ Client created successfully")
except Exception as e:
    print(f"❌ Client creation error: {e}")
    
    # Try with kwargs
    try:
        print("\nTrying with kwargs...")
        client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')  # Get API key from environment variables
        )
        print("✅ Client with kwargs created successfully")
    except Exception as e2:
        print(f"❌ Kwargs error: {e2}")
        exit(1)

print("\nTesting API call...")
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=20
    )
    print("✅ API call successful!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ API call error: {e}")
