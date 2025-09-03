"""
Data models for the Daily Journal Assistant
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()

class JournalEntry(Base):
    """SQLAlchemy model for journal entries"""
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)
    insights = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JournalEntryModel(BaseModel):
    """Pydantic model for journal entries"""
    id: Optional[int] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    insights: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JournalInsight(BaseModel):
    """Model for AI-generated insights"""
    mood_analysis: str
    key_themes: List[str]
    suggestions: List[str]
    emotional_patterns: Dict[str, Any]
    growth_areas: List[str]

class JournalPrompt(BaseModel):
    """Model for journal prompts"""
    prompt_type: str  # "daily", "reflection", "gratitude", "goal", "freeform"
    prompt_text: str
    suggestions: List[str]

class DatabaseManager:
    """Database manager for journal entries"""
    
    def __init__(self, database_url: str = "sqlite:///journal.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = SessionLocal
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def create_entry(self, entry: JournalEntryModel) -> JournalEntry:
        """Create a new journal entry"""
        db = self.get_session()
        try:
            db_entry = JournalEntry(
                title=entry.title,
                content=entry.content,
                mood=entry.mood,
                tags=entry.tags,
                insights=entry.insights,
                date=entry.date
            )
            db.add(db_entry)
            db.commit()
            db.refresh(db_entry)
            return db_entry
        finally:
            db.close()
    
    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        """Get journal entry by ID"""
        db = self.get_session()
        try:
            return db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        finally:
            db.close()
    
    def get_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[JournalEntry]:
        """Get journal entries within date range"""
        db = self.get_session()
        try:
            return db.query(JournalEntry).filter(
                JournalEntry.date >= start_date,
                JournalEntry.date <= end_date
            ).order_by(JournalEntry.date.desc()).all()
        finally:
            db.close()
    
    def get_all_entries(self, limit: int = 100) -> List[JournalEntry]:
        """Get all journal entries with limit"""
        db = self.get_session()
        try:
            return db.query(JournalEntry).order_by(JournalEntry.date.desc()).limit(limit).all()
        finally:
            db.close()
    
    def update_entry(self, entry_id: int, entry: JournalEntryModel) -> Optional[JournalEntry]:
        """Update journal entry"""
        db = self.get_session()
        try:
            db_entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
            if db_entry:
                db_entry.title = entry.title
                db_entry.content = entry.content
                db_entry.mood = entry.mood
                db_entry.tags = entry.tags
                db_entry.insights = entry.insights
                db_entry.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(db_entry)
            return db_entry
        finally:
            db.close()
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete journal entry"""
        db = self.get_session()
        try:
            db_entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
            if db_entry:
                db.delete(db_entry)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def get_total_entries(self) -> int:
        """Get total number of entries"""
        db = self.get_session()
        try:
            return db.query(JournalEntry).count()
        finally:
            db.close()
    
    def get_recent_entries(self, limit: int = 5) -> List[JournalEntry]:
        """Get recent entries"""
        db = self.get_session()
        try:
            return db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    def get_entries_paginated(self, page: int = 1, per_page: int = 10) -> List[JournalEntry]:
        """Get entries with pagination"""
        db = self.get_session()
        try:
            offset = (page - 1) * per_page
            return db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).offset(offset).limit(per_page).all()
        finally:
            db.close()
    
    def get_entry_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        """Get entry by ID (alias for get_entry)"""
        return self.get_entry(entry_id)
