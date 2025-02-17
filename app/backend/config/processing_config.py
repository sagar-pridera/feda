"""
Configuration settings for feedback processing
"""

class BatchConfig:
    """Configuration for batch processing"""
    DEFAULT_BATCH_SIZE = 50
    MIN_BATCH_SIZE = 10
    MAX_BATCH_SIZE = 100

    @staticmethod
    def validate_batch_size(size: int) -> int:
        """Validate and adjust batch size to be within acceptable range"""
        return max(min(size, BatchConfig.MAX_BATCH_SIZE), BatchConfig.MIN_BATCH_SIZE) 