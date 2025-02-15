import json
import streamlit as st
from typing import Dict, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

class DatabaseService:
    def __init__(self, cred_path: Optional[str] = None):
        """Initialize the Firebase database service"""
        load_dotenv()
        
        # Try to get credentials from different sources
        self.cred_dict = self._get_credentials(cred_path)
        self.db = None
        self.collection_name = 'processed_feedback'

    def _get_credentials(self, cred_path: Optional[str] = None):
        """Get credentials from file or Streamlit secrets"""
        # First try Streamlit secrets
        try:
            return json.loads(st.secrets["firebase"]["service_account_key"])
        except (KeyError, AttributeError):
            # If not in Streamlit Cloud, try local file
            local_cred_path = cred_path or os.getenv("FIREBASE_CRED_PATH")
            if not local_cred_path or not os.path.exists(local_cred_path):
                raise ValueError("Firebase credentials not found in Streamlit secrets or local file")
            
            with open(local_cred_path) as f:
                return json.load(f)

    async def initialize(self):
        """Initialize Firebase connection"""
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.cred_dict)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()

    async def save_processed_feedback(self, feedback_data: Dict) -> str:
        """Save processed feedback to Firebase"""
        if not self.db:
            raise Exception("Database not initialized. Call initialize() first.")

        # Convert Enum to string if present
        if hasattr(feedback_data['sentiment'], 'value'):
            feedback_data['sentiment'] = feedback_data['sentiment'].value

        # Add timestamp
        feedback_data['created_at'] = datetime.now()
        
        # Ensure email field exists
        if 'email' not in feedback_data:
            feedback_data['email'] = ""

        # Add to Firestore
        doc_ref = self.db.collection(self.collection_name).document()
        doc_ref.set(feedback_data)
        
        return doc_ref.id

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict]:
        """Retrieve processed feedback by ID"""
        if not self.db:
            raise Exception("Database not initialized. Call initialize() first.")

        doc_ref = self.db.collection(self.collection_name).document(feedback_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None

    async def get_all_feedback(self) -> list[Dict]:
        """Retrieve all processed feedback"""
        if not self.db:
            raise Exception("Database not initialized. Call initialize() first.")

        docs = self.db.collection(self.collection_name).stream()
        return [doc.to_dict() for doc in docs]

    async def close(self):
        """Cleanup (not needed for Firebase but kept for interface consistency)"""
        pass 