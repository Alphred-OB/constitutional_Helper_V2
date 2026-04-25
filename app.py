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
import asyncio
import edge_tts
from groq import Groq
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
    import time
    
    t0 = time.time()
    
    # Check for simple greetings
    greetings = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", 
        "how far", "maakye", "maaha", "maadwo", "eti s3n", "ete sen", "enti s3n", "enti sen",
        "wo ho te sen", "akwaaba", "yo", "sup"
    ]
    is_greeting = any(g in question.lower().strip() for g in greetings)

    
    # Step 1: Search (Wrapped in spinner in app.py)
    results = search(question, chunks, embeddings, top_n=RAG_TOP_N)
    t1 = time.time()
    logger.info(f"Search completed in {t1-t0:.3f}s")
    
    context = build_context(results)
    
    # Logic: If it's a greeting OR results are empty OR results have very low scores (noise)
    top_score = results[0]["score"] if results else 0
    
    if language == "Twi":
        lang_note = "Reply in simple Asante Twi. Write 'Ghana' as 'Gaana'. Keep sentences short."
        greeting_fallback = "Me ma wo akwaaba! Me yɛ Gaana Amanyɔ Mmara boafoɔ. Sɛ wo wɔ nsɛm bi fa Gaana amanyɔ mmara ho a, bisa me."
    else:
        lang_note = "Reply in simple, straightforward English without legal jargon."
        greeting_fallback = "Hello! I am your Constitutional Helper. How can I help you understand Ghana's 1992 Constitution today?"
    
    # If it's a greeting OR no results found OR very low relevance (noise)
    if is_greeting or not results or top_score < 0.32:
        prompt = f"""You are Constitutional Helper, a friendly expert on the 1992 Constitution of the Republic of GHANA.
        The user said: '{question}'. 
        
        INSTRUCTIONS:
        - If the user is just saying hello or greeting you, greet them back warmly (using {language}) and ask how you can help them with the Constitution today.
        - If the user asked a non-constitutional question, politely explain that you can only answer questions related to the 1992 Constitution of Ghana, and that their query doesn't match your database.
        
        IDENTITY: You are helpful, polite, and welcoming. Do not be overly strict or robotic about pleasantries.
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
            temperature=0.5,
            stream=True,
        )
        t2 = time.time()
        logger.info(f"LLM stream initialized in {t2-t1:.3f}s")
        
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
            "Reply in natural Asante Twi. Be concise and conversational. "
            "Do not repeat words or phrases excessively. "
            "Write in standard Twi spelling."
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
    Render a chat message with Tailwind utility classes.
    """
    is_user = role == "user"
    user_icon = svg('user', 18, '#ffffff')
    ai_icon = svg('scale', 18, '#000000')
    
    if is_user:
        st.markdown(f"""
        <div class="flex justify-end mb-8 animate-in fade-in slide-in-from-right duration-500">
            <div class="max-w-[80%] bg-slate-100 border border-slate-200 p-5 rounded-2xl rounded-tr-none shadow-sm">
                <div class="text-slate-900 text-[15px] leading-relaxed">{escape(content)}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        formatted = format_reply(content)
        st.markdown(f"""
        <div class="mb-10 pl-6 border-l-4 border-black animate-in fade-in slide-in-from-left duration-500">
            <div class="flex items-center gap-2 mb-4 text-[11px] font-bold text-black uppercase tracking-widest">
                {ai_icon} Constitutional Analysis
            </div>
            <div class="text-slate-900 text-base leading-loose">
                {formatted}
            </div>
        </div>""", unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────────────────────
#  AUDIO GENERATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_audio(text: str, language: str) -> Optional[str]:
    """
    Generate audio file using edge-tts and return base64-encoded data URL.
    """
    if not ENABLE_AUDIO:
        return None
    
    # Nested async function to handle edge-tts
    async def _async_generate():
        # Limit text length for audio (Edge handles ~20k, but 5k is safe)
        clean_text = text[:AUDIO_MAX_LENGTH]
        
        # PHONETIC HACK: If language is Twi, replace special characters 
        # so the neural voice can pronounce them naturally.
        if language == "Twi":
            clean_text = clean_text.replace("ɛ", "e").replace("Ɛ", "E")
            clean_text = clean_text.replace("ɔ", "o").replace("Ɔ", "O")
            # Remove parentheses content for cleaner audio
            import re
            clean_text = re.sub(r'\(.*?\)', '', clean_text)
            
        voice = TTS_VOICE_MAP.get(language, "en-NG-AbeoNeural")
        
        logger.info(f"Generating neural audio ({voice}, {len(clean_text)} chars)")
        
        communicate = edge_tts.Communicate(clean_text, voice)
        
        # Use a temporary buffer
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        if not audio_data:
            return None
            
        b64 = base64.b64encode(audio_data).decode()
        logger.info("Neural audio generated successfully")
        # Return HTML audio tag with base64 data
        return f'<audio autoplay controls style="width: 100%; border-radius: 8px; margin-top: 10px;"><source src="data:audio/mp3;base64,{b64}"></audio>'

    try:
        # Run the async generator in the current thread
        return asyncio.run(_async_generate())
    except Exception as e:
        logger.error(f"Neural audio generation failed: {e}")
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

# Inject Tailwind CSS CDN
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

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
# Main App Entry (Welcome screen or Chat)
if len(st.session_state.messages) == 0:
    pass # Will render below


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
    <div style="padding: 20px 0 32px; text-align: left; padding-left: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; background: var(--brand-600); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);">
                {svg('landmark', 20, 'currentColor')}
            </div>
            <div>
                <div style="font-weight: 800; font-size: 16px; color: #0F172A; letter-spacing: -0.01em; line-height: 1.2;">GhanaLex</div>
                <div style="font-size: 11px; color: #64748B; font-weight: 500;">Constitutional AI</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Language Selector in Sidebar
    st.markdown("<div style='margin-bottom: 8px; font-size: 11px; font-weight: 700; color: #000000; letter-spacing: 0.1em; padding-left: 4px;'>LANGUAGE</div>", unsafe_allow_html=True)
    lang_options = ["English", "Twi"]
    current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    new_lang = st.segmented_control(
        "lang",
        options=lang_options,
        default=current_lang,
        key="sidebar_lang",
        label_visibility="collapsed"
    )
    if new_lang and new_lang != current_lang:
        st.session_state.language = new_lang
        st.rerun()

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 12px; font-size: 11px; font-weight: 700; color: #000000; letter-spacing: 0.1em; padding-left: 4px;'>EXPLORE</div>", unsafe_allow_html=True)
    
    # Navigation Links
    st.markdown(f"""<div style="margin-bottom: -35px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #000000;">{svg('file-text', 14, '#000000')}</div>""", unsafe_allow_html=True)
    if st.button("      Documentation", use_container_width=True, key="sidebar_docs"):
        st.session_state.page = "docs"
        st.rerun()
        
    st.markdown(f"""<div style="margin-bottom: -35px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #000000;">{svg('help-circle', 14, '#000000')}</div>""", unsafe_allow_html=True)
    if st.button("      How it Works", use_container_width=True, key="sidebar_overview"):
        st.markdown(f'<meta http-equiv="refresh" content="0; url=SYSTEM_OVERVIEW.html">', unsafe_allow_html=True)

    # Download Section
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 12px; font-size: 11px; font-weight: 700; color: #000000; letter-spacing: 0.1em; padding-left: 4px;'>DOWNLOAD</div>", unsafe_allow_html=True)
    
    import config
    pdf_file_path = os.path.join(os.path.dirname(__file__), config.PDF_PATH)
    
    if os.path.exists(pdf_file_path):
        with open(pdf_file_path, "rb") as f:
            pdf_bytes = f.read()

        
        st.markdown(f"""<div style="margin-bottom: -35px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #000000;">{svg('download', 14, '#000000')}</div>""", unsafe_allow_html=True)
        st.download_button(
            label="      Download Constitution",
            data=pdf_bytes,
            file_name="1992_Constitution_of_Ghana.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="sidebar_download_v3"
        )


    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 12px; font-size: 11px; font-weight: 700; color: #000000; letter-spacing: 0.1em; padding-left: 4px;'>QUICK TOPICS</div>", unsafe_allow_html=True)
    
    for label, question in QUICK_TOPICS.items():
        if st.button(label, use_container_width=True, key=f"topic_{label}", type="secondary"):
            st.session_state.pending_question = question
            st.rerun()

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="margin-bottom: -35px; margin-left: 12px; position: relative; z-index: 10; pointer-events: none; color: #000000;">{svg('trash', 14, 'currentColor')}</div>""", unsafe_allow_html=True)
    if st.button("      Clear Conversation", use_container_width=True, key="btn_clear", type="secondary"):
        st.session_state.messages = []
        st.rerun()





# ─────────────────────────────────────────────────────────────────────────────
#  PREMIUM HERO SECTION (Welcome Screen with Popular Questions)
# ─────────────────────────────────────────────────────────────────────────────
if len(st.session_state.messages) == 0:
    st.markdown(f"""
    <div class="max-w-2xl mx-auto py-16 text-center">
        <div class="inline-flex items-center gap-2 px-4 py-2 bg-slate-50 border border-slate-200 rounded-full text-slate-600 text-xs font-bold mb-6 tracking-wide">
            {svg('shield', 14, '#475569')} 1992 CONSTITUTION OF GHANA
        </div>
        <h1 class="text-5xl font-black text-slate-900 leading-[1.1] mb-6 tracking-tight">
            The Constitution,<br/><span class="text-slate-400">Simplified.</span>
        </h1>
        <p class="text-lg text-slate-500 max-w-lg mx-auto mb-10 leading-relaxed font-medium">
            Understand your rights and the laws of Ghana with our AI-powered assistant.
        </p>
    </div>
    """, unsafe_allow_html=True)



    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)






# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY CHAT HISTORY
# ─────────────────────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    render_message(msg["role"], msg["content"], idx=i)
    
    if msg["role"] == "assistant":
        # Simple, professional text button
        c1, _ = st.columns([1, 4])
        with c1:
            if st.button("Listen", key=f"spk_{i}", help="Hear this constitutional reference", type="secondary"):
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
    
    # We use a placeholder to stream into our custom HTML bubble
    placeholder = st.empty()
    full_response = ""
    ai_icon = svg('scale', 18, '#3b82f6')
    
    for chunk in stream_res(last_query, language, client, chunks, embeddings):
        full_response += chunk
        # Re-render the whole bubble with the current progress
        # We process the text to handle the references section and basic formatting
        formatted = format_reply(full_response)
        
        placeholder.markdown(f"""
        <div class="msg-row">
          <div class="avatar ai">{ai_icon}</div>
          <div class="bubble ai">
            <div class="legal-header">
                {svg('scale', 14, 'currentColor')} CONSTITUTIONAL ANALYSIS
            </div>
            <div style="color: var(--text); font-size: 16px; line-height: 1.7;">
                {formatted}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Final cleanup if needed (placeholder already has the full response)

    
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()
