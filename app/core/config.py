"""
Configuration settings for the SQL Agent
All settings can be overridden with environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AI Model Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))  # 0 = deterministic responses

# BigQuery Database Configuration
BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Query Limits and Safety
MAX_BYTES_BILLED = int(os.getenv("MAX_BYTES_BILLED", "10000000000").split('#')[0].strip())  # 10GB limit (increased from 5GB)
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "90").split('#')[0].strip())  # 90 seconds timeout (increased from 60) 