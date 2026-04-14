"""
Configuration file for Constitutional Helper.
All settings centralized for easy modification without editing code.
"""

import os

# ─────────────────────────────────────────────────────────────────
#  LLM CONFIGURATION
# ─────────────────────────────────────────────────────────────────
# Using Groq API for cloud-based LLM inference
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_MAX_TOKENS = 600
LLM_TEMPERATURE = 0.2  # Lower = more deterministic, better for factual Q&A

# ─────────────────────────────────────────────────────────────────
#  RAG CONFIGURATION
# ─────────────────────────────────────────────────────────────────
RAG_TOP_N = 5  # Number of relevant articles to retrieve
RAG_SIMILARITY_THRESHOLD = 0.15  # Minimum cosine similarity score
CHUNKS_PATH = "constitution_chunks.json"
EMBEDDINGS_PATH = "constitution_embeddings.pkl"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ─────────────────────────────────────────────────────────────────
#  FILE CONFIGURATION
# ─────────────────────────────────────────────────────────────────
PDF_PATH = "constitution.pdf"
PDF_MAX_SIZE_MB = 50

# ─────────────────────────────────────────────────────────────────
#  UI CONFIGURATION
# ─────────────────────────────────────────────────────────────────
PAGE_TITLE = "Constitutional Helper"
PAGE_ICON = "⚖"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# ─────────────────────────────────────────────────────────────────
#  THEME COLORS
# ─────────────────────────────────────────────────────────────────
THEME = {
    "BRAND_50": "#F0FDF4",
    "BRAND_100": "#DCFCE7",
    "BRAND_200": "#BBF7D0",
    "BRAND_300": "#86EFAC",
    "BRAND_400": "#4ADE80",
    "BRAND_500": "#22C55E",
    "BRAND_600": "#16A34A",
    "BRAND_700": "#15803D",
    "BRAND_800": "#166534",
    "BRAND_900": "#14532D",
    "BG": "#FFFFFF",
    "SURFACE": "#F8FAFC",
    "SURFACE2": "#F1F5F9",
    "BORDER": "#E2E8F0",
    "TEXT": "#0F172A",
    "TEXT2": "#475569",
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
AUDIO_MAX_LENGTH = 600  # Characters to convert to speech
TTS_LANGUAGE_MAP = {
    "English": "en-uk",
    "Twi": "ak",  # Akan (Twi) language code
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
    "Fundamental Rights": "What are the fundamental human rights of every Ghanaian under the Constitution?",
    "Rights When Arrested": "What are my rights if I am arrested in Ghana?",
    "Becoming President": "What are the qualifications to become President of Ghana?",
    "How Parliament Works": "How does Parliament work in Ghana and how are laws made?",
    "Role of the Judiciary": "What is the role of the Judiciary in Ghana?",
    "Elections in Ghana": "How do elections work in Ghana according to the Constitution?",
    "Amending Constitution": "How can Ghana's Constitution be amended?"
}

# ─────────────────────────────────────────────────────────────────
#  STARTUP VALIDATION
# ─────────────────────────────────────────────────────────────────
# NOTE: PDF_PATH is optional (only needed for preprocessing chunks)
# At runtime, we use pre-processed chunks and embeddings
REQUIRED_FILES = [
    (CHUNKS_PATH, "Constitution data chunks"),
    (EMBEDDINGS_PATH, "Pre-computed embeddings"),
]

REQUIRED_ENV_VARS = [
    ("GROQ_API_KEY", "Groq API key for LLM inference"),
]
