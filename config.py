"""
Centralized configuration — loads all API keys and settings from environment variables.
Copy .env.example to .env and fill in your keys before running.
"""

import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


def get_llm():
    """Initialize and return the Azure OpenAI chat model."""
    return AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )


SPRINGER_API_KEY = os.getenv("SPRINGER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")
