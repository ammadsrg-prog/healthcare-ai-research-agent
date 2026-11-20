"""
Loads the project's settings from the .env file.

Every other file imports settings from here, for example:
    from config.settings import AWS_REGION
"""

import os

from dotenv import load_dotenv

# Read the .env file and put its values into the environment
load_dotenv()

OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")

# Optional safety guardrail. If the ID is empty, the app runs without it (a "feature flag").
BEDROCK_GUARDRAIL_ID = os.getenv("BEDROCK_GUARDRAIL_ID", "")
BEDROCK_GUARDRAIL_VERSION = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")
