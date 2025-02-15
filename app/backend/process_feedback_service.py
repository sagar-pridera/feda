# This file is used to process the feedback from the user
# - what to do with the feedback : 
#    - tagging the feedback as positive, negative or neutral
#    - categorizing the feedback
#    - summarizing the feedback based on categories
#    - finding the most common issues
# It will use the llm_service to get the response from the llm
# It will then save the response to the database

from typing import Dict, List, Optional
from enum import Enum
from .llm_service import LLMService
from .database_service import DatabaseService
import asyncio

class FeedbackSentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

    @classmethod
    def from_string(cls, value: str) -> 'FeedbackSentiment':
        """Convert string to FeedbackSentiment, handling common variations"""
        # Clean the input string
        cleaned = value.lower().strip().strip('.')
        
        # Map common variations to standard values
        sentiment_map = {
            'positive': cls.POSITIVE,
            'pos': cls.POSITIVE,
            'good': cls.POSITIVE,
            
            'negative': cls.NEGATIVE,
            'neg': cls.NEGATIVE,
            'bad': cls.NEGATIVE,
            
            'neutral': cls.NEUTRAL,
            'neu': cls.NEUTRAL,
            'mixed': cls.NEUTRAL
        }
        
        # Try to get the mapped sentiment, default to neutral if not found
        return sentiment_map.get(cleaned, cls.NEUTRAL)

class ProcessFeedbackService:
    def __init__(self, llm_service: LLMService, db_service: DatabaseService, batch_size: int = 50):
        self.llm_service = llm_service
        self.db_service = db_service
        self.batch_size = batch_size

    async def process_feedback_batch(self, feedbacks: List[Dict[str, str]]) -> List[Dict]:
        """Process a batch of feedback entries"""
        results = []
        
        # Process in batches
        for i in range(0, len(feedbacks), self.batch_size):
            batch = feedbacks[i:i + self.batch_size]
            
            # Process each aspect in batch
            sentiments = await self._analyze_sentiments_batch([f['feedback'] for f in batch])
            categories = await self._categorize_feedback_batch([f['feedback'] for f in batch])
            summaries = await self._summarize_feedback_batch([f['feedback'] for f in batch])
            
            # Combine results
            for j, feedback in enumerate(batch):
                result = {
                    "email": feedback.get('email', ''),
                    "original_feedback": feedback['feedback'],
                    "sentiment": sentiments[j],
                    "categories": categories[j],
                    "summary": summaries[j]
                }
                await self.db_service.save_processed_feedback(result)
                results.append(result)
                
        return results

    async def _analyze_sentiments_batch(self, feedbacks: List[str]) -> List[FeedbackSentiment]:
        """Analyze sentiments for a batch of feedbacks"""
        prompt = (
            "Analyze the sentiment of each feedback below. "
            "For each feedback, respond with exactly one word (positive, negative, or neutral) "
            "in a numbered list.\n\n"
        )
        for i, feedback in enumerate(feedbacks, 1):
            prompt += f"{i}. {feedback}\n"
        
        response = await self.llm_service.get_response_safe(prompt)
        
        # Parse response into list of sentiments
        sentiment_lines = [line.split('.', 1)[1].strip() if '.' in line else line.strip() 
                         for line in response.split('\n') if line.strip()]
        
        return [FeedbackSentiment.from_string(sent) for sent in sentiment_lines]

    async def _categorize_feedback_batch(self, feedbacks: List[str]) -> List[List[str]]:
        """Categorize a batch of feedbacks"""
        prompt = (
            "Categorize each feedback below into relevant categories. "
            "For each feedback, provide a comma-separated list of categories "
            "in a numbered list.\n\n"
        )
        for i, feedback in enumerate(feedbacks, 1):
            prompt += f"{i}. {feedback}\n"
        
        response = await self.llm_service.get_response_safe(prompt)
        
        # Parse response into list of category lists
        category_lines = [line.split('.', 1)[1].strip() if '.' in line else line.strip() 
                         for line in response.split('\n') if line.strip()]
        
        return [
            [cat.strip() for cat in line.split(',')]
            for line in category_lines
        ]

    async def _summarize_feedback_batch(self, feedbacks: List[str]) -> List[str]:
        """Summarize a batch of feedbacks"""
        prompt = (
            "Provide a brief summary for each feedback below. "
            "For each feedback, provide a one-line summary "
            "in a numbered list.\n\n"
        )
        for i, feedback in enumerate(feedbacks, 1):
            prompt += f"{i}. {feedback}\n"
        
        response = await self.llm_service.get_response_safe(prompt)
        
        # Parse response into list of summaries
        return [line.split('.', 1)[1].strip() if '.' in line else line.strip() 
                for line in response.split('\n') if line.strip()]

    async def analyze_common_issues(self, feedbacks: List[str]) -> Dict[str, int]:
        """Analyze multiple pieces of feedback to find common issues"""
        # Process in batches for large datasets
        all_categories = []
        for i in range(0, len(feedbacks), self.batch_size):
            batch = feedbacks[i:i + self.batch_size]
            categories_batch = await self._categorize_feedback_batch(batch)
            for cats in categories_batch:
                all_categories.extend(cats)
        
        return dict((category, all_categories.count(category)) 
                   for category in set(all_categories))



