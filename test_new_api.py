#!/usr/bin/env python3
"""
Test the new API key
"""
import requests
import json

# Your new API key
API_KEY = "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"

def test_api():
    """Test the new API key"""
    print("🧪 Testing new API key...")
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': 'Hello! Just testing the API. Please respond with "API working!"'}],
        'max_tokens': 10,
        'temperature': 0.7
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content'].strip()
            print(f"✅ API working! Response: {message}")
            return True
        elif response.status_code == 429:
            print("❌ Quota exceeded - need to add credits")
            return False
        elif response.status_code == 401:
            print("❌ Invalid API key")
            return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    test_api()
