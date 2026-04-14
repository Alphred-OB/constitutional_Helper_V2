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
from typing import Optional, Tuple
from html import escape

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
    
    Args:
        text: Text possibly containing article references
    
    Returns:
        str: Text with HTML-formatted article badges
    """
    book_svg = svg('book', 14, THEME["BRAND_700"])
    return re.sub(
        r'\[Article\s*(\d+\w*)\]',
        f'<span class="artbadge">{book_svg} Art.\\1</span>',
        text,
        flags=re.IGNORECASE
    )


def format_reply(text: str) -> str:
    """
    Format LLM response with HTML markup, citations, and styling.
    
    Args:
        text: Raw LLM response
    
    Returns:
        str: Formatted HTML ready for Streamlit display
    """
    # Escape HTML first
    text = escape_and_format_html(text)
    
    # Highlight articles
    text = highlight_articles(text)
    
    # Parse into structured HTML
    lines = text.split('\n')
    out, in_list, in_refs = [], False, False
    check_svg = svg('check', 14, THEME["BRAND_500"])
    
    for line in lines:
        s = line.strip()
        
        if 'REFERENCES:' in s:
            if in_list:
                out.append('</div>')
                in_list = False
            
            out.append(
                f'<div style="margin-top:16px;padding:12px 16px;'
                f'background:{THEME["SURFACE2"]};border-left:4px solid {THEME["BRAND_500"]};'
                f'border-radius:0 8px 8px 0;font-size:14px;color:{THEME["TEXT2"]}">'
                f'<div style="margin-bottom:8px;display:flex;align-items:center;gap:6px;">'
                f'<strong style="color:{THEME["TEXT"]}">{svg("book", 16, THEME["BRAND_600"])} '
                f'REFERENCES</strong></div>'
            )
            in_refs = True
            continue
        
        if s.startswith('- ') or s.startswith('• ') or s.startswith('* '):
            if not in_list:
                out.append('<div class="checklist">')
                in_list = True
            out.append(f'<div class="checkitem"><div class="checkdot">{check_svg}</div>'
                      f'<span>{s[2:]}</span></div>')
        else:
            if in_list:
                out.append('</div>')
                in_list = False
            if s:
                if s.startswith('&gt;'):
                    s = s[4:].strip()
                out.append(f'<p style="margin-bottom:8px">{s}</p>')
    
    if in_list:
        out.append('</div>')
    if in_refs:
        out.append('</div>')
    
    return ''.join(out)


# ─────────────────────────────────────────────────────────────────────────────
#  RAG-POWERED LLM QUERY
# ─────────────────────────────────────────────────────────────────────────────
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
#  CONSTITUTION DOWNLOAD
# ─────────────────────────────────────────────────────────────────────────────
def generate_constitution_file(chunks: list) -> str:
    """
    Generate constitution content from chunks for download (on-demand only).
    
    Args:
        chunks: List of constitution chunks
    
    Returns:
        str: Markdown-formatted constitution text
    """
    content = []
    content.append("# GHANA'S 1992 CONSTITUTION\n")
    content.append("*Compiled from constitutional articles and provisions*\n")
    content.append("---\n\n")
    
    current_chapter = None
    for chunk in chunks:
        chapter = chunk.get("chapter", "")
        article = chunk.get("article", "")
        text = chunk.get("text", "")
        
        if chapter and chapter != current_chapter:
            content.append(f"\n## {chapter}\n\n")
            current_chapter = chapter
        
        if article:
            content.append(f"### {article}\n\n")
        
        content.append(f"{text}\n\n")
        content.append("---\n\n")
    
    return "\n".join(content)


# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGE RENDERING
# ─────────────────────────────────────────────────────────────────────────────
def render_message(role: str, content: str, idx: int = None) -> None:
    """
    Render a chat message with proper styling and icons.
    
    Args:
        role: "user" or "assistant"
        content: Message content (text)
        idx: Message index for tracking
    """
    is_user = role == "user"
    user_icon = svg('user', 20, '#ffffff')
    ai_icon = svg('scale', 20, THEME["BRAND_500"])
    
    if is_user:
        st.markdown(f"""
        <div class="msgrow user">
          <div class="avatar user">{user_icon}</div>
          <div class="bubble user">{escape(content)}</div>
        </div>""", unsafe_allow_html=True)
    else:
        formatted = format_reply(content)
        verified_svg = svg('check', 16, THEME["TEXT2"])
        st.markdown(f"""
        <div class="msgrow">
          <div class="avatar ai">{ai_icon}</div>
          <div style="flex-grow: 1;">
            <div class="bubble ai">
              {formatted}
              <div class="msgref">
                {verified_svg} Generated from Ghana's 1992 Constitution
              </div>
            </div>
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

# Initialize API clients and RAG
client = initialize_groq_client()
chunks, embeddings = initialize_rag()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "speak_index" not in st.session_state:
    st.session_state.speak_index = None
if "language" not in st.session_state:
    st.session_state.language = DEFAULT_LANGUAGE
if "chunks" not in st.session_state:
    st.session_state.chunks = chunks
if "embeddings" not in st.session_state:
    st.session_state.embeddings = embeddings


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD CSS THEME (From external file or inline)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def get_theme_css():
    """Load and cache theme CSS."""
    css_file = "styles.css"
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            return f.read()
    else:
        # Fallback inline CSS
        return f"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: {THEME['BG']} !important;
    font-family: 'Inter', sans-serif;
    color: {THEME['TEXT']};
}}

.msgrow {{ display:flex;gap:16px;align-items:flex-start;margin-bottom:24px;animation:fadeup 0.4s ease-out; }}
.msgrow.user {{ flex-direction:row-reverse; }}
@keyframes fadeup {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}

.avatar {{
    width:40px;height:40px;border-radius:12px;
    display:flex;align-items:center;justify-content:center;
    flex-shrink:0;margin-top:2px;
}}
.avatar.ai {{ background:{THEME['SURFACE2']}; border: 1px solid {THEME['BORDER']}; }}
.avatar.user {{ background:{THEME['BRAND_600']}; color: white; }}

.bubble {{
    max-width:calc(100% - 60px);
    padding:16px 20px;font-size:15px;line-height:1.6;
}}
.bubble.ai {{
    background:{THEME['SURFACE']};color:{THEME['TEXT']};
    border:1px solid {THEME['BORDER']};
    border-radius:4px 16px 16px 16px;
}}
.bubble.user {{
    background:{THEME['BRAND_600']};color:#ffffff;
    border-radius:16px 4px 16px 16px;
}}

.artbadge {{
    display:inline-flex;align-items:center;gap:6px;
    background:{THEME['BRAND_50']}; border:1px solid {THEME['BRAND_200']};
    color:{THEME['BRAND_700']};font-size:12px;font-weight:600;
    padding:4px 10px;border-radius:6px;margin:2px 4px;
}}

.checklist {{ margin:12px 0;display:flex;flex-direction:column;gap:12px; }}
.checkitem {{ display:flex;gap:12px;align-items:flex-start;color:{THEME['TEXT']}; }}
.checkdot {{
    width:20px;height:20px;border-radius:50%;
    background:{THEME['SURFACE2']}; border:1.5px solid {THEME['BRAND_500']};
    display:flex;align-items:center;justify-content:center;
    flex-shrink:0;color:{THEME['BRAND_500']};
}}
"""

st.markdown(f"<style>{get_theme_css()}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TOP BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="border-bottom: 1px solid {THEME['BORDER']}; padding:24px 0; margin-bottom:24px;">
  <div style="display:flex;align-items:center;gap:16px;">
    <div style="width:48px;height:48px;background:{THEME['BRAND_500']};border-radius:12px;
                display:flex;align-items:center;justify-content:center;color:white;">
      {svg('scale', 24, '#ffffff')}
    </div>
    <div>
      <div style="font-size:24px;font-weight:700;color:{THEME['TEXT']};letter-spacing:-0.02em;">
        Constitutional Helper
      </div>
      <div style="font-size:13px;color:{THEME['TEXT2']};margin-top:4px;font-weight:500;">
        Powered by Ghana's 1992 Constitution with AI
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Constitutional Helper")
    st.caption("Ghana 1992 Constitution AI")
    st.divider()
    
    # Language selector
    st.markdown(f"<p style='font-size:13px;color:{THEME['TEXT2']};margin:16px 0 8px;font-weight:500'>"
                "Response Language</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("English", use_container_width=True, key="btn_en"):
            st.session_state.language = "English"
            st.rerun()
    with col2:
        if st.button("Twi", use_container_width=True, key="btn_tw"):
            st.session_state.language = "Twi"
            st.rerun()
    
    lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    st.markdown(f"<p style='font-size:12px;color:{THEME['BRAND_600']};margin-top:4px'>"
                f"Active: {lang}</p>", unsafe_allow_html=True)
    st.divider()
    
    # Download button
    st.markdown("**Downloads**")
    try:
        # Try to load from PDF first
        if os.path.exists(PDF_PATH):
            with open(PDF_PATH, "rb") as file:
                pdf_data = file.read()
            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name="Ghana_1992_Constitution.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            # Generate from chunks if PDF not available
            constitution_text = generate_constitution_file(st.session_state.get("chunks", []))
            st.download_button(
                label="📄 Download Constitution (Markdown)",
                data=constitution_text,
                file_name="Ghana_1992_Constitution.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.caption("Generated from constitutional articles", help="Compiled from 675 constitution chunks")
    except Exception as e:
        logger.error(f"Download error: {e}")
        st.warning("Download unavailable")
    
    st.divider()
    
    # Quick topics
    st.markdown("**Quick Topics**")
    for label, question in QUICK_TOPICS.items():
        if st.button(label, use_container_width=True, key=f"t_{label}"):
            st.session_state.pending_question = question
    
    st.divider()
    if st.button("Clear Chat", use_container_width=True, key="btn_clear"):
        st.session_state.messages = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  WELCOME CARD
# ─────────────────────────────────────────────────────────────────────────────
if len(st.session_state.messages) == 0:
    st.markdown(f"""
    <div style="background:{THEME['SURFACE']};border:1px solid {THEME['BORDER']};
                border-radius:16px;padding:40px 32px;text-align:center;margin-bottom:32px;">
      <div style="width:64px;height:64px;margin:0 auto 20px;background:{THEME['BRAND_50']};
                  border:1px solid {THEME['BRAND_100']};border-radius:16px;
                  display:flex;align-items:center;justify-content:center;color:{THEME['BRAND_600']};">
        {svg('library', 32, THEME['BRAND_600'])}
      </div>
      <h2 style="font-size:24px;font-weight:700;color:{THEME['TEXT']};margin-bottom:12px;">
        Welcome to Constitutional Helper
      </h2>
      <p style="font-size:15px;color:{THEME['TEXT2']};line-height:1.6;">
        Your AI guide powered by Ghana's 1992 Constitution. Ask any legal question to receive
        an accurate, cited response in English or Twi.
      </p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY CHAT HISTORY
# ─────────────────────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    render_message(msg["role"], msg["content"], idx=i)
    
    if msg["role"] == "assistant":
        if st.button("Hear Reference", key=f"spk_{i}"):
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
    
    with st.spinner("Searching constitution..."):
        answer = get_res(question, language, client, chunks, embeddings)
    
    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})
        logger.info(f"Answer generated for topic question")
    else:
        st.error("Failed to generate answer")
    
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN CHAT INPUT
# ─────────────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question about the constitution...", key="chat_input")

if user_input:
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    
    # Validate input
    is_valid, result = validate_question(user_input)
    if not is_valid:
        st.warning(f"Invalid input: {result}")
    else:
        question = result
        st.session_state.messages.append({"role": "user", "content": question})
        
        with st.spinner("Thinking..."):
            answer = get_res(question, language, client, chunks, embeddings)
        
        if answer:
            st.session_state.messages.append({"role": "assistant", "content": answer})
            logger.info(f"Answered user question")
        else:
            st.error("Failed to generate answer. Please try again.")
        
        st.rerun()
