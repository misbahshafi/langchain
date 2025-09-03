"""
LangChain utilities for the Daily Journal Assistant
"""
from typing import List, Dict, Any, Optional

# Try to import LangChain components, fall back to None if not available
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, PromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.callbacks.manager import CallbackManagerForChainRun
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LangChain not available: {e}")
    ChatOpenAI = None
    ChatPromptTemplate = None
    PromptTemplate = None
    HumanMessage = None
    SystemMessage = None
    LLMChain = None
    ConversationBufferMemory = None
    CallbackManagerForChainRun = None
    LANGCHAIN_AVAILABLE = False
import json
import re

from config import Config, JOURNAL_PROMPTS
from models import JournalEntryModel, JournalInsight

class JournalAssistant:
    """Main LangChain-powered journal assistant"""
    
    def __init__(self, api_key: str = None):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain components not available")
        
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=Config.DEFAULT_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
        self.memory = ConversationBufferMemory()
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup LangChain chains for different tasks"""
        
        # Mood analysis chain
        mood_analysis_template = """
        Analyze the emotional tone and mood of the following journal entry.
        Provide a brief mood assessment and identify key emotional themes.
        
        Journal Entry: {content}
        
        Please respond with:
        1. Primary mood (one word: happy, sad, anxious, peaceful, etc.)
        2. Emotional themes (comma-separated list)
        3. Brief explanation (1-2 sentences)
        
        Format your response as:
        Mood: [mood]
        Themes: [themes]
        Explanation: [explanation]
        """
        
        self.mood_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content"],
                template=mood_analysis_template
            ),
            memory=self.memory
        )
        
        # Insight generation chain
        insight_template = """
        As a thoughtful journaling assistant, analyze this journal entry and provide insights.
        
        Journal Entry: {content}
        Date: {date}
        Mood: {mood}
        
        Please provide:
        1. Key themes and patterns
        2. Personal growth observations
        3. Suggestions for reflection
        4. Emotional patterns noticed
        
        Be supportive, insightful, and encouraging. Focus on personal development and self-awareness.
        """
        
        self.insight_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content", "date", "mood"],
                template=insight_template
            ),
            memory=self.memory
        )
        
        # Title generation chain
        title_template = """
        Generate a concise, meaningful title for this journal entry.
        The title should capture the essence or main theme of the entry.
        
        Journal Entry: {content}
        
        Provide only the title, nothing else. Keep it under 10 words.
        """
        
        self.title_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content"],
                template=title_template
            )
        )
        
        # Tag extraction chain
        tag_template = """
        Extract relevant tags from this journal entry. Focus on:
        - Topics mentioned
        - Activities described
        - Emotions expressed
        - People or places mentioned
        
        Journal Entry: {content}
        
        Provide 3-5 relevant tags, separated by commas. Use lowercase, single words or short phrases.
        """
        
        self.tag_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content"],
                template=tag_template
            )
        )
        
        # Conversation chain for interactive journaling
        conversation_template = """
        You are a supportive journaling assistant. Help the user explore their thoughts and feelings.
        Ask thoughtful questions to encourage deeper reflection.
        
        Previous conversation: {history}
        Current input: {input}
        
        Respond as a caring, non-judgmental friend who helps with self-reflection.
        """
        
        self.conversation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["history", "input"],
                template=conversation_template
            ),
            memory=self.memory
        )
    
    def analyze_mood(self, content: str) -> Dict[str, str]:
        """Analyze mood from journal content"""
        try:
            response = self.mood_chain.run(content=content)
            return self._parse_mood_response(response)
        except Exception as e:
            print(f"Error analyzing mood: {e}")
            return {"mood": "neutral", "themes": "general", "explanation": "Unable to analyze mood"}
    
    def generate_insights(self, content: str, date: str, mood: str) -> str:
        """Generate insights from journal entry"""
        try:
            response = self.insight_chain.run(content=content, date=date, mood=mood)
            return response
        except Exception as e:
            print(f"Error generating insights: {e}")
            return "Unable to generate insights at this time."
    
    def generate_title(self, content: str) -> str:
        """Generate title for journal entry"""
        try:
            response = self.title_chain.run(content=content)
            return response.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Error generating title: {e}")
            return "Untitled Entry"
    
    def extract_tags(self, content: str) -> List[str]:
        """Extract tags from journal content"""
        try:
            response = self.tag_chain.run(content=content)
            tags = [tag.strip().lower() for tag in response.split(',')]
            return tags[:5]  # Limit to 5 tags
        except Exception as e:
            print(f"Error extracting tags: {e}")
            return []
    
    def process_journal_entry(self, content: str, date: str = None) -> Dict[str, Any]:
        """Process a complete journal entry with AI analysis"""
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Generate title
        title = self.generate_title(content)
        
        # Analyze mood
        mood_analysis = self.analyze_mood(content)
        mood = mood_analysis.get("mood", "neutral")
        
        # Extract tags
        tags = self.extract_tags(content)
        
        # Generate insights
        insights = self.generate_insights(content, date, mood)
        
        return {
            "title": title,
            "content": content,
            "mood": mood,
            "tags": tags,
            "insights": insights,
            "date": date,
            "mood_analysis": mood_analysis
        }
    
    def get_journal_prompt(self, prompt_type: str = "daily") -> Dict[str, Any]:
        """Get journal prompt and suggestions"""
        return JOURNAL_PROMPTS.get(prompt_type, JOURNAL_PROMPTS["daily"])
    
    def chat_about_entry(self, user_input: str) -> str:
        """Have a conversation about journal entry"""
        try:
            response = self.conversation_chain.run(input=user_input)
            return response
        except Exception as e:
            print(f"Error in conversation: {e}")
            return "I'm having trouble processing that. Could you try rephrasing?"
    
    def _parse_mood_response(self, response: str) -> Dict[str, str]:
        """Parse mood analysis response"""
        try:
            lines = response.strip().split('\n')
            mood_data = {}
            
            for line in lines:
                if line.startswith('Mood:'):
                    mood_data['mood'] = line.split(':', 1)[1].strip()
                elif line.startswith('Themes:'):
                    mood_data['themes'] = line.split(':', 1)[1].strip()
                elif line.startswith('Explanation:'):
                    mood_data['explanation'] = line.split(':', 1)[1].strip()
            
            return mood_data
        except Exception as e:
            print(f"Error parsing mood response: {e}")
            return {"mood": "neutral", "themes": "general", "explanation": "Unable to parse mood analysis"}

class JournalAnalyzer:
    """Advanced journal analysis using LangChain"""
    
    def __init__(self, api_key: str = None):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain components not available")
        
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=Config.DEFAULT_MODEL,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
    
    def analyze_emotional_patterns(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional patterns across multiple entries"""
        if not entries:
            return {"error": "No entries to analyze"}
        
        # Prepare entries for analysis
        entries_text = "\n\n".join([
            f"Date: {entry.get('date', 'Unknown')}\n"
            f"Mood: {entry.get('mood', 'Unknown')}\n"
            f"Content: {entry.get('content', '')[:500]}..."
            for entry in entries[-10:]  # Analyze last 10 entries
        ])
        
        analysis_template = """
        Analyze the emotional patterns in these journal entries over time.
        
        Entries:
        {entries}
        
        Please identify:
        1. Recurring emotional themes
        2. Mood trends and patterns
        3. Triggers or situations that affect mood
        4. Positive and negative patterns
        5. Suggestions for emotional well-being
        
        Provide a structured analysis focusing on patterns and insights.
        """
        
        try:
            prompt = PromptTemplate(
                input_variables=["entries"],
                template=analysis_template
            )
            chain = LLMChain(llm=self.llm, prompt=prompt)
            response = chain.run(entries=entries_text)
            return {"analysis": response, "entries_analyzed": len(entries)}
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def generate_weekly_summary(self, entries: List[Dict[str, Any]]) -> str:
        """Generate a weekly summary of journal entries"""
        if not entries:
            return "No entries to summarize this week."
        
        entries_text = "\n\n".join([
            f"Date: {entry.get('date', 'Unknown')}\n"
            f"Title: {entry.get('title', 'Untitled')}\n"
            f"Content: {entry.get('content', '')[:300]}..."
            for entry in entries
        ])
        
        summary_template = """
        Create a thoughtful weekly summary of these journal entries.
        
        Entries:
        {entries}
        
        Include:
        1. Key highlights and achievements
        2. Challenges faced and how they were handled
        3. Emotional journey throughout the week
        4. Personal growth and insights
        5. Goals and intentions for the coming week
        
        Write in a warm, supportive tone that celebrates progress and encourages continued reflection.
        """
        
        try:
            prompt = PromptTemplate(
                input_variables=["entries"],
                template=summary_template
            )
            chain = LLMChain(llm=self.llm, prompt=prompt)
            return chain.run(entries=entries_text)
        except Exception as e:
            return f"Unable to generate summary: {str(e)}"
