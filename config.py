"""
Configuration file for Constitutional Helper.
All settings centralized for easy modification without editing code.
"""

import os

# ─────────────────────────────────────────────────────────────────
#  LLM CONFIGURATION
# ─────────────────────────────────────────────────────────────────
# Using Groq API for cloud-based LLM inference
# PERFORMANCE NOTE: 70B model gives best quality. For 3x faster responses, use:
#   LLM_MODEL = "llama-3.1-8b-instant"
LLM_MODEL = "llama-3.1-8b-instant"
LLM_MAX_TOKENS = 400  # Reduced for faster responses
LLM_TEMPERATURE = 0.5  # Increased from 0.0 to prevent repetition/looping in Twi

# ─────────────────────────────────────────────────────────────────
#  RAG CONFIGURATION
# ─────────────────────────────────────────────────────────────────
RAG_TOP_N = 5  # Increased for better context coverage
RAG_SIMILARITY_THRESHOLD = 0.28  # Higher threshold to filter out irrelevant 'noise'
CHUNKS_PATH = "constitution_chunks.json"
EMBEDDINGS_PATH = "constitution_embeddings.pkl"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ─────────────────────────────────────────────────────────────────
#  FILE CONFIGURATION
# ─────────────────────────────────────────────────────────────────
PDF_PATH = "Ghana Constitution.pdf"
PDF_MAX_SIZE_MB = 50

# ─────────────────────────────────────────────────────────────────
#  UI CONFIGURATION
# ─────────────────────────────────────────────────────────────────
PAGE_TITLE = "Constitutional Helper"
PAGE_ICON = "favicon.png"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# ─────────────────────────────────────────────────────────────────
#  THEME COLORS (Dark Slate #32394a)
# ─────────────────────────────────────────────────────────────────
THEME = {
    "BRAND_50": "#F1F2F4",
    "BRAND_100": "#E4E6E9",
    "BRAND_200": "#C9CED4",
    "BRAND_300": "#AEB5BF",
    "BRAND_400": "#939DAA",
    "BRAND_500": "#32394a",  # Primary dark slate
    "BRAND_600": "#2D333F",
    "BRAND_700": "#282E38",
    "BRAND_800": "#1F242C",
    "BRAND_900": "#161920",
    "BG": "#FFFFFF",
    "SURFACE": "#FAFAFA",
    "SURFACE2": "#F5F5F7",
    "BORDER": "#E5E7EB",
    "TEXT": "#1D1D1F",
    "TEXT2": "#86868B",
}

# ─────────────────────────────────────────────────────────────────
#  VALIDATION & LIMITS
# ─────────────────────────────────────────────────────────────────
MAX_QUESTION_LENGTH = 500
# No minimum length - allow any non-empty question
MAX_RETRIES = 2
REQUEST_TIMEOUT_SECONDS = 30

# ─────────────────────────────────────────────────────────────────
#  LANGUAGE SETTINGS
# ─────────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = ["English", "Twi"]
DEFAULT_LANGUAGE = "English"

# ─────────────────────────────────────────────────────────────────
#  AUDIO SETTINGS
# ─────────────────────────────────────────────────────────────────
ENABLE_AUDIO = True  
AUDIO_MAX_LENGTH = 5000  # Increased for long constitutional articles
TTS_VOICE_MAP = {
    "English": "en-NG-AbeoNeural", # High-quality West African Voice (closest to Ghana)
    "Twi": "en-NG-AbeoNeural",     
}

# ─────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────
LOG_FILE = "constitutional_helper.log"
LOG_LEVEL = "INFO"

# ─────────────────────────────────────────────────────────────────
#  QUICK TOPICS (Sidebar shortcuts)
# ─────────────────────────────────────────────────────────────────
QUICK_TOPICS = {
    "Police & Arrests": "What are my rights if I am arrested or stopped by the police in Ghana?",
    "Fundamental Rights": "What are the basic human rights every Ghanaian is entitled to?",
    "Presidential Rules": "What are the requirements to become President of Ghana?",
    "Making Laws": "How does Parliament actually make laws for the country?",
    "Land & Property": "What does the Constitution say about land ownership and property rights?",
    "Voting Rights": "Who is allowed to vote in Ghana and how is the process protected?",
    "Amending the Law": "Can we change the Constitution? How does that process work?"
}

# ─────────────────────────────────────────────────────────────────
#  STARTUP VALIDATION
# ─────────────────────────────────────────────────────────────────
# NOTE: PDF_PATH is optional (only needed for preprocessing chunks)
# At runtime, we use pre-processed chunks and embeddings
REQUIRED_FILES = [
    (CHUNKS_PATH, "Constitution data chunks"),
]

REQUIRED_ENV_VARS = [
    ("GROQ_API_KEY", "Groq API key for LLM inference"),
]
