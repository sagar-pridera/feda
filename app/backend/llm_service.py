"""
LLM Service for processing feedback using Groq
"""

from typing import Dict, List
import groq
import os
from dotenv import load_dotenv
import json
import logging

from .models.llm_models import ModelName, FeedbackResponse, FeedbackSentiment
from .config.llm_config import LLMConfig, PromptTemplates
from .models.categories import Categories

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model: ModelName = LLMConfig.DEFAULT_MODEL):
        """Initialize LLM service with specified model"""
        load_dotenv()
        self.model = model
        self._initialize_client()
        self.logger = logging.getLogger(__name__)

    def _initialize_client(self) -> None:
        """Initialize the Groq client with API key"""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = groq.Groq(api_key=api_key)

    def _create_chat_completion(self, messages: list, temperature: float = LLMConfig.DEFAULT_TEMPERATURE) -> str:
        """Create a chat completion with the specified messages"""
        try:
            completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model.value,
                temperature=temperature,
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}")
            raise

    def _parse_llm_response(self, response: str) -> FeedbackResponse:
        """Parse and validate LLM response"""
        try:
            # Clean the response if needed
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:-3]
            
            # Parse JSON and validate with Pydantic model
            data = json.loads(cleaned_response)
            return FeedbackResponse(**data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            raise ValueError(f"Error parsing response: {str(e)}")

    async def process_feedback(self, feedback: str) -> Dict:
        """Process a single piece of feedback"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": PromptTemplates.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": PromptTemplates.FEEDBACK_ANALYSIS.format(feedback=feedback)
                }
            ]
            
            response = self._create_chat_completion(messages)
            parsed_response = self._parse_llm_response(response)
            
            return {
                "sentiment": parsed_response.sentiment,
                "category": parsed_response.category,
                "subcategory": parsed_response.subcategory,
                "details": parsed_response.details,
                "summary": parsed_response.summary
            }

        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return {
                "sentiment": "neutral",
                "category": "Error",
                "subcategory": "Processing Error",
                "details": ["error_processing"],
                "summary": f"Error processing feedback: {str(e)}"
            }

    async def get_response_safe(self, prompt: str) -> str:
        """
        Safely get a response from the LLM with error handling
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: The LLM's response or error message
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": PromptTemplates.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            return self._create_chat_completion(messages)
        except Exception as e:
            self.logger.error(f"Error in LLM processing: {str(e)}")
            return f"Error: {str(e)}"

    async def process_feedback_batch(self, feedbacks: List[str]) -> List[Dict]:
        """
        Process multiple feedback items in a single API call
        
        Args:
            feedbacks: List of feedback texts to process
            
        Returns:
            List of processed results
        """
        prompt = f"""Analyze each feedback item and provide a JSON array of results.
Each result should have:
- sentiment: exactly one of "positive", "negative", "neutral"
- category: one of {list(Categories.CATEGORIES.keys())}
- subcategory: specific subcategory from the category
- details: array of specific details
- summary: one clear, concise summary line

Categories and Subcategories:
{json.dumps(Categories.CATEGORIES, indent=2)}

Feedback items to analyze:
{json.dumps(feedbacks, indent=2)}

Respond with a JSON array of results only, no additional text."""

        try:
            messages = [
                {
                    "role": "system",
                    "content": PromptTemplates.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self._create_chat_completion(messages)
            results = json.loads(response)
            
            # Validate each result
            validated_results = []
            for result in results:
                try:
                    validated_result = FeedbackResponse(**result).dict()
                    validated_results.append(validated_result)
                except Exception as e:
                    logger.error(f"Validation error for result: {str(e)}")
                    validated_results.append({
                        "sentiment": "neutral",
                        "category": "Error",
                        "subcategory": "Validation Error",
                        "details": ["error_processing"],
                        "summary": f"Error validating feedback: {str(e)}"
                    })
            
            return validated_results

        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            # Return error results for each feedback
            return [
                {
                    "sentiment": "neutral",
                    "category": "Error",
                    "subcategory": "Processing Error",
                    "details": ["error_processing"],
                    "summary": f"Error processing feedback: {str(e)}"
                }
                for _ in feedbacks
            ]





