from typing import Dict, Optional
from datetime import datetime

class DatabaseService:
    def __init__(self):
        """Initialize the database service"""
        self.feedback_store = []  # Simple in-memory storage

    async def initialize(self):
        """Initialize connection - not needed for in-memory storage"""
        pass

    async def save_processed_feedback(self, feedback_data: Dict) -> str:
        """Save processed feedback to memory"""
        # Add timestamp
        feedback_data['created_at'] = datetime.now()
        
        # Ensure email field exists
        if 'email' not in feedback_data:
            feedback_data['email'] = ""

        # Convert Enum to string if present
        if hasattr(feedback_data['sentiment'], 'value'):
            feedback_data['sentiment'] = feedback_data['sentiment'].value

        # Add to memory store
        self.feedback_store.append(feedback_data)
        
        return str(len(self.feedback_store) - 1)  # Return index as ID

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict]:
        """Retrieve processed feedback by ID"""
        try:
            index = int(feedback_id)
            if 0 <= index < len(self.feedback_store):
                return self.feedback_store[index]
        except ValueError:
            pass
        return None

    async def get_all_feedback(self) -> list[Dict]:
        """Retrieve all processed feedback"""
        return self.feedback_store

    async def close(self):
        """Cleanup - not needed for in-memory storage"""
        pass 