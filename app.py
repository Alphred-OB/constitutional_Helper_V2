"""
Constitutional Helper - Ghana Constitution AI Assistant
=========================================================

Real-time AI-powered answers to constitutional questions using semantic search (RAG)
and large language models. Supports English and Asante Twi with audio output.

Author: GhanaLex Team
Version: 1.0.0
"""

import logging
import os
import sys
import io
import base64
import re
import hashlib
from typing import Optional, Tuple
from html import escape

# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE CACHE (Speeds up repeated/common questions)
# ─────────────────────────────────────────────────────────────────────────────
_response_cache = {}
CACHE_MAX_SIZE = 100  # Maximum cached responses

def get_cache_key(question: str, language: str) -> str:
    """Generate cache key from question and language."""
    key = f"{question.strip().lower()}:{language}"
    return hashlib.md5(key.encode()).hexdigest()[:16]

def get_cached_response(question: str, language: str) -> Optional[str]:
    """Get cached response if available."""
    key = get_cache_key(question, language)
    return _response_cache.get(key)

def set_cached_response(question: str, language: str, response: str) -> None:
    """Cache a response, evicting oldest if at capacity."""
    global _response_cache
    if len(_response_cache) >= CACHE_MAX_SIZE:
        # Remove oldest entry
        _response_cache.pop(next(iter(_response_cache)))
    key = get_cache_key(question, language)
    _response_cache[key] = response


import streamlit as st
from groq import Groq
from gtts import gTTS
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

from config import *
from icons import svg

# ─────────────────────────────────────────────────────────────────────────────
#  DEPLOYMENT DETECTION
# ─────────────────────────────────────────────────────────────────────────────
# Detect if running on Streamlit Cloud or locally
IS_STREAMLIT_CLOUD = "STREAMLIT_SERVER_HEADLESS" in os.environ
DEPLOYMENT_ENV = "cloud" if IS_STREAMLIT_CLOUD else "local"

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  STARTUP VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def validate_startup() -> bool:
    """
    Validate all required configuration on app startup.
    
    Returns:
        bool: True if all checks pass, False otherwise
    
    Raises:
        SystemExit: If validation fails
    """
    logger.info("Starting Constitutional Helper...")
    failures = []
    
    # Check environment variables
    load_dotenv()
    for env_var, description in REQUIRED_ENV_VARS:
        try:
            value = st.secrets.get(env_var) or os.getenv(env_var)
        except (AttributeError, FileNotFoundError):
            value = os.getenv(env_var)
        
        if not value:
            failures.append(f"Missing {description} ({env_var})")
            logger.error(f"Missing: {description}")
    
    # Check required files
    for file_path, description in REQUIRED_FILES:
        if not os.path.exists(file_path):
            failures.append(f"Missing {description} ({file_path})")
            logger.error(f"Missing file: {file_path}")
    
    if failures:
        error_msg = "Startup validation failed:\n\n" + "\n".join(f"• {f}" for f in failures)
        st.error(error_msg)
        logger.error(f"Startup failed: {error_msg}")
        st.stop()
    
    logger.info("Startup validation passed")
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  API & MODEL INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def initialize_groq_client() -> Groq:
    """
    Initialize Groq API client with proper error handling.
    
    Returns:
        Groq: Initialized Groq client
    
    Raises:
        SystemExit: If API key is not configured
    """
    try:
        key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    except (AttributeError, FileNotFoundError):
        key = os.getenv("GROQ_API_KEY")
    
    if not key:
        st.error("GROQ_API_KEY not configured. Check .env or Streamlit secrets.")
        logger.error("GROQ_API_KEY missing")
        sys.exit(1)
    
    try:
        client = Groq(api_key=key)
        logger.info("Groq client initialized")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        st.error(f"Failed to initialize Groq API: {e}")
        sys.exit(1)


@st.cache_resource
def initialize_rag():
    """
    Load constitution chunks and embeddings for semantic search.
    
    Returns:
        Tuple[List, np.ndarray]: (chunks, embeddings)
    
    Raises:
        SystemExit: If RAG initialization fails
    """
    try:
        from rag import load_chunks, load_or_build_embeddings
        
        logger.info("Loading RAG components...")
        chunks = load_chunks(CHUNKS_PATH)
        embeddings = load_or_build_embeddings(chunks, EMBEDDINGS_PATH)
        
        logger.info(f"RAG ready: {len(chunks)} chunks, embeddings shape {embeddings.shape}")
        return chunks, embeddings
    
    except Exception as e:
        logger.error(f"RAG initialization failed: {e}", exc_info=True)
        st.error(f"Failed to load constitution data: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  INPUT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def validate_question(question: str) -> Tuple[bool, str]:
    """
    Validate user question for length, format, and prompt injection attempts.
    
    Args:
        question: User's question text
    
    Returns:
        Tuple[bool, str]: (is_valid, message_or_cleaned_question)
    """
    if not question or len(question.strip()) == 0:
        return False, "Question cannot be empty"
    
    question = question.strip()
    
    if len(question) > MAX_QUESTION_LENGTH:
        return False, f"Question too long (maximum {MAX_QUESTION_LENGTH} characters)"
    
    # Check for prompt injection patterns
    injection_patterns = [
        r"ignore\s+previous",
        r"forget\s+(?:the|your)\s+system",
        r"new\s+instructions",
        r"bypass\s+(?:the\s+)?system",
        r"system\s+override",
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            logger.warning(f"Blocked potential prompt injection: {question[:50]}")
            return False, "Invalid question format detected"
    
    return True, question


# ─────────────────────────────────────────────────────────────────────────────
#  HTML SECURITY & FORMATTING
# ─────────────────────────────────────────────────────────────────────────────
def escape_and_format_html(text: str) -> str:
    """
    Safely escape HTML and apply safe formatting.
    
    Args:
        text: Raw text from LLM
    
    Returns:
        str: HTML-safe formatted text
    """
    # First escape all HTML
    text = escape(text)
    
    # Then selectively restore safe markdown-like formatting
    text = re.sub(r'\\\*\\\*(.*?)\\\*\\\*', r'<strong>\1</strong>', text)
    
    return text


def highlight_articles(text: str) -> str:
    """
    Highlight article references with styled badges.
    """
    book_svg = svg('book', 12, 'currentColor')
    return re.sub(
        r'\[Article\s*(\d+\w*)\]',
        f'<span class="art-badge">{book_svg} Art.\\1</span>',
        text,
        flags=re.IGNORECASE
    )


def format_reply(text: str) -> str:
    """
    Format LLM response with clean HTML markup, semantic references, and checklist items.
    """
    # Escape HTML first
    text = escape_and_format_html(text)
    
    # Highlight articles
    text = highlight_articles(text)
    
    # Parse into structured HTML
    lines = text.split('\n')
    out, in_list, in_refs = [], False, False
    check_svg = svg('check', 14, 'currentColor')
    
    for line in lines:
        s = line.strip()
        
        if 'REFERENCES:' in s or 'RESOURCES:' in s:
            if in_list:
                out.append('</div>')
                in_list = False
            
            out.append(
                f'<div class="ref-block">'
                f'<div class="ref-label">{svg("library", 14, "currentColor")} References</div>'
            )
            in_refs = True
            continue
        
        if s.startswith('- ') or s.startswith('• ') or s.startswith('* '):
            if not in_list:
                out.append('<div class="checklist">')
                in_list = True
            out.append(f'<div class="check-item"><div class="check-icon">{check_svg}</div>'
                      f'<span>{s[2:]}</span></div>')
        else:
            if in_list:
                out.append('</div>')
                in_list = False
            if s:
                if s.startswith('&gt;'):
                    s = s[4:].strip()
                out.append(f'<p style="margin-bottom:12px">{s}</p>')
    
    if in_list:
        out.append('</div>')
    if in_refs:
        out.append('</div>')
    
    return ''.join(out)


# ─────────────────────────────────────────────────────────────────────────────
#  RAG-POWERED LLM QUERY
# ─────────────────────────────────────────────────────────────────────────────
def stream_res(question: str, language: str, client: Groq, chunks, embeddings):
    """
    Generator that streams constitutional answers chunk by chunk.
    Handles small talk and greetings gracefully if no RAG results are found.
    """
    from rag import search, build_context
    
    # Check for simple greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "how far", "maakye", "maaha", "maadwo"]
    is_greeting = question.lower().strip().strip("?!.") in greetings
    
    # Step 1: Search (Wrapped in spinner in app.py)
    results = search(question, chunks, embeddings, top_n=RAG_TOP_N)
    context = build_context(results)
    
    if language == "Twi":
        lang_note = "Reply in simple Asante Twi. Write 'Ghana' as 'Gaana'. Keep sentences short."
        greeting_fallback = "Me ma wo akwaaba! Me yɛ Gaana Amanyɔ Mmara boafoɔ. Sɛ wo wɔ nsɛm bi fa Gaana amanyɔ mmara ho a, bisa me."
    else:
        lang_note = "Reply in simple, straightforward English without legal jargon."
        greeting_fallback = "Hello! I am your Constitutional Helper. How can I help you understand Ghana's 1992 Constitution today?"
    
    # If it's a greeting OR no results found, allow the AI to be conversational
    if is_greeting or not results:
        prompt = f"""You are Constitutional Helper, an expert ONLY on the 1992 Constitution of the Republic of GHANA.
        The user said: '{question}'. 
        {lang_note}
        
        STRICT RULES:
        1. NO HALLUCINATIONS: You are FORBIDDEN from using any knowledge about Ghana's laws or constitution that is not in the provided context. If the answer is not in the text, say: "I'm sorry, but the 1992 Constitution doesn't specifically cover this topic based on my current database."
        2. NO INTRODUCTIONS: Do not start with "Here is...", "Based on...", or "Hello".
        3. NO PLEASANTRIES: Do not end with "Hope this helps" or "Let me know if...".
        4. IDENTITY: You are a direct, authoritative Ghanaian legal guide.
        5. LANGUAGE: Respond warmly in {language} but stay professional.
        """

    else:
        prompt = f"""You are Constitutional Helper, a strict expert on the 1992 Constitution of the Republic of GHANA.
        
        Answer the question based ONLY on the constitutional articles provided below.
        
        {context}
        
        STRICT RULES:
        1. STRICT CONTEXT: Answer using ONLY the provided articles. If the articles do not contain the answer, state that the specific information is not available in the 1992 Constitution text provided.
        2. NO EXTERNAL DATA: Do not mention laws, cases, or articles that are not in the provided {context}.
        3. NO FILLER: Skip phrases like "According to the text provided..." or "I have found...".
        4. NO AI SLOP: Avoid "Certainly!", "I can help with that", or legalistic fluff.
        5. REFERENCES: You MUST include a 'REFERENCES:' section at the end with exact verbatim quotes.
        
        Question: {question}"""



    # Step 2: Stream LLM
    try:
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        yield "Error: Failed to stream response."


def get_res(question: str, language: str, client: Groq, chunks, embeddings,
            max_retries: int = MAX_RETRIES) -> Optional[str]:
    """
    Generate constitutional answer grounded in actual constitutional text using RAG.

    Args:
        question: User's constitutional question
        language: Response language ("English" or "Twi")
        client: Groq API client
        chunks: Constitutional article chunks
        embeddings: Pre-computed embeddings for semantic search
        max_retries: Number of retries on API failure

    Returns:
        Optional[str]: AI-generated answer with citations, or None if failed
    """
    from rag import search, build_context

    # Step 0: Check cache first (instant response for repeated questions)
    cached = get_cached_response(question, language)
    if cached:
        logger.info(f"Cache hit for question: {question[:50]}...")
        return cached

    # Step 1: Validate input
    is_valid, result = validate_question(question)
    if not is_valid:
        st.warning(f"Invalid question: {result}")
        logger.warning(f"Invalid question rejected: {result}")
        return None

    question = result  # Use cleaned question

    # Step 2: Retrieve relevant articles using semantic search
    logger.info(f"Searching for relevant articles: {question[:50]}")
    try:
        results = search(question, chunks, embeddings, top_n=RAG_TOP_N)
        context = build_context(results)
        logger.info(f"Found {len(results)} relevant articles")
    except Exception as e:
        logger.error(f"RAG search failed: {e}", exc_info=True)
        st.error("Failed to search constitutional database")
        return None
    
    # Step 3: Build language-specific LLM instructions
    if language == "Twi":
        lang_note = (
            "Reply in simple Asante Twi. Use phonetically readable Twi words where possible. "
            "Write 'Ghana' as 'Gaana' if it helps pronunciation. Keep sentences very short."
        )
    else:
        lang_note = "Reply in simple, straightforward English without legal jargon."
    
    # Step 4: Construct prompt with constitutional context
    prompt = f"""You are Constitutional Helper, an expert on Ghana's 1992 Constitution.

Based on the constitutional articles below, answer the user's question directly and simply for everyday citizens.

{context}

IMPORTANT: You MUST include a section at the end titled 'REFERENCES:' where you quote the exact, verbatim 
constitutional text that supports your answer. Make sure quotes are accurate to the 1992 Constitution of Ghana.

{lang_note}

Question: {question}"""
    
    # Step 5: Query LLM with retry logic
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM query attempt {attempt + 1}/{max_retries}")
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
            )
            
            answer = response.choices[0].message.content
            logger.info(f"LLM response received ({len(answer)} chars)")
            # Cache the response for future identical questions
            set_cached_response(question, language, answer)
            return answer
        
        except Exception as e:
            logger.error(f"LLM query failed (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                st.warning(f"Retrying... (attempt {attempt + 1}/{max_retries})")
            else:
                st.error(f"Failed to generate answer after {max_retries} attempts")
                return None
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGE RENDERING
# ─────────────────────────────────────────────────────────────────────────────
def render_message(role: str, content: str, idx: int = None) -> None:
    """
    Render a chat message with a professional, legal-brief inspired layout.
    """
    is_user = role == "user"
    user_icon = svg('user', 18, '#ffffff')
    ai_icon = svg('scale', 18, 'currentColor')
    
    if is_user:
        st.markdown(f"""
        <div class="msg-row user">
          <div class="avatar user">{user_icon}</div>
          <div class="bubble user" style="border-radius: 12px 12px 0 12px;">{escape(content)}</div>
        </div>""", unsafe_allow_html=True)
    else:
        formatted = format_reply(content)
        st.markdown(f"""
        <div style="margin-bottom: 32px; border-left: 4px solid var(--brand-500); padding-left: 24px; animation: fadeIn 0.5s ease-out;">
            <div style="font-size: 11px; font-weight: 800; color: var(--brand-600); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                {ai_icon} Constitutional Analysis
            </div>
            <div class="bubble ai" style="background: transparent; border: none; padding: 0; color: var(--text); font-size: 16px; line-height: 1.7;">
                {formatted}
            </div>
        </div>""", unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────────────────────
#  AUDIO GENERATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_audio(text: str, language: str) -> Optional[str]:
    """
    Generate audio file and return base64-encoded data URL.
    
    Args:
        text: Text to convert to speech
        language: "English" or "Twi"
    
    Returns:
        Optional[str]: Base64-encoded audio data URL, or None if failed
    """
    if not ENABLE_AUDIO:
        return None
    
    try:
        # Limit text length for audio
        text = text[:AUDIO_MAX_LENGTH]
        lang_code = TTS_LANGUAGE_MAP.get(language, "en-uk")
        
        logger.info(f"Generating audio ({lang_code}, {len(text)} chars)")
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        
        b64 = base64.b64encode(buf.read()).decode()
        logger.info("Audio generated successfully")
        return f'<audio autoplay controls><source src="data:audio/mp3;base64,{b64}"></audio>'
    
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE SETUP & CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
validate_startup()  # Validate before any Streamlit calls

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE
)

# Initialize API clients and RAG (Lazy initialization or cached)
client = initialize_groq_client()

# We load these lazily in the session state if they don't exist
if "chunks" not in st.session_state or "embeddings" not in st.session_state:
    with st.spinner("Waking up Constitutional Helper..."):
        chunks, embeddings = initialize_rag()
        st.session_state.chunks = chunks
        st.session_state.embeddings = embeddings
else:
    chunks = st.session_state.chunks
    embeddings = st.session_state.embeddings

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "speak_index" not in st.session_state:
    st.session_state.speak_index = None
if "language" not in st.session_state:
    st.session_state.language = DEFAULT_LANGUAGE


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD CSS THEME (From external file or inline)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def get_theme_css():
    """Load and cache theme CSS from external file with minimal fallback."""
    css_file = "styles.css"
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .msg-row { display:flex; gap:16px; margin-bottom:24px; }
        .bubble { padding:14px 18px; border-radius:16px; font-size:15px; }
        .bubble.ai { background:#F8FAFC; border:1px solid #E2E8F0; }
        .bubble.user { background:#2563eb; color:white; }
        :root {
            --success: #10B981;
            --brand-500: #3b82f6;
            --brand-600: #2563eb;
            --text: #0F172A;
        }


        .topic-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            text-align: left;
            transition: all 0.2s ease;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }

        .topic-card:hover {
            border-color: var(--brand-500);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
        }
        """

st.markdown(f"<style>{get_theme_css()}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TOP BANNER - Premium Glass Header
# ─────────────────────────────────────────────────────────────────────────────
# Language toggle logic
lang = st.session_state.get("language", DEFAULT_LANGUAGE)
twi_active = "active" if lang == "Twi" else ""
en_active = "active" if lang == "English" else ""



# ─────────────────────────────────────────────────────────────────────────────
#  TOP LANGUAGE SELECTOR (Always Visible)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    lang_options = ["English", "Twi"]
    current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    new_lang = st.segmented_control(
        "Choose Language / Pae mu kyerɛ kasa",
        options=lang_options,
        default=current_lang,
        key="lang_selector",
        label_visibility="collapsed"
    )
    if new_lang and new_lang != current_lang:
        st.session_state.language = new_lang
        st.rerun()

# Handle language selection via a hidden radio/button if needed, 
# but for now let's use standard Streamlit buttons for reliability 
# and just place them nicely.


# ─────────────────────────────────────────────────────────────────────────────
#  MINIMAL SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR (Dashboard Command Center)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 20px 0 40px; text-align: center;">
        <div style="width: 48px; height: 48px; background: var(--brand-600); border-radius: 12px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center; color: white;">
            {svg('landmark', 24, 'currentColor')}
        </div>
        <div style="font-weight: 800; font-size: 18px; color: white; letter-spacing: -0.02em;">GHANALEX</div>
        <div style="font-size: 12px; color: #64748B; margin-top: 4px;">v2.0.4 Production</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 20px; font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.1em;'>RESOURCES</div>", unsafe_allow_html=True)
    
    st.markdown(f"""<div style="margin-bottom: -40px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #94A3B8;">{svg('file-text', 14, 'currentColor')}</div>""", unsafe_allow_html=True)
    if st.button("      Documentation", use_container_width=True, key="sidebar_docs"):
        st.session_state.page = "docs"
        st.rerun()
        
    st.markdown(f"""<div style="margin-bottom: -40px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #94A3B8;">{svg('settings', 14, 'currentColor')}</div>""", unsafe_allow_html=True)
    if st.button("      How it Works", use_container_width=True, key="sidebar_overview"):
        st.markdown(f'<meta http-equiv="refresh" content="0; url=SYSTEM_OVERVIEW.html">', unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 12px; font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.1em;'>POPULAR TOPICS</div>", unsafe_allow_html=True)
    
    for label, question in QUICK_TOPICS.items():
        if st.button(label, use_container_width=True, key=f"topic_{label}", type="secondary"):
            st.session_state.pending_question = question
            st.rerun()

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="margin-bottom: -45px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #94A3B8;">{svg('trash', 16, 'currentColor')}</div>""", unsafe_allow_html=True)
    if st.button("      Clear Chat", use_container_width=True, key="btn_clear", type="secondary"):
        st.session_state.messages = []
        st.rerun()



# ─────────────────────────────────────────────────────────────────────────────
#  PREMIUM HERO SECTION (Welcome Screen with Popular Questions)
# ─────────────────────────────────────────────────────────────────────────────
if len(st.session_state.messages) == 0:
    st.markdown(f"""
    <div style="padding: 40px 0 20px; text-align: center;">
      <div style="display: inline-flex; align-items: center; gap: 10px; padding: 8px 16px; 
                  background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); 
                  border-radius: 100px; color: var(--brand-600); font-size: 13px; font-weight: 600; 
                  margin-bottom: 24px; animation: fadeIn 0.8s ease-out;">
        {svg('shield', 14, 'currentColor')} 1992 Constitution of Ghana
      </div>
      <h1 style="font-size: 42px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; 
                 background: linear-gradient(135deg, #0F172A 0%, #3B82F6 100%); 
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        The Constitution,<br/>Simplified.
      </h1>
      <p style="font-size: 16px; color: var(--text-2); max-width: 520px; margin: 0 auto 32px; line-height: 1.6;">
        Ask anything about our supreme law or choose a popular topic below to get started.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size: 11px; font-weight: 700; color: var(--text-3); text-transform: uppercase; 
                letter-spacing: 0.1em; margin-bottom: 16px; text-align: center;">
        POPULAR INQUIRIES
    </div>
    """, unsafe_allow_html=True)

    # Icon mapping for topics
    topic_icons = {
        "Police & Arrests": "shield",
        "Fundamental Rights": "landmark",
        "Presidential Rules": "crown",
        "Making Laws": "file-text",
        "Land & Property": "map-pin",
        "Voting Rights": "vote",
        "Amending the Law": "settings"
    }

    # Render popular questions as high-end Bento Cards
    topics = list(QUICK_TOPICS.items())
    
    # 2x4 Grid logic using columns
    for i in range(0, len(topics), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(topics):
                label, question = topics[i + j]
                icon_name = topic_icons.get(label, "scale")
                
                with cols[j]:
                    # The Interaction Wrapper
                    st.markdown('<div class="topic-card-wrapper">', unsafe_allow_html=True)
                    
                    # 1. The Visual Card
                    st.markdown(f"""
                    <div class="topic-card">
                        <div class="icon-wrapper">
                            {svg(icon_name, 22, 'currentColor')}
                        </div>
                        <div class="label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 2. The Invisible Interaction Layer
                    st.markdown('<div class="overlay-btn">', unsafe_allow_html=True)
                    if st.button(f"Select {label}", key=f"topic_btn_{i+j}"):
                        st.session_state.pending_question = question
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True) # close overlay-btn
                    
                    st.markdown('</div>', unsafe_allow_html=True) # close topic-card-wrapper


    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)






# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY CHAT HISTORY
# ─────────────────────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    render_message(msg["role"], msg["content"], idx=i)
    
    if msg["role"] == "assistant":
        st.markdown(f"""<div style="margin-bottom: -45px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: var(--brand-500);">{svg('volume', 16, 'currentColor')}</div>""", unsafe_allow_html=True)
        if st.button("      Hear Reference", key=f"spk_{i}"):
            st.session_state.speak_index = i
    
    if msg["role"] == "assistant" and st.session_state.speak_index == i:
        audio_html = generate_audio(msg["content"], st.session_state.language)
        if audio_html:
            st.markdown(audio_html, unsafe_allow_html=True)
        else:
            st.warning("Could not generate audio")
        st.session_state.speak_index = None


# ─────────────────────────────────────────────────────────────────────────────
#  HANDLE SIDEBAR TOPIC CLICK
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.pending_question:
    question = st.session_state.pending_question
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    st.session_state.pending_question = None
    
    st.session_state.messages.append({"role": "user", "content": question})
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN CHAT INPUT
# ─────────────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question about the constitution...", key="chat_input")

if user_input:
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    is_valid, result = validate_question(user_input)
    if is_valid:
        st.session_state.messages.append({"role": "user", "content": result})
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PROCESS LAST MESSAGE IF USER
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_query = st.session_state.messages[-1]["content"]
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    
    # Render the assistant avatar and start the bubble
    ai_icon = svg('scale', 18, '#3b82f6')
    st.markdown(f"""
    <div class="msg-row">
      <div class="avatar ai">{ai_icon}</div>
      <div class="bubble ai" id="streaming-bubble">
    """, unsafe_allow_html=True)
    
    with st.spinner("Thinking..."):
        response_generator = stream_res(last_query, language, client, chunks, embeddings)
        full_response = st.write_stream(response_generator)
    
    # Close the bubble div
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()
