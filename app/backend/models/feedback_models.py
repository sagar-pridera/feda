"""
Data models for feedback processing
Contains all the data structures used in feedback processing
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
from ..llm_service import FeedbackSentiment

@dataclass
class FeedbackItem:
    """Structure for a single feedback item"""
    text: str
    email: str = ""

@dataclass
class ProcessedFeedback:
    """Structure for processed feedback data"""
    email: str
    original_feedback: str
    sentiment: str
    categories: List[str]
    summary: str
    created_at: str

    def to_dict(self) -> Dict:
        """Convert the feedback object to a dictionary"""
        return {
            'email': self.email,
            'original_feedback': self.original_feedback,
            'sentiment': self.sentiment,
            'categories': self.categories,
            'summary': self.summary,
            'created_at': self.created_at
        }

    @classmethod
    def create_error_response(cls, feedback_item: 'FeedbackItem', error_message: str) -> 'ProcessedFeedback':
        """Create an error response for failed feedback processing"""
        return cls(
            email=feedback_item.email,
            original_feedback=feedback_item.text,
            sentiment=FeedbackSentiment.NEUTRAL.value,
            categories=["Error Processing"],
            summary=f"Error processing feedback: {error_message}",
            created_at=datetime.now().isoformat()
        ) 