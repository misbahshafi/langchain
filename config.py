"""
Configuration settings for the Daily Journal Assistant
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "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")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///journal.db")
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "Daily Journal Assistant")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # LLM Settings
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000
    
    # Journal Settings
    MAX_ENTRY_LENGTH: int = 5000
    DEFAULT_PROMPT_TYPE: str = "daily"
    
    # File Paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            return False
        return True

# Pre-defined journal prompts
JOURNAL_PROMPTS = {
    "daily": {
        "prompt": "How was your day today? What were the highlights and challenges?",
        "suggestions": [
            "What made you smile today?",
            "What was the most challenging part of your day?",
            "What did you learn today?",
            "How did you feel overall today?"
        ]
    },
    "reflection": {
        "prompt": "Take a moment to reflect on your recent experiences. What patterns do you notice?",
        "suggestions": [
            "What recurring themes have you noticed lately?",
            "How have you grown recently?",
            "What would you like to change?",
            "What are you grateful for?"
        ]
    },
    "gratitude": {
        "prompt": "Write about what you're grateful for today.",
        "suggestions": [
            "What people are you grateful for?",
            "What experiences brought you joy?",
            "What simple pleasures did you enjoy?",
            "What opportunities are you thankful for?"
        ]
    },
    "goal": {
        "prompt": "Reflect on your goals and progress. What steps are you taking?",
        "suggestions": [
            "What goals are you working towards?",
            "What progress have you made recently?",
            "What obstacles are you facing?",
            "What's your next step?"
        ]
    },
    "freeform": {
        "prompt": "Write freely about whatever is on your mind.",
        "suggestions": [
            "What's weighing on your mind?",
            "What are you excited about?",
            "What questions do you have?",
            "What would you like to explore?"
        ]
    }
}

# Mood options
MOOD_OPTIONS = [
    "😊 Happy", "😔 Sad", "😰 Anxious", "😌 Peaceful", "😤 Frustrated",
    "🤔 Contemplative", "😴 Tired", "🚀 Energized", "😍 Excited", "😌 Content",
    "😟 Worried", "😎 Confident", "😅 Overwhelmed", "😌 Relaxed", "😡 Angry"
]

# Common tags
COMMON_TAGS = [
    "work", "family", "friends", "health", "travel", "learning", "creativity",
    "exercise", "food", "nature", "music", "books", "movies", "relationships",
    "goals", "challenges", "success", "gratitude", "reflection", "future"
]
