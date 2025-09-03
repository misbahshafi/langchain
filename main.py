"""
Daily Journal Assistant - Main Application
A LangChain-powered journaling application with AI insights
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from datetime import datetime, timedelta
import json
import os
from typing import Optional, List

from config import Config, JOURNAL_PROMPTS, MOOD_OPTIONS, COMMON_TAGS
from models import DatabaseManager, JournalEntryModel
from langchain_utils import JournalAssistant, JournalAnalyzer

# Initialize Rich console
console = Console()

# Initialize Typer app
app = typer.Typer(
    name="journal",
    help="Daily Journal Assistant - AI-powered journaling with LangChain",
    add_completion=False
)

# Global variables
db_manager = None
journal_assistant = None
journal_analyzer = None

def initialize_app():
    """Initialize the application"""
    global db_manager, journal_assistant, journal_analyzer
    
    # Create directories
    Config.create_directories()
    
    # Initialize database
    db_manager = DatabaseManager(Config.DATABASE_URL)
    
    # Validate configuration
    if not Config.validate_config():
        console.print("[red]Warning: OpenAI API key not found. Some features may not work.[/red]")
        console.print("Please set your OPENAI_API_KEY in a .env file or environment variable.")
        if not Confirm.ask("Continue without API key?"):
            raise typer.Exit(1)
    
    # Initialize AI components
    try:
        journal_assistant = JournalAssistant()
        journal_analyzer = JournalAnalyzer()
        console.print("[green]✓ AI components initialized successfully[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: AI components not available: {e}[/yellow]")
        journal_assistant = None
        journal_analyzer = None

@app.command()
def new(
    prompt_type: str = typer.Option("daily", help="Type of journal prompt"),
    interactive: bool = typer.Option(True, help="Interactive mode"),
    title: Optional[str] = typer.Option(None, help="Custom title for the entry")
):
    """Create a new journal entry"""
    if not db_manager:
        initialize_app()
    
    console.print(Panel.fit(
        "[bold blue]📝 New Journal Entry[/bold blue]",
        border_style="blue"
    ))
    
    # Get prompt
    prompt_data = JOURNAL_PROMPTS.get(prompt_type, JOURNAL_PROMPTS["daily"])
    console.print(f"\n[bold]Prompt:[/bold] {prompt_data['prompt']}")
    
    if prompt_data['suggestions']:
        console.print("\n[bold]Suggestions:[/bold]")
        for i, suggestion in enumerate(prompt_data['suggestions'], 1):
            console.print(f"  {i}. {suggestion}")
    
    # Get content
    if interactive:
        console.print("\n[bold]Start writing your journal entry:[/bold]")
        console.print("(Type 'END' on a new line when finished)")
        
        content_lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            content_lines.append(line)
        
        content = "\n".join(content_lines)
    else:
        content = Prompt.ask("Enter your journal entry")
    
    if not content.strip():
        console.print("[red]No content provided. Entry not saved.[/red]")
        return
    
    # Process with AI if available
    if journal_assistant:
        console.print("\n[blue]🤖 Processing with AI...[/blue]")
        try:
            processed_entry = journal_assistant.process_journal_entry(content)
            
            # Use AI-generated title if not provided
            if not title:
                title = processed_entry['title']
            
            # Create entry model
            entry = JournalEntryModel(
                title=title,
                content=content,
                mood=processed_entry['mood'],
                tags=processed_entry['tags'],
                insights=processed_entry['insights']
            )
            
            console.print(f"[green]✓ Mood detected: {processed_entry['mood']}[/green]")
            console.print(f"[green]✓ Tags: {', '.join(processed_entry['tags'])}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]AI processing failed: {e}[/yellow]")
            entry = JournalEntryModel(
                title=title or "Untitled Entry",
                content=content
            )
    else:
        # Manual entry without AI
        if not title:
            title = Prompt.ask("Enter a title for your entry")
        
        mood = Prompt.ask("Select mood", choices=MOOD_OPTIONS, default="😌 Content")
        mood = mood.split(" ", 1)[1] if " " in mood else mood
        
        tags_input = Prompt.ask("Enter tags (comma-separated)", default="")
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
        
        entry = JournalEntryModel(
            title=title,
            content=content,
            mood=mood,
            tags=tags
        )
    
    # Save to database
    try:
        db_entry = db_manager.create_entry(entry)
        console.print(f"\n[green]✓ Journal entry saved with ID: {db_entry.id}[/green]")
        
        # Show insights if available
        if journal_assistant and hasattr(entry, 'insights') and entry.insights:
            console.print("\n[bold blue]💡 AI Insights:[/bold blue]")
            console.print(Panel(entry.insights, border_style="blue"))
            
    except Exception as e:
        console.print(f"[red]Error saving entry: {e}[/red]")

@app.command()
def list(
    limit: int = typer.Option(10, help="Number of entries to show"),
    days: Optional[int] = typer.Option(None, help="Show entries from last N days")
):
    """List recent journal entries"""
    if not db_manager:
        initialize_app()
    
    console.print(Panel.fit(
        "[bold blue]📚 Journal Entries[/bold blue]",
        border_style="blue"
    ))
    
    try:
        if days:
            start_date = datetime.now() - timedelta(days=days)
            entries = db_manager.get_entries_by_date_range(start_date, datetime.now())
        else:
            entries = db_manager.get_all_entries(limit)
        
        if not entries:
            console.print("[yellow]No entries found.[/yellow]")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Date", width=12)
        table.add_column("Title", width=30)
        table.add_column("Mood", width=15)
        table.add_column("Tags", width=20)
        
        for entry in entries:
            tags_str = ", ".join(entry.tags) if entry.tags else "None"
            table.add_row(
                str(entry.id),
                entry.date.strftime("%Y-%m-%d"),
                entry.title[:27] + "..." if len(entry.title) > 30 else entry.title,
                entry.mood or "Unknown",
                tags_str[:17] + "..." if len(tags_str) > 20 else tags_str
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error retrieving entries: {e}[/red]")

@app.command()
def read(
    entry_id: int = typer.Argument(..., help="ID of the entry to read")
):
    """Read a specific journal entry"""
    if not db_manager:
        initialize_app()
    
    try:
        entry = db_manager.get_entry(entry_id)
        if not entry:
            console.print(f"[red]Entry with ID {entry_id} not found.[/red]")
            return
        
        # Display entry
        console.print(Panel.fit(
            f"[bold blue]📖 {entry.title}[/bold blue]",
            border_style="blue"
        ))
        
        console.print(f"[bold]Date:[/bold] {entry.date.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"[bold]Mood:[/bold] {entry.mood or 'Not specified'}")
        
        if entry.tags:
            console.print(f"[bold]Tags:[/bold] {', '.join(entry.tags)}")
        
        console.print(f"\n[bold]Content:[/bold]")
        console.print(Panel(entry.content, border_style="green"))
        
        if entry.insights:
            console.print(f"\n[bold blue]💡 AI Insights:[/bold blue]")
            console.print(Panel(entry.insights, border_style="blue"))
            
    except Exception as e:
        console.print(f"[red]Error reading entry: {e}[/red]")

@app.command()
def analyze(
    days: int = typer.Option(30, help="Analyze entries from last N days")
):
    """Analyze journal entries for patterns and insights"""
    if not db_manager or not journal_analyzer:
        initialize_app()
        if not journal_analyzer:
            console.print("[red]AI analysis not available. Please check your API key.[/red]")
            return
    
    console.print(Panel.fit(
        "[bold blue]🔍 Journal Analysis[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Get entries from specified period
        start_date = datetime.now() - timedelta(days=days)
        entries = db_manager.get_entries_by_date_range(start_date, datetime.now())
        
        if not entries:
            console.print(f"[yellow]No entries found in the last {days} days.[/yellow]")
            return
        
        console.print(f"[blue]Analyzing {len(entries)} entries from the last {days} days...[/blue]")
        
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
        
        # Perform analysis
        analysis = journal_analyzer.analyze_emotional_patterns(entries_data)
        
        if 'error' in analysis:
            console.print(f"[red]Analysis failed: {analysis['error']}[/red]")
            return
        
        console.print("\n[bold blue]📊 Emotional Pattern Analysis:[/bold blue]")
        console.print(Panel(analysis['analysis'], border_style="blue"))
        
        # Generate weekly summary if we have enough entries
        if len(entries) >= 3:
            console.print("\n[bold blue]📝 Weekly Summary:[/bold blue]")
            summary = journal_analyzer.generate_weekly_summary(entries_data[-7:])  # Last 7 entries
            console.print(Panel(summary, border_style="green"))
        
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")

@app.command()
def chat(
    entry_id: Optional[int] = typer.Option(None, help="Chat about a specific entry")
):
    """Interactive chat about your journal entries"""
    if not db_manager or not journal_assistant:
        initialize_app()
        if not journal_assistant:
            console.print("[red]Chat feature not available. Please check your API key.[/red]")
            return
    
    console.print(Panel.fit(
        "[bold blue]💬 Journal Chat[/bold blue]",
        border_style="blue"
    ))
    
    # Load entry context if specified
    context_entry = None
    if entry_id:
        try:
            context_entry = db_manager.get_entry(entry_id)
            if context_entry:
                console.print(f"[green]Loaded entry: {context_entry.title}[/green]")
                console.print(f"Date: {context_entry.date.strftime('%Y-%m-%d')}")
                console.print(f"Content: {context_entry.content[:200]}...")
            else:
                console.print(f"[red]Entry with ID {entry_id} not found.[/red]")
                return
        except Exception as e:
            console.print(f"[red]Error loading entry: {e}[/red]")
            return
    
    console.print("\n[bold]Start chatting about your journal![/bold]")
    console.print("Type 'exit' to quit, 'help' for commands.")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print("[green]Goodbye! Keep journaling! 📝[/green]")
                break
            
            if user_input.lower() == 'help':
                console.print("""
[bold]Available commands:[/bold]
- exit/quit/bye: End the chat
- help: Show this help
- context: Show current entry context
- clear: Clear conversation memory
                """)
                continue
            
            if user_input.lower() == 'context' and context_entry:
                console.print(f"\n[bold]Current context:[/bold]")
                console.print(f"Entry: {context_entry.title}")
                console.print(f"Date: {context_entry.date.strftime('%Y-%m-%d')}")
                console.print(f"Content: {context_entry.content}")
                continue
            
            if user_input.lower() == 'clear':
                journal_assistant.memory.clear()
                console.print("[green]Conversation memory cleared.[/green]")
                continue
            
            # Get AI response
            response = journal_assistant.chat_about_entry(user_input)
            console.print(f"\n[bold green]Assistant:[/bold green] {response}")
            
        except KeyboardInterrupt:
            console.print("\n[green]Goodbye! Keep journaling! 📝[/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

@app.command()
def stats():
    """Show journal statistics"""
    if not db_manager:
        initialize_app()
    
    console.print(Panel.fit(
        "[bold blue]📊 Journal Statistics[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Get all entries
        all_entries = db_manager.get_all_entries(1000)  # Get up to 1000 entries
        
        if not all_entries:
            console.print("[yellow]No entries found.[/yellow]")
            return
        
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
        
        # Display statistics
        console.print(f"[bold]Total Entries:[/bold] {total_entries}")
        console.print(f"[bold]Date Range:[/bold] {oldest_entry.date.strftime('%Y-%m-%d')} to {newest_entry.date.strftime('%Y-%m-%d')}")
        
        # Top moods
        if mood_counts:
            console.print(f"\n[bold]Top Moods:[/bold]")
            sorted_moods = sorted(mood_counts.items(), key=lambda x: x[1], reverse=True)
            for mood, count in sorted_moods[:5]:
                console.print(f"  {mood}: {count} entries")
        
        # Top tags
        if tag_counts:
            console.print(f"\n[bold]Top Tags:[/bold]")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            for tag, count in sorted_tags[:10]:
                console.print(f"  {tag}: {count} entries")
        
        # Writing streak (simplified)
        dates = sorted([entry.date.date() for entry in all_entries])
        if dates:
            current_streak = 0
            today = datetime.now().date()
            check_date = today
            
            while check_date in dates:
                current_streak += 1
                check_date -= timedelta(days=1)
            
            console.print(f"\n[bold]Current Writing Streak:[/bold] {current_streak} days")
        
    except Exception as e:
        console.print(f"[red]Error calculating statistics: {e}[/red]")

@app.command()
def export(
    format: str = typer.Option("json", help="Export format (json, txt)"),
    output_file: Optional[str] = typer.Option(None, help="Output file path")
):
    """Export journal entries"""
    if not db_manager:
        initialize_app()
    
    try:
        entries = db_manager.get_all_entries(1000)
        
        if not entries:
            console.print("[yellow]No entries to export.[/yellow]")
            return
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"journal_export_{timestamp}.{format}"
        
        if format == "json":
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
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        elif format == "txt":
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Daily Journal Assistant - Export\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in entries:
                    f.write(f"Entry #{entry.id}\n")
                    f.write(f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}\n")
                    f.write(f"Title: {entry.title}\n")
                    f.write(f"Mood: {entry.mood or 'Not specified'}\n")
                    f.write(f"Tags: {', '.join(entry.tags) if entry.tags else 'None'}\n")
                    f.write("-" * 30 + "\n")
                    f.write(entry.content + "\n")
                    if entry.insights:
                        f.write("\nAI Insights:\n")
                        f.write(entry.insights + "\n")
                    f.write("\n" + "=" * 50 + "\n\n")
        
        console.print(f"[green]✓ Exported {len(entries)} entries to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error exporting entries: {e}[/red]")

@app.command()
def setup():
    """Setup the journal assistant"""
    console.print(Panel.fit(
        "[bold blue]⚙️ Journal Assistant Setup[/bold blue]",
        border_style="blue"
    ))
    
    # Check if .env file exists
    env_file = ".env"
    if not os.path.exists(env_file):
        console.print(f"[yellow]Creating {env_file} file...[/yellow]")
        
        api_key = Prompt.ask("Enter your OpenAI API key")
        
        with open(env_file, 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
            f.write("DATABASE_URL=sqlite:///journal.db\n")
            f.write("APP_NAME=Daily Journal Assistant\n")
            f.write("APP_VERSION=1.0.0\n")
        
        console.print(f"[green]✓ {env_file} created successfully[/green]")
    else:
        console.print(f"[green]✓ {env_file} already exists[/green]")
    
    # Initialize database
    console.print("[blue]Initializing database...[/blue]")
    try:
        db = DatabaseManager()
        console.print("[green]✓ Database initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error initializing database: {e}[/red]")
        return
    
    # Test AI connection
    console.print("[blue]Testing AI connection...[/blue]")
    try:
        assistant = JournalAssistant()
        test_response = assistant.generate_title("This is a test journal entry.")
        console.print(f"[green]✓ AI connection successful[/green]")
        console.print(f"Test response: {test_response}")
    except Exception as e:
        console.print(f"[red]AI connection failed: {e}[/red]")
        console.print("Please check your API key and try again.")
    
    console.print("\n[bold green]🎉 Setup complete! You can now start journaling![/bold green]")
    console.print("Try: [bold]journal new[/bold] to create your first entry")

if __name__ == "__main__":
    app()
