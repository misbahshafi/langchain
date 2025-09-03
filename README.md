# Daily Journal Assistant using LangChain

A powerful AI-powered journaling application built with LangChain that helps you maintain a daily journal with intelligent insights, mood analysis, and personalized prompts.

## Features

🤖 **AI-Powered Insights**
- Automatic mood analysis from your entries
- Intelligent title generation
- Smart tag extraction
- Personalized insights and suggestions

📝 **Rich Journaling Experience**
- Multiple journal prompt types (daily, reflection, gratitude, goals, freeform)
- Interactive CLI with beautiful formatting
- Mood tracking and emotional pattern analysis
- Tag-based organization

💬 **Interactive Chat**
- Chat with AI about your journal entries
- Get personalized advice and reflection questions
- Explore your thoughts and feelings with AI assistance

📊 **Analytics & Insights**
- Emotional pattern analysis over time
- Weekly summaries and progress tracking
- Writing streak tracking
- Export functionality (JSON, TXT)

🗄️ **Data Management**
- SQLite database for reliable storage
- Full CRUD operations on journal entries
- Data export and backup capabilities

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Quick Setup

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment:**
   ```bash
   python main.py setup
   ```
   This will prompt you for your OpenAI API key and create the necessary configuration files.

4. **Start journaling:**
   ```bash
   python main.py new
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///journal.db
APP_NAME=Daily Journal Assistant
APP_VERSION=1.0.0
```

### API Keys

- **OpenAI API Key**: Required for AI features. Get one from [OpenAI](https://platform.openai.com/api-keys)
- **Optional**: Anthropic or Google API keys for alternative LLM providers

## Usage

### Basic Commands

```bash
# Create a new journal entry
python main.py new

# Create entry with specific prompt type
python main.py new --prompt-type gratitude

# List recent entries
python main.py list

# List entries from last 7 days
python main.py list --days 7

# Read a specific entry
python main.py read 1

# Analyze your journal patterns
python main.py analyze

# Chat about your entries
python main.py chat

# Chat about a specific entry
python main.py chat --entry-id 1

# View statistics
python main.py stats

# Export your journal
python main.py export --format json

# Setup the application
python main.py setup
```

### Journal Prompt Types

1. **Daily** - General daily reflection
2. **Reflection** - Deeper self-reflection
3. **Gratitude** - Focus on appreciation
4. **Goal** - Goal setting and progress
5. **Freeform** - Open-ended writing

### Interactive Features

- **Rich CLI Interface**: Beautiful terminal interface with colors and formatting
- **Smart Prompts**: AI-generated suggestions based on your writing
- **Mood Tracking**: Automatic mood detection and tracking
- **Tag System**: Automatic tag extraction and manual tagging
- **Chat Mode**: Interactive conversations about your journal entries

## Project Structure

```
journal-assistant/
├── main.py              # Main application entry point
├── models.py            # Data models and database management
├── langchain_utils.py   # LangChain integration and AI processing
├── config.py            # Configuration and settings
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables template
├── README.md           # This file
├── data/               # Data directory (created automatically)
└── logs/               # Logs directory (created automatically)
```

## AI Features

### Mood Analysis
The AI analyzes your journal entries to detect emotional patterns and suggest mood tags.

### Title Generation
Automatically generates meaningful titles for your journal entries based on content.

### Tag Extraction
Intelligently extracts relevant tags from your entries for better organization.

### Insights Generation
Provides thoughtful insights and suggestions based on your journal content.

### Pattern Analysis
Analyzes emotional patterns across multiple entries to identify trends and growth areas.

## Database Schema

The application uses SQLite with the following schema:

- **journal_entries**: Main table storing journal entries
  - id, date, title, content, mood, tags, insights, timestamps

## Examples

### Creating Your First Entry

```bash
$ python main.py new
📝 New Journal Entry

Prompt: How was your day today? What were the highlights and challenges?

Suggestions:
  1. What made you smile today?
  2. What was the most challenging part of your day?
  3. What did you learn today?
  4. How did you feel overall today?

Start writing your journal entry:
(Type 'END' on a new line when finished)

Today was a productive day at work. I completed the project I've been working on for weeks, and my manager gave me positive feedback. I felt really accomplished and proud of my work.

END

🤖 Processing with AI...
✓ Mood detected: happy
✓ Tags: work, accomplishment, feedback, productivity

✓ Journal entry saved with ID: 1

💡 AI Insights:
It's wonderful to hear about your productive day and the positive feedback from your manager! This entry shows clear signs of professional growth and personal satisfaction. The completion of a long-term project is a significant achievement that demonstrates your dedication and skills. Consider reflecting on what specific strategies or approaches helped you succeed, as these insights can be valuable for future projects.
```

### Analyzing Patterns

```bash
$ python main.py analyze --days 30
🔍 Journal Analysis

Analyzing 15 entries from the last 30 days...

📊 Emotional Pattern Analysis:
Based on your recent entries, I notice several positive patterns emerging:

1. **Growth Mindset**: You consistently reflect on learning opportunities and personal development
2. **Gratitude Practice**: Regular expressions of appreciation for small moments and relationships
3. **Resilience**: You handle challenges with a constructive approach, focusing on solutions

**Mood Trends**: Your entries show a generally positive emotional trajectory with occasional stress during work deadlines, which is completely normal.

**Suggestions for Emotional Well-being**:
- Continue your gratitude practice as it's clearly benefiting your overall outlook
- Consider setting aside time for stress management during busy periods
- Your reflection habit is excellent for personal growth - keep it up!
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: OpenAI API key not found
   ```
   Solution: Run `python main.py setup` and enter your API key

2. **Database Error**
   ```
   Error: Database connection failed
   ```
   Solution: Check file permissions and ensure the data directory is writable

3. **Import Error**
   ```
   ModuleNotFoundError: No module named 'langchain'
   ```
   Solution: Install dependencies with `pip install -r requirements.txt`

### Getting Help

- Check the console output for detailed error messages
- Ensure all dependencies are installed correctly
- Verify your OpenAI API key is valid and has sufficient credits
- Check file permissions in the project directory

## Contributing

This is a complete, ready-to-use journaling application. Feel free to:

- Add new prompt types
- Implement additional AI features
- Enhance the CLI interface
- Add new export formats
- Implement cloud storage options

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the console output for error details
3. Ensure all requirements are met
4. Verify API key configuration

---

**Happy Journaling! 📝✨**

Start your journey of self-reflection and personal growth with AI-powered insights.
