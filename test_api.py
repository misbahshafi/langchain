#!/usr/bin/env python3
"""
Test OpenAI API key functionality
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ No API key found in environment")
    exit(1)

print(f"✅ API key found: {api_key[:20]}...")

# Test API connection
try:
    client = OpenAI(api_key=api_key)
    
    # Make a simple test request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Hello, API is working!'"}],
        max_tokens=10
    )
    
    print("✅ API connection successful!")
    print(f"✅ Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ API connection failed: {e}")
    
    # Check if it's a quota issue
    if "quota" in str(e).lower() or "429" in str(e):
        print("\n🔍 This appears to be a quota/billing issue.")
        print("💡 Solutions:")
        print("   1. Check your OpenAI account billing at: https://platform.openai.com/account/billing")
        print("   2. Add credits to your account")
        print("   3. Check your usage limits")
        print("   4. Use the offline mode: python web_app_offline.py")
    elif "invalid" in str(e).lower() or "401" in str(e):
        print("\n🔍 This appears to be an invalid API key issue.")
        print("💡 Solutions:")
        print("   1. Generate a new API key at: https://platform.openai.com/api-keys")
        print("   2. Make sure the key is copied correctly")
    else:
        print(f"\n🔍 Unknown error: {e}")
