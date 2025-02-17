"""
Data models for LLM service responses and configurations
"""

from typing import List
from enum import Enum
from pydantic import BaseModel, Field, validator

class ModelName(Enum):
    """Available LLM models"""
    MIXTRAL = "mixtral-8x7b-32768"
    LLAMA = "llama2-70b-4096"
    GPT4 = "gpt-4"

class FeedbackSentiment(str, Enum):
    """Valid sentiment values"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class FeedbackResponse(BaseModel):
    """Structured feedback response with validation"""
    sentiment: FeedbackSentiment
    categories: List[str] = Field(..., min_items=1)
    summary: str = Field(..., min_length=10, max_length=200)

    @validator('categories')
    def validate_categories(cls, categories):
        """Ensure categories are properly formatted"""
        return [cat.strip() for cat in categories if cat.strip()]

    @validator('summary')
    def validate_summary(cls, summary):
        """Ensure summary is properly formatted"""
        return summary.strip().rstrip('.') 