"""
Daily Journal Assistant - Web Application
A Flask-based web interface for the AI-powered journaling application
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename

from config import Config, JOURNAL_PROMPTS, MOOD_OPTIONS, COMMON_TAGS
from models import DatabaseManager, JournalEntryModel

# Try to import AI components, fall back to None if not available
try:
    from langchain_utils import JournalAssistant, JournalAnalyzer
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI features not available: {e}")
    JournalAssistant = None
    JournalAnalyzer = None
    AI_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initialize components
db_manager = None
journal_assistant = None
journal_analyzer = None

def initialize_components():
    """Initialize database and AI components"""
    global db_manager, journal_assistant, journal_analyzer
    
    # Create directories
    Config.create_directories()
    
    # Initialize database
    db_manager = DatabaseManager(Config.DATABASE_URL)
    
    # Initialize AI components if available and API key is set
    try:
        if AI_AVAILABLE and Config.OPENAI_API_KEY:
            journal_assistant = JournalAssistant()
            journal_analyzer = JournalAnalyzer()
            print("✅ AI components initialized successfully")
        else:
            print("⚠️  AI features disabled (API key missing or components unavailable)")
    except Exception as e:
        print(f"⚠️  AI components not available: {e}")
        journal_assistant = None
        journal_analyzer = None

# Initialize on startup
initialize_components()

@app.route('/')
def index():
    """Home page"""
    try:
        # Get recent entries for dashboard
        recent_entries = db_manager.get_all_entries(5) if db_manager else []
        
        # Get statistics
        stats = {}
        if db_manager:
            all_entries = db_manager.get_all_entries(1000)
            stats = {
                'total_entries': len(all_entries),
                'this_week': len([e for e in all_entries if e.date >= datetime.now() - timedelta(days=7)]),
                'this_month': len([e for e in all_entries if e.date >= datetime.now() - timedelta(days=30)])
            }
        
        return render_template('index.html', 
                             recent_entries=recent_entries, 
                             stats=stats,
                             ai_available=journal_assistant is not None)
    except Exception as e:
        return render_template('index.html', 
                             recent_entries=[], 
                             stats={'total_entries': 0, 'this_week': 0, 'this_month': 0},
                             ai_available=False)

@app.route('/new')
def new_entry():
    """New journal entry page"""
    prompt_type = request.args.get('type', 'daily')
    prompt_data = JOURNAL_PROMPTS.get(prompt_type, JOURNAL_PROMPTS["daily"])
    
    return render_template('new_entry.html', 
                         prompt_data=prompt_data, 
                         prompt_type=prompt_type,
                         ai_available=journal_assistant is not None)

@app.route('/create_entry', methods=['POST'])
def create_entry():
    """Create a new journal entry"""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        title = data.get('title', '').strip()
        prompt_type = data.get('prompt_type', 'daily')
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'})
        
        # Process with AI if available
        if journal_assistant:
            try:
                processed_entry = journal_assistant.process_journal_entry(content)
                
                # Use AI-generated title if not provided
                if not title:
                    title = processed_entry['title']
                
                entry = JournalEntryModel(
                    title=title,
                    content=content,
                    mood=processed_entry['mood'],
                    tags=processed_entry['tags'],
                    insights=processed_entry['insights']
                )
                
                ai_processed = True
                ai_data = {
                    'mood': processed_entry['mood'],
                    'tags': processed_entry['tags'],
                    'insights': processed_entry['insights']
                }
                
            except Exception as e:
                print(f"AI processing failed (likely API quota exceeded): {e}")
                # Fallback to manual entry without AI
                entry = JournalEntryModel(
                    title=title or "Untitled Entry",
                    content=content
                )
                ai_processed = False
                ai_data = {}
        else:
            # Manual entry without AI
            entry = JournalEntryModel(
                title=title or "Untitled Entry",
                content=content
            )
            ai_processed = False
            ai_data = {}
        
        # Save to database
        db_entry = db_manager.create_entry(entry)
        
        return jsonify({
            'success': True, 
            'entry_id': db_entry.id,
            'ai_processed': ai_processed,
            'ai_data': ai_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/entries')
def entries():
    """List all journal entries"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 10
        offset = (page - 1) * per_page
        
        all_entries = db_manager.get_all_entries(1000) if db_manager else []
        
        # Pagination
        total_entries = len(all_entries)
        entries = all_entries[offset:offset + per_page]
        total_pages = (total_entries + per_page - 1) // per_page
        
        return render_template('entries.html', 
                             entries=entries,
                             page=page,
                             total_pages=total_pages,
                             total_entries=total_entries)
    except Exception as e:
        return render_template('entries.html', 
                             entries=[],
                             page=1,
                             total_pages=0,
                             total_entries=0)

@app.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    """View a specific journal entry"""
    try:
        entry = db_manager.get_entry(entry_id) if db_manager else None
        if not entry:
            flash('Entry not found', 'error')
            return redirect(url_for('entries'))
        
        return render_template('view_entry.html', entry=entry)
    except Exception as e:
        flash(f'Error loading entry: {str(e)}', 'error')
        return redirect(url_for('entries'))

@app.route('/analyze')
def analyze():
    """Journal analysis page"""
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        entries = db_manager.get_entries_by_date_range(start_date, datetime.now()) if db_manager else []
        
        analysis_data = None
        if journal_analyzer and entries:
            # Convert to dict format for analysis
            entries_data = []
            for entry in entries:
                entries_data.append({
                    'id': entry.id,
                    'date': entry.date.strftime('%Y-%m-%d'),
                    'title': entry.title,
                    'content': entry.content,
                    'mood': entry.mood,
                    'tags': entry.tags
                })
            
            analysis_data = journal_analyzer.analyze_emotional_patterns(entries_data)
        
        return render_template('analyze.html', 
                             entries=entries,
                             analysis_data=analysis_data,
                             days=days,
                             ai_available=journal_analyzer is not None)
    except Exception as e:
        return render_template('analyze.html', 
                             entries=[],
                             analysis_data=None,
                             days=30,
                             ai_available=False)

@app.route('/chat')
def chat():
    """Interactive chat page"""
    entry_id = request.args.get('entry_id')
    context_entry = None
    
    if entry_id and db_manager:
        try:
            context_entry = db_manager.get_entry(int(entry_id))
        except:
            pass
    
    return render_template('chat.html', 
                         context_entry=context_entry,
                         ai_available=journal_assistant is not None)

@app.route('/chat_message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message or not journal_assistant:
            return jsonify({'success': False, 'error': 'Chat not available'})
        
        response = journal_assistant.chat_about_entry(message)
        
        return jsonify({'success': True, 'response': response})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stats')
def stats():
    """Statistics page"""
    try:
        all_entries = db_manager.get_all_entries(1000) if db_manager else []
        
        if not all_entries:
            return render_template('stats.html', 
                                 total_entries=0,
                                 mood_counts={},
                                 tag_counts={},
                                 date_range=None,
                                 current_streak=0)
        
        # Calculate statistics
        total_entries = len(all_entries)
        oldest_entry = min(all_entries, key=lambda x: x.date)
        newest_entry = max(all_entries, key=lambda x: x.date)
        
        # Mood statistics
        mood_counts = {}
        tag_counts = {}
        
        for entry in all_entries:
            if entry.mood:
                mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1
            
            if entry.tags:
                for tag in entry.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Writing streak
        dates = sorted([entry.date.date() for entry in all_entries])
        current_streak = 0
        if dates:
            today = datetime.now().date()
            check_date = today
            
            while check_date in dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        
        return render_template('stats.html',
                             total_entries=total_entries,
                             mood_counts=mood_counts,
                             tag_counts=tag_counts,
                             date_range=(oldest_entry.date, newest_entry.date),
                             current_streak=current_streak)
        
    except Exception as e:
        return render_template('stats.html',
                             total_entries=0,
                             mood_counts={},
                             tag_counts={},
                             date_range=None,
                             current_streak=0)

@app.route('/export')
def export():
    """Export journal entries"""
    try:
        format_type = request.args.get('format', 'json')
        entries = db_manager.get_all_entries(1000) if db_manager else []
        
        if format_type == 'json':
            export_data = []
            for entry in entries:
                export_data.append({
                    "id": entry.id,
                    "date": entry.date.isoformat(),
                    "title": entry.title,
                    "content": entry.content,
                    "mood": entry.mood,
                    "tags": entry.tags,
                    "insights": entry.insights,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat()
                })
            
            response = app.response_class(
                json.dumps(export_data, indent=2, ensure_ascii=False),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename=journal_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
            )
            return response
        
        elif format_type == 'txt':
            content = "Daily Journal Assistant - Export\n"
            content += "=" * 50 + "\n\n"
            
            for entry in entries:
                content += f"Entry #{entry.id}\n"
                content += f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}\n"
                content += f"Title: {entry.title}\n"
                content += f"Mood: {entry.mood or 'Not specified'}\n"
                content += f"Tags: {', '.join(entry.tags) if entry.tags else 'None'}\n"
                content += "-" * 30 + "\n"
                content += entry.content + "\n"
                if entry.insights:
                    content += "\nAI Insights:\n"
                    content += entry.insights + "\n"
                content += "\n" + "=" * 50 + "\n\n"
            
            response = app.response_class(
                content,
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename=journal_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'}
            )
            return response
        
        return jsonify({'error': 'Invalid format'})
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
