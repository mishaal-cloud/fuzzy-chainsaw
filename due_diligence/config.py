"""Configuration for the AI Due Diligence Agent Tool."""

import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Model selection - Sonnet for research/analysis, configurable for writing
RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", "claude-sonnet-4-20250514")
WRITING_MODEL = os.getenv("WRITING_MODEL", "claude-sonnet-4-20250514")

# Output directory
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "outputs"))

# Max tokens per agent response
MAX_TOKENS_RESEARCH = 8192
MAX_TOKENS_ANALYSIS = 8192
MAX_TOKENS_WRITING = 16384

# Web search configuration
WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 10}
