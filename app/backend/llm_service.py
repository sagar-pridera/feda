from typing import Optional
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
import os
from dotenv import load_dotenv
import logging

class LLMService:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """Initialize the LLM service with API key and model"""
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ API key must be provided either directly or through GROQ_API_KEY environment variable")
        
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=model
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
        before_sleep=lambda retry_state: logging.warning(
            f"Attempt {retry_state.attempt_number} failed. Retrying..."
        )
    )
    async def get_response(self, prompt: str) -> str:
        """
        Get response from LLM with retry logic for resilience
        Returns the text response from the model
        """
        try:
            response = self.llm.invoke(prompt)
            if not response or not response.content:
                raise Exception("Empty response from LLM")
            return response.content.strip()
        except Exception as e:
            logging.error(f"LLM error: {str(e)}")
            raise Exception(f"Failed to get response from LLM: {str(e)}")

    async def get_response_safe(self, prompt: str, default_response: str = "neutral") -> str:
        """
        A safer version of get_response that won't raise exceptions
        Returns default_response if all retries fail
        """
        try:
            return await self.get_response(prompt)
        except RetryError as e:
            logging.error(f"All retry attempts failed: {str(e)}")
            return default_response
        except Exception as e:
            logging.error(f"Unexpected error in LLM service: {str(e)}")
            return default_response





