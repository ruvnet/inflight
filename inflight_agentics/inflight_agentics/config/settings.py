"""Configuration settings for the Inflight Agentics system."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Kafka Settings
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "flight-events")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Default retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds

# Validate required settings
if OPENAI_API_KEY == "your-openai-api-key":
    import warnings
    warnings.warn(
        "OpenAI API key not set. Please set OPENAI_API_KEY environment variable.",
        RuntimeWarning
    )
