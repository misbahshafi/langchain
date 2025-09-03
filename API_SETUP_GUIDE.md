# OpenAI API Setup Guide

## Why AI Features Aren't Working

The error you're seeing:
```
Error code: 429 - You exceeded your current quota, please check your plan and billing details.
```

This means your OpenAI API key has either:
1. **Exceeded its usage limit** (most common)
2. **No credits remaining**
3. **Invalid API key**

## Solutions

### Option 1: Fix Your OpenAI API Key (Recommended)

1. **Go to OpenAI Platform**: https://platform.openai.com/
2. **Sign in** to your account
3. **Check your usage**: Go to "Usage" tab to see your current usage
4. **Add credits**: Go to "Billing" tab and add credits to your account
5. **Get a new API key**: Go to "API Keys" tab and create a new key
6. **Update your .env file**:
   ```
   OPENAI_API_KEY=your_new_api_key_here
   ```

### Option 2: Use Offline Mode (No AI Features)

If you don't want to use AI features, you can run the offline version:

**Windows:**
```bash
run_offline.bat
```

**Or manually:**
```bash
python web_app_offline.py
```

This version works perfectly without any AI features - you can still:
- ✅ Create journal entries
- ✅ View all entries
- ✅ Export data
- ✅ View statistics
- ✅ Beautiful web interface

### Option 3: Use Free AI Alternatives

You can modify the code to use free AI services like:
- **Hugging Face Transformers** (completely free)
- **Ollama** (local AI models)
- **Google Colab** (free GPU access)

## Current Status

Your web application is working perfectly! The AI features are just disabled due to the API quota issue. You can:

1. **Continue using the offline version** - it's fully functional
2. **Fix your OpenAI API key** to enable AI features
3. **Use the app as-is** - it's still a great journaling tool

## Features Available in Offline Mode

- 📝 **Create Journal Entries** - Full writing experience
- 📚 **View All Entries** - Browse your journal history
- 📊 **Statistics** - See your writing patterns
- 📈 **Analysis** - Basic mood and pattern analysis
- 💾 **Export Data** - Download your entries as JSON or TXT
- 🎨 **Beautiful Interface** - Modern, responsive design

The app is working great - just without the AI enhancements!
