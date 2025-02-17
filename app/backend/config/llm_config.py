"""
Configuration settings for LLM service
"""

from ..models.llm_models import ModelName
from ..models.categories import Categories

class LLMConfig:
    """Configuration settings for LLM"""
    DEFAULT_MODEL = ModelName.LLAMA
    DEFAULT_TEMPERATURE = 0.1
    MAX_RETRIES = 3

class PromptTemplates:
    """Collection of prompt templates"""
    SYSTEM_PROMPT = """You are a feedback analysis assistant specialized in software feedback categorization.
Provide responses in exact JSON format with no additional text.
Use predefined categories and tags for classification."""
    
    FEEDBACK_ANALYSIS = """Analyze this feedback and respond with JSON containing:
{
    "sentiment": "positive" | "negative" | "neutral",
    "category": "<main_category>",
    "subcategory": "<specific_subcategory>",
    "tag": ["specific_tag1", "specific_tag2"],
    "summary": "One clear, concise summary line"
}

Guidelines for categorization and tagging:
1. Bug & Issues: 
   - Tags: crash, ui_issue, login_error, performance_lag, display_error, etc.
2. Feature Requests: 
   - Tags: new_feature, dark_mode, customization, enhancement, etc.
3. Performance: 
   - Tags: slow_loading, performance_lag, optimization, etc.
4. User Satisfaction: 
   - Tags: praise, complaint, suggestion, feedback, etc.
5. App Experience: 
   - Tags: ads, compatibility, usability, device_issue, etc.

For example:
- "App keeps crashing" → Tags: ["crash", "bug"]
- "Need dark mode" → Tags: ["dark_mode", "customization"]
- "Too many ads" → Tags: ["ads", "content_issue"]
- "Great app!" → Tags: ["praise", "positive"]
- "Can't login" → Tags: ["login_error", "auth_issue"]

Categories and Subcategories:
{json.dumps(Categories.CATEGORIES, indent=2)}

Feedback: "{feedback}"

Requirements:
- Choose specific, relevant tags that describe the feedback
- Include at least one tag, maximum three tags
- Tags should be lowercase and use underscores for spaces
- Tags should reflect both the category and specific issue
- Summary should capture the main point concisely""" 