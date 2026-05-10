"""Configuration module for Office Assistant MVP."""
import os
from pathlib import Path

# Try to load from .env file if it exists
def load_env():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env if exists
load_env()

# Get OpenAI API key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# LLM Configuration
LLM_MODEL = "gpt-4.1-mini"
LLM_TEMPERATURE = 0.3

# Validate API key
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables or .env file. "
        "Please set your OpenAI API key."
    )
