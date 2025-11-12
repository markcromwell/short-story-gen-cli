"""
Constants used across the story generation system.
"""

# Default timeout for AI generation calls (10 minutes)
# Large models (30B+ parameters) can take several minutes to generate
DEFAULT_TIMEOUT_SECONDS = 600

# Default retry attempts for generation failures
DEFAULT_MAX_RETRIES = 3

# Default AI models
DEFAULT_MODEL = "anthropic/claude-3-5-sonnet-20241022"
