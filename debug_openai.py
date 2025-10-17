#!/usr/bin/env python3
"""
Debug OpenAI initialization issue
"""

import os
import traceback
import sys

# Set API key
OPENAI_API_KEY = ""  # Add your OpenAI API key here

print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nImporting openai...")
import openai

print(f"OpenAI version: {openai.__version__}")
print(f"OpenAI path: {openai.__file__}")

print("\nTrying to create client with full traceback...")
try:
    # Get the exact constructor to see what's being called
    print(f"OpenAI class: {openai.OpenAI}")
    print(f"Constructor: {openai.OpenAI.__init__}")
    
    # Try to see what arguments are being passed somehow
    original_init = openai.OpenAI.__init__
    
    def debug_init(self, *args, **kwargs):
        print(f"DEBUG: __init__ called with args={args}, kwargs={kwargs}")
        return original_init(self, *args, **kwargs)
    
    openai.OpenAI.__init__ = debug_init
    
    client = openai.OpenAI()
    print("✅ Client created successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Full traceback:")
    traceback.print_exc()
