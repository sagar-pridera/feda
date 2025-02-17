"""
Configuration settings for LLM service
"""

from ..models.llm_models import ModelName

class LLMConfig:
    """Configuration settings for LLM"""
    DEFAULT_MODEL = ModelName.LLAMA
    DEFAULT_TEMPERATURE = 0.1
    MAX_RETRIES = 3

class PromptTemplates:
    """Collection of prompt templates"""
    SYSTEM_PROMPT = """You are a feedback analysis assistant. 
Provide responses in exact JSON format with no additional text.
Ensure categories are specific and relevant tags."""
    
    FEEDBACK_ANALYSIS = """Analyze this feedback and respond with JSON containing:
{
    "sentiment": "positive" | "negative" | "neutral",
    "categories": ["category1", "category2", ...],
    "summary": "One clear, concise summary line"
}

Feedback: "{feedback}"

Requirements:
- sentiment must be exactly one of: positive, negative, neutral
- categories must be specific, relevant tags without explanatory text
- summary must be one clear line without any prefixes or headers""" 