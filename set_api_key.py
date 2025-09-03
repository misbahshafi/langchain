#!/usr/bin/env python3
"""
Set OpenAI API Key directly in the environment
"""
import os

# Set the new API key
api_key = "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"

# Set environment variable
os.environ['OPENAI_API_KEY'] = api_key

# Also create .env file
with open('.env', 'w') as f:
    f.write(f'OPENAI_API_KEY={api_key}\n')
    f.write('DATABASE_URL=sqlite:///data/journal.db\n')
    f.write('DEBUG=True\n')
    f.write('SECRET_KEY=your-secret-key-change-this-in-production\n')

print("✅ New API key set successfully!")
print(f"✅ API key length: {len(api_key)} characters")
print("✅ .env file updated")