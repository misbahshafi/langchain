"""
Simple Daily Journal Assistant - Web Application
A Flask-based web interface without LangChain dependencies
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename

from config import Config, JOURNAL_PROMPTS, MOOD_OPTIONS, COMMON_TAGS
from models import DatabaseManager, JournalEntryModel

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initialize components
db_manager = None

def initialize_components():
    """Initialize database components"""
    global db_manager
    
    # Create directories
    Config.create_directories()
    
    # Initialize database
    db_manager = DatabaseManager(Config.DATABASE_URL)
    print("✅ Database initialized successfully")
    print("⚠️  AI features disabled (using simple mode)")

# Initialize on startup
initialize_components()

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
        
        return render_template('index.html', stats=stats, ai_available=False)
    except Exception as e:
        print(f"Error in index: {e}")
        return render_template('index.html', stats={'total_entries': 0, 'weekly_entries': 0, 'monthly_entries': 0, 'recent_entries': []}, ai_available=False)

@app.route('/new')
def new_entry():
    """New entry form"""
    return render_template('new_entry.html', ai_available=False)

@app.route('/create_entry', methods=['POST'])
def create_entry():
    """Create a new journal entry"""
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('Content is required!', 'error')
            return redirect(url_for('new_entry'))
        
        # Create entry without AI processing
        entry = JournalEntryModel(
            title=title or "Untitled Entry",
            content=content
        )
        
        # Save to database
        entry_id = db_manager.create_entry(entry)
        
        flash('Entry created successfully!', 'success')
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
        
        return render_template('view_entry.html', entry=entry, ai_available=False)
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
    
    return render_template('chat.html', context_entry=context_entry, ai_available=False)

@app.route('/chat_message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Simple response without AI
        response = "I'm sorry, but AI features are currently unavailable. Please check your API configuration or use the offline mode."
        
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
        
        # Basic analysis without AI
        analysis = {
            'total_entries': len(entries),
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'entries': entries,
            'ai_insights': "AI analysis is currently unavailable. Please check your API configuration."
        }
        
        return render_template('analyze.html', analysis=analysis, ai_available=False)
    except Exception as e:
        print(f"Error in analyze: {e}")
        return render_template('analyze.html', analysis={'total_entries': 0, 'date_range': '', 'entries': [], 'ai_insights': 'Error loading analysis.'}, ai_available=False)

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
    print("🚀 Starting Simple Daily Journal Assistant...")
    print("📝 All features work except AI analysis")
    print("🌐 Web interface will be available at: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
