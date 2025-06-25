"""
Configuration settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model settings
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Default to gpt-4 if not specified
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # Default to openai if not specified
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))  # Default to 0 for deterministic output

# BigQuery settings
BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")

# API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Query settings
MAX_BYTES_BILLED = int(os.getenv("MAX_BYTES_BILLED", "500000000"))  # Default to 500MB
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "30"))  # Default to 30 seconds 