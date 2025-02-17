"""
Data models for LLM service responses and configurations
"""

from typing import List
from enum import Enum
from pydantic import BaseModel, Field, validator
from .categories import Categories  # Add this import

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
    category: str
    subcategory: str
    details: List[str] = Field(default_factory=lambda: ["general_feedback"])
    summary: str = Field(..., min_length=10, max_length=200)

    @validator('sentiment', pre=True)
    def validate_sentiment(cls, v):
        """Normalize sentiment values"""
        if isinstance(v, str):
            # Map common variations to valid sentiments
            sentiment_mapping = {
                'positive': 'positive',
                'praise': 'positive',
                'good': 'positive',
                'great': 'positive',
                'negative': 'negative',
                'bad': 'negative',
                'issue': 'negative',
                'problem': 'negative',
                'bug': 'negative',
                'neutral': 'neutral',
                'suggestion': 'neutral',
                'feature_request': 'neutral',
                'request': 'neutral'
            }
            normalized = sentiment_mapping.get(v.lower(), 'neutral')
            return FeedbackSentiment(normalized)
        return v

    @validator('category')
    def validate_category(cls, category):
        """Ensure category is from predefined list"""
        # Map common variations to standard categories
        category_mapping = {
            'Bug': 'Bug & Issues',
            'Bugs': 'Bug & Issues',
            'Feature': 'Feature Requests',
            'Features': 'Feature Requests',
            'Performance Issues': 'Performance',
            'Performance Problems': 'Performance'
        }
        
        # Normalize the category
        normalized_category = category_mapping.get(category, category)
        
        if normalized_category not in Categories.CATEGORIES and normalized_category != 'Error':
            raise ValueError(f"Invalid category: {category}. Must be one of: {list(Categories.CATEGORIES.keys())}")
        return normalized_category

    @validator('subcategory')
    def validate_subcategory(cls, subcategory, values):
        """Ensure subcategory belongs to the category"""
        category = values.get('category')
        if category == 'Error':
            return subcategory
            
        # Get all valid subcategories for the category
        valid_subcategories = set()
        for subcat_group in Categories.CATEGORIES.get(category, {}).keys():
            valid_subcategories.add(subcat_group)
            # Also add the individual details as possible subcategories
            valid_subcategories.update(Categories.CATEGORIES[category][subcat_group])
            
        if subcategory not in valid_subcategories:
            # Try to find the most appropriate subcategory group
            for subcat_group, details in Categories.CATEGORIES[category].items():
                if subcategory in details:
                    return subcat_group
            # If still not found, use a default subcategory
            if category == 'Performance':
                return 'Speed Issues'
            elif category == 'Bug & Issues':
                return 'UI/UX Bugs'
            elif category == 'Feature Requests':
                return 'New Features'
            
        return subcategory

    @validator('details', pre=True)
    def ensure_details(cls, v, values):
        """Ensure details is never empty"""
        if not v or len(v) == 0:
            category = values.get('category', 'Uncategorized')
            subcategory = values.get('subcategory', 'General Comments')
            
            # Get default detail based on category
            if category == 'Uncategorized':
                return ["general_feedback"]
            elif category == 'User Satisfaction':
                return ["feedback"]
            elif category == 'App Experience':
                return ["user_feedback"]
            else:
                return ["unspecified"]
        return v 