"""
Working AI-Powered Daily Journal Assistant
A Flask-based web interface with AI features that actually work
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import os
import requests
from werkzeug.utils import secure_filename

from config import Config, JOURNAL_PROMPTS, MOOD_OPTIONS, COMMON_TAGS
from models import DatabaseManager, JournalEntryModel

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initialize components
db_manager = None
ai_available = False

def initialize_components():
    """Initialize database and AI components"""
    global db_manager, ai_available
    
    # Create directories
    Config.create_directories()
    
    # Initialize database
    db_manager = DatabaseManager(Config.DATABASE_URL)
    print("✅ Database initialized successfully")
    
    # Check AI availability (no blocking test)
    if Config.OPENAI_API_KEY and len(Config.OPENAI_API_KEY) > 20:
        ai_available = True
        print("✅ AI features enabled (API key found)")
    else:
        print("⚠️  AI features disabled: No valid API key found")

# Initialize on startup
initialize_components()

def call_openai_api(messages, max_tokens=150):
    """Call OpenAI API directly with better error handling"""
    if not ai_available or not Config.OPENAI_API_KEY:
        return "AI features are currently unavailable."
    
    try:
        headers = {
            'Authorization': f'Bearer {Config.OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        elif response.status_code == 429:
            return "AI quota exceeded. Please check your OpenAI account billing."
        elif response.status_code == 401:
            return "Invalid API key. Please check your OpenAI API key."
        else:
            return f"AI error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "AI request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "AI connection failed. Please check your internet connection."
    except Exception as e:
        return f"AI error: {str(e)}"

def analyze_entry_with_ai(content):
    """Analyze journal entry with AI"""
    if not ai_available:
        return {
            'mood': 'neutral',
            'tags': ['general'],
            'insights': 'AI analysis unavailable',
            'title': 'Untitled Entry'
        }
    
    # Simple mood analysis prompt
    mood_prompt = f"""Analyze this journal entry and respond with a JSON object:
    {{
        "mood": "happy/sad/neutral/excited/anxious/calm",
        "tags": ["tag1", "tag2", "tag3"],
        "insights": "Brief insight about the entry",
        "title": "Short descriptive title"
    }}
    
    Entry: {content[:300]}"""
    
    response = call_openai_api([{'role': 'user', 'content': mood_prompt}])
    
    try:
        # Try to parse JSON response
        if response.startswith('{') and response.endswith('}'):
            return json.loads(response)
        else:
            # Fallback if not JSON
            return {
                'mood': 'neutral',
                'tags': ['general'],
                'insights': response[:100] if response else 'AI analysis unavailable',
                'title': 'AI Generated Title'
            }
    except:
        return {
            'mood': 'neutral',
            'tags': ['general'],
            'insights': response[:100] if response else 'AI analysis unavailable',
            'title': 'AI Generated Title'
        }

def chat_with_ai(message, context=""):
    """Chat with AI about journal entries"""
    if not ai_available:
        return "I'm sorry, but AI features are currently unavailable. Please check your API configuration."
    
    system_prompt = """You are a helpful journaling assistant. Help the user explore their thoughts and feelings. 
    Be supportive, insightful, and encouraging. Keep responses concise and helpful."""
    
    if context:
        system_prompt += f"\n\nContext from their journal: {context[:200]}"
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': message}
    ]
    
    return call_openai_api(messages, max_tokens=200)

@app.route('/')
def index():
    """Home page with quick stats and actions"""
    try:
        # Get basic stats
        total_entries = db_manager.get_total_entries()
        recent_entries = db_manager.get_recent_entries(limit=5)
        
        # Calculate weekly and monthly stats
        week_ago = datetime.now() - timedelta(days=7)
        month_ago = datetime.now() - timedelta(days=30)
        
        weekly_entries = db_manager.get_entries_by_date_range(week_ago, datetime.now())
        monthly_entries = db_manager.get_entries_by_date_range(month_ago, datetime.now())
        
        stats = {
            'total_entries': total_entries,
            'weekly_entries': len(weekly_entries),
            'monthly_entries': len(monthly_entries),
            'recent_entries': recent_entries
        }
        
        return render_template('index.html', stats=stats, ai_available=ai_available)
    except Exception as e:
        print(f"Error in index: {e}")
        return render_template('index.html', stats={'total_entries': 0, 'weekly_entries': 0, 'monthly_entries': 0, 'recent_entries': []}, ai_available=ai_available)

@app.route('/new')
def new_entry():
    """New entry form"""
    # Get prompt type from URL parameter
    prompt_type = request.args.get('type', 'daily')
    
    # Get prompt data from config
    from config import JOURNAL_PROMPTS
    prompt_data = JOURNAL_PROMPTS.get(prompt_type, JOURNAL_PROMPTS['daily'])
    
    return render_template('new_entry.html', ai_available=ai_available, prompt_data=prompt_data, prompt_type=prompt_type)

@app.route('/create_entry', methods=['POST'])
def create_entry():
    """Create a new journal entry"""
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('Content is required!', 'error')
            return redirect(url_for('new_entry'))
        
        # Process with AI if available
        if ai_available:
            try:
                ai_analysis = analyze_entry_with_ai(content)
                
                # Use AI-generated title if not provided
                if not title:
                    title = ai_analysis.get('title', 'Untitled Entry')
                
                entry = JournalEntryModel(
                    title=title,
                    content=content,
                    mood=ai_analysis.get('mood', 'neutral'),
                    tags=','.join(ai_analysis.get('tags', ['general'])),
                    insights=ai_analysis.get('insights', '')
                )
                
                flash('Entry created successfully with AI analysis!', 'success')
                
            except Exception as e:
                print(f"AI processing failed: {e}")
                # Fallback to manual entry
                entry = JournalEntryModel(
                    title=title or "Untitled Entry",
                    content=content
                )
                flash('Entry created successfully! (AI analysis failed)', 'warning')
        else:
            # Manual entry without AI
            entry = JournalEntryModel(
                title=title or "Untitled Entry",
                content=content
            )
            flash('Entry created successfully!', 'success')
        
        # Save to database
        entry_id = db_manager.create_entry(entry)
        return redirect(url_for('view_entry', entry_id=entry_id))
        
    except Exception as e:
        print(f"Error creating entry: {e}")
        flash('Error creating entry. Please try again.', 'error')
        return redirect(url_for('new_entry'))

@app.route('/entries')
def entries():
    """List all entries"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 10
        
        entries = db_manager.get_entries_paginated(page=page, per_page=per_page)
        total_entries = db_manager.get_total_entries()
        
        return render_template('entries.html', entries=entries, page=page, 
                             total_pages=(total_entries + per_page - 1) // per_page)
    except Exception as e:
        print(f"Error in entries: {e}")
        return render_template('entries.html', entries=[], page=1, total_pages=0)

@app.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    """View a specific entry"""
    try:
        entry = db_manager.get_entry_by_id(entry_id)
        if not entry:
            flash('Entry not found!', 'error')
            return redirect(url_for('entries'))
        
        return render_template('view_entry.html', entry=entry, ai_available=ai_available)
    except Exception as e:
        print(f"Error viewing entry: {e}")
        flash('Error loading entry.', 'error')
        return redirect(url_for('entries'))

@app.route('/chat')
def chat():
    """AI Chat page"""
    entry_id = request.args.get('entry_id')
    context_entry = None
    
    if entry_id:
        try:
            context_entry = db_manager.get_entry_by_id(int(entry_id))
        except:
            pass
    
    return render_template('chat.html', context_entry=context_entry, ai_available=ai_available)

@app.route('/chat_message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Get context if available
        context = ""
        entry_id = data.get('entry_id')
        if entry_id:
            try:
                entry = db_manager.get_entry_by_id(int(entry_id))
                if entry:
                    context = entry.content
            except:
                pass
        
        # Get AI response
        response = chat_with_ai(message, context)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'})

@app.route('/analyze')
def analyze():
    """Analysis page"""
    try:
        days = int(request.args.get('days', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        entries = db_manager.get_entries_by_date_range(start_date, end_date)
        
        # AI analysis if available
        ai_insights = "AI analysis is currently unavailable."
        if ai_available and entries:
            try:
                # Combine recent entries for analysis
                combined_content = " ".join([entry.content[:100] for entry in entries[:5]])
                analysis_prompt = f"""Analyze these journal entries and provide insights about patterns, themes, and emotional trends. Keep it concise and helpful.
                
                Entries: {combined_content}"""
                
                ai_insights = call_openai_api([{'role': 'user', 'content': analysis_prompt}], max_tokens=300)
            except Exception as e:
                ai_insights = f"AI analysis failed: {e}"
        
        analysis = {
            'total_entries': len(entries),
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'entries': entries,
            'ai_insights': ai_insights
        }
        
        return render_template('analyze.html', analysis=analysis, ai_available=ai_available)
    except Exception as e:
        print(f"Error in analyze: {e}")
        return render_template('analyze.html', analysis={'total_entries': 0, 'date_range': '', 'entries': [], 'ai_insights': 'Error loading analysis.'}, ai_available=ai_available)

@app.route('/stats')
def stats():
    """Statistics page"""
    try:
        total_entries = db_manager.get_total_entries()
        recent_entries = db_manager.get_recent_entries(limit=10)
        
        # Calculate basic stats
        if recent_entries:
            first_entry = min(recent_entries, key=lambda x: x.created_at)
            days_active = (datetime.now() - first_entry.created_at).days + 1
            avg_entries = total_entries / max(days_active, 1)
        else:
            days_active = 0
            avg_entries = 0
        
        stats = {
            'total_entries': total_entries,
            'days_active': days_active,
            'avg_entries_per_day': round(avg_entries, 2),
            'recent_entries': recent_entries
        }
        
        return render_template('stats.html', stats=stats)
    except Exception as e:
        print(f"Error in stats: {e}")
        return render_template('stats.html', stats={'total_entries': 0, 'days_active': 0, 'avg_entries_per_day': 0, 'recent_entries': []})

if __name__ == '__main__':
    print("🚀 Starting Working AI-Powered Daily Journal Assistant...")
    print("🤖 AI features enabled with direct OpenAI API integration")
    print("🌐 Web interface will be available at: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
