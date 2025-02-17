"""
Categories and classification models for feedback analysis
"""

class Categories:
    """Main categories and their subcategories"""
    CATEGORIES = {
        "Bug & Issues": {
            "UI/UX Bugs": ["display_error", "layout_issue", "responsive_bug", "visual_glitch"],
            "Functional Bugs": ["crash", "data_loss", "performance_lag", "feature_malfunction"],
            "Authentication Bugs": ["login_error", "session_issue", "access_denied", "token_expired"],
            "Payment Bugs": ["transaction_fail", "pricing_error", "checkout_issue", "refund_problem"],
            "Integration Bugs": ["api_error", "sync_fail", "third_party_issue", "connection_error"],
            "Security Bugs": ["vulnerability", "data_breach", "authentication_bypass", "injection_risk"]
        },
        "Feature Requests": {
            "New Features": ["new_functionality", "additional_option", "new_integration", "new_tool"],
            "Enhancements": ["improvement", "optimization", "better_ui", "workflow_enhancement"],
            "Customization": ["personalization", "configuration", "theming", "user_preference"],
            "Integration": ["api_feature", "third_party", "external_service", "data_sync"]
        },
        "Performance": {
            "Speed Issues": ["slow_loading", "response_time", "lag", "bottleneck"],
            "Resource Usage": ["high_cpu", "memory_leak", "battery_drain", "storage_issue"],
            "Scalability": ["load_handling", "concurrent_users", "data_volume", "traffic_spike"],
            "Optimization": ["efficiency", "resource_optimization", "caching", "performance_tuning"]
        },
        "User Satisfaction": {
            "Positive Feedback": ["praise", "appreciation", "satisfaction", "endorsement"],
            "Complaints": ["frustration", "dissatisfaction", "annoyance", "disappointment"],
            "Suggestions": ["recommendation", "improvement_idea", "user_request", "feedback"]
        },
        "App Experience": {
            "Usability": ["ease_of_use", "user_friendly", "intuitive", "accessibility"],
            "Content": ["ads", "pricing", "features", "information"],
            "Compatibility": ["device_support", "version_issues", "platform_specific", "compatibility_problem"]
        },
        "Uncategorized": {
            "General Comments": ["general_feedback", "comment", "statement", "observation"],
            "Unclear Feedback": ["ambiguous", "unclear", "incomplete", "unspecific"],
            "Other": ["miscellaneous", "unclassified", "other", "unknown"]
        }
    }

    @classmethod
    def get_subcategories(cls, category: str) -> dict:
        """Get subcategories for a main category"""
        return cls.CATEGORIES.get(category, {}) 