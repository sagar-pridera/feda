"""
Feedback Processing Service

This module handles batch processing of user feedback through:
- Sentiment analysis
- Categorization
- Summarization
- Common issues identification

It coordinates between the LLM service for analysis and database service for storage.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from .llm_service import LLMService, ModelName
from .database_service import DatabaseService
from .models.feedback_models import FeedbackItem, ProcessedFeedback, Categories
from .config.processing_config import BatchConfig

# Configure logging
logger = logging.getLogger(__name__)

class FeedbackProcessor:
    """Service for batch processing feedback"""
    
    def __init__(
        self,
        model: ModelName = ModelName.MIXTRAL,
        batch_size: int = BatchConfig.DEFAULT_BATCH_SIZE,
        db_service: Optional[DatabaseService] = None
    ):
        """
        Initialize the feedback processor
        
        Args:
            model: LLM model to use for processing
            batch_size: Number of feedback items to process in each batch
            db_service: Database service for storing results
        """
        self.llm_service = LLMService(model=model)
        self.db_service = db_service or DatabaseService()
        self.batch_size = BatchConfig.validate_batch_size(batch_size)

    async def process_feedback_batch(self, feedback_items: List[Dict]) -> List[Dict]:
        """Process a batch of feedback items efficiently"""
        results: List[ProcessedFeedback] = []
        
        try:
            # Convert batch to FeedbackItems
            feedback_batch = [
                FeedbackItem(
                    text=item['feedback'],
                    email=item.get('email', '')
                ) for item in feedback_items
            ]

            # Process entire batch at once
            processed_batch = await self._process_feedback_batch(feedback_batch)
            
            # Save results and add to output
            for feedback_item, processed_result in zip(feedback_batch, processed_batch):
                try:
                    result = ProcessedFeedback(
                        email=feedback_item.email,
                        original_feedback=feedback_item.text,
                        sentiment=processed_result['sentiment'],
                        category=processed_result['category'],
                        subcategory=processed_result['subcategory'],
                        details=processed_result.get('details', ['general_feedback']),
                        summary=processed_result['summary'],
                        created_at=datetime.now().isoformat()
                    )
                    await self.db_service.save_processed_feedback(result.to_dict())
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing individual feedback: {str(e)}")
                    results.append(ProcessedFeedback.create_error_response(
                        feedback_item,
                        f"Processing error: {str(e)}"
                    ))
                
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            # Add error results for the entire batch
            results.extend([
                ProcessedFeedback.create_error_response(
                    FeedbackItem(text=item['feedback'], email=item.get('email', '')),
                    f"Batch processing error: {str(e)}"
                )
                for item in feedback_items
            ])
        
        return [result.to_dict() for result in results]

    async def _process_feedback_batch(self, feedback_items: List[FeedbackItem]) -> List[Dict]:
        """
        Process a batch of feedback items in a single API call
        
        Args:
            feedback_items: List of FeedbackItem objects
            
        Returns:
            List of processed results from LLM
        """
        # Prepare batch text
        feedback_texts = [item.text for item in feedback_items]
        
        # Process entire batch in one API call
        return await self.llm_service.process_feedback_batch(feedback_texts)

    async def analyze_common_issues(self, feedbacks: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Analyze multiple pieces of feedback to identify common issues
        
        Args:
            feedbacks: List of feedback texts to analyze
            
        Returns:
            Dictionary mapping categories to their subcategories and counts
        """
        category_analysis = {}
        
        # Process in batches
        for i in range(0, len(feedbacks), self.batch_size):
            batch = feedbacks[i:i + self.batch_size]
            try:
                batch_results = await self.llm_service.process_feedback_batch(batch)
                for result in batch_results:
                    category = result['category']
                    subcategory = result['subcategory']
                    
                    if category not in category_analysis:
                        category_analysis[category] = {}
                        
                    if subcategory not in category_analysis[category]:
                        category_analysis[category][subcategory] = 0
                        
                    category_analysis[category][subcategory] += 1
                    
            except Exception as e:
                logger.error(f"Error in batch analysis: {str(e)}", exc_info=True)
                continue

        return category_analysis

    @staticmethod
    def _count_and_sort_categories(categories: List[str]) -> Dict[str, int]:
        """Count and sort categories by frequency"""
        category_counts = {}
        for category in set(categories):
            count = categories.count(category)
            if count > 0:
                category_counts[category] = count

        return dict(sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))



