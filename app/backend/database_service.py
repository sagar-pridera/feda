"""
Database Service using Supabase
Handles all database operations for feedback storage and retrieval
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling database operations with Supabase"""

    def __init__(self):
        """Initialize Supabase client"""
        load_dotenv()
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.table_name = 'processed_feedback'

    async def initialize(self):
        """
        Initialize database connection
        This method is kept for compatibility with existing code
        """
        try:
            # Test connection by fetching a single row
            self.client.table(self.table_name).select("*").limit(1).execute()
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            raise

    async def save_processed_feedback(self, feedback_data: Dict) -> str:
        """
        Save processed feedback to Supabase
        
        Args:
            feedback_data: Dictionary containing processed feedback
            
        Returns:
            str: ID of the inserted record
        """
        try:
            # Ensure created_at is in ISO format
            if 'created_at' not in feedback_data:
                feedback_data['created_at'] = datetime.now().isoformat()

            # Insert data and return the ID
            result = self.client.table(self.table_name)\
                .insert(feedback_data)\
                .execute()

            return result.data[0]['id']

        except Exception as e:
            logger.error(f"Error saving feedback to Supabase: {str(e)}")
            raise

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict]:
        """
        Retrieve processed feedback by ID
        
        Args:
            feedback_id: ID of the feedback to retrieve
            
        Returns:
            Optional[Dict]: The feedback data if found, None otherwise
        """
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq('id', feedback_id)\
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error retrieving feedback from Supabase: {str(e)}")
            return None

    async def get_all_feedback(self) -> List[Dict]:
        """
        Retrieve all processed feedback
        
        Returns:
            List[Dict]: List of all feedback entries
        """
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .order('created_at', desc=True)\
                .execute()

            return result.data

        except Exception as e:
            logger.error(f"Error retrieving all feedback from Supabase: {str(e)}")
            return []

    async def close(self):
        """
        Close database connection
        This method is kept for compatibility
        """
        # Supabase client doesn't require explicit cleanup
        pass 