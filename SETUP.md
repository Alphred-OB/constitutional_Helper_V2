# Constitutional Helper - Setup Guide

Complete installation and deployment guide for the Ghana Constitutional Q&A Assistant.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Development vs Production](#development-vs-production)
7. [Deployment](#deployment)

---

## System Requirements

### Hardware
- **CPU**: 2+ cores (Intel/AMD x86-64 or Apple Silicon)
- **RAM**: 8GB minimum (16GB recommended for smooth operation)
- **Storage**: 5GB free space (for model downloads and cache)
- **Internet**: Required for initial setup and API calls

### Software
- **Python**: 3.9+ (tested on 3.10, 3.11, 3.12)
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Package Manager**: pip (included with Python)

### API Requirements
- **Groq API Key**: Required for LLM inference (free tier available)
  - Sign up at: https://console.groq.com
  - Get API key from: https://console.groq.com/keys
  - Note: API key must be set in `.env` file before running

---

## Installation

### Step 1: Clone or Extract Project

```bash
# If using git:
git clone https://github.com/yourusername/constitutional-helper.git
cd constitutional-helper

# Or extract from zip file and navigate to directory
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import streamlit, groq, sentence_transformers; print('✓ All packages installed')"
```

Expected output: `✓ All packages installed`

### Step 4: Download Constitution Data

The app requires Ghana's 1992 Constitution in JSON format:

```bash
# Check if constitution_chunks.json exists
ls constitution_chunks.json

# If missing, download from:
# https://github.com/yourrepo/ghanalex/raw/main/constitution_chunks.json
# Or create it by running the preprocessing script:
python -c "from rag import load_chunks; print(load_chunks())" 2>&1 | head -20
```

### Step 5: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Windows (PowerShell):
echo "GROQ_API_KEY=your_api_key_here" > .env

# macOS/Linux (Bash):
echo "GROQ_API_KEY=your_api_key_here" > .env
```

**To get your Groq API Key:**
1. Go to https://console.groq.com/keys
2. Create a new API key
3. Copy the key (looks like: `gsk_...`)
4. Paste into `.env` file

⚠️ **IMPORTANT**: Never commit `.env` file to git. It's in `.gitignore` for security.

---

## Configuration

### Application Settings

All configuration is centralized in `config.py`:

```python
# LLM Settings
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq's fastest inference
LLM_MAX_TOKENS = 600                    # Max response length
LLM_TEMPERATURE = 0.2                   # Low for factual answers

# RAG Settings (Semantic Search)
RAG_TOP_N = 5                           # Retrieve 5 relevant articles
RAG_SIMILARITY_THRESHOLD = 0.15         # Min relevance score
EMBEDDING_MODEL = "all-MiniLM-L6-v2"    # Fast, accurate embeddings

# File Settings
PDF_PATH = "constitution.pdf"           # Source PDF (if available)
CHUNKS_PATH = "constitution_chunks.json" # Preprocessed chunks
EMBEDDINGS_PATH = "constitution_embeddings.pkl"  # Cached vectors
```

To customize:
1. Edit `config.py`
2. Restart the app: `streamlit run app.py`
3. Changes take effect immediately

### Streamlit Configuration

Create `~/.streamlit/config.toml` for advanced settings:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#f5f5f5"
secondaryBackgroundColor = "#ffffff"
textColor = "#262730"

[client]
showErrorDetails = false

[logger]
level = "info"

[server]
maxUploadSize = 50
```

---

## Verification

### Quick Startup Test

```bash
# Start the app
streamlit run app.py

# Expected console output:
# 2024-01-15 10:30:45 INFO - Startup validation passed ✓
# 2024-01-15 10:30:45 INFO - RAG components initialized
# 2024-01-15 10:30:46 INFO - Groq client ready
# Streamlit running at: http://localhost:8501
```

### Manual API Test

```bash
# Test Groq API connection
python -c "
from config import *
from groq import Groq

client = Groq(api_key='YOUR_KEY')
response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[{'role': 'user', 'content': 'Hello'}],
    max_tokens=10
)
print('✓ API working:', response.choices[0].message.content[:50])
"
```

### Test RAG System

```bash
# Test semantic search
python -c "
from rag import load_chunks, load_or_build_embeddings, search

chunks = load_chunks()
embeddings = load_or_build_embeddings(chunks)
results = search('What are my rights?', chunks, embeddings, top_n=3)

print(f'✓ Found {len(results)} relevant articles')
for r in results:
    print(f'  - {r[\"article\"]}: {r[\"score\"]:.3f} relevance')
"
```

### Run Unit Tests

```bash
# Run all tests
pytest test_constitutional_helper.py -v

# Expected output:
# test_constitutional_helper.py::TestValidateQuestion::test_empty_question PASSED
# test_constitutional_helper.py::TestHTMLSecurity::test_script_tags_escaped PASSED
# ... (30+ tests)
# ===== 30 passed in 2.34s =====
```

---

## Troubleshooting

### Issue: "GROQ_API_KEY not found"

**Symptom**: App crashes on startup with `KeyError: 'GROQ_API_KEY'`

**Solution**:
```bash
# Verify .env file exists
cat .env  # macOS/Linux
type .env  # Windows

# Should output: GROQ_API_KEY=gsk_...

# If missing, create it:
echo "GROQ_API_KEY=your_key" > .env

# Restart app:
streamlit run app.py
```

### Issue: "ModuleNotFoundError: No module named 'sentence_transformers'"

**Symptom**: ImportError when starting app

**Solution**:
```bash
# Reinstall packages
pip install -r requirements.txt

# Or specific package:
pip install sentence-transformers

# Verify:
python -c "import sentence_transformers; print('✓ Installed')"
```

### Issue: "constitution_chunks.json not found"

**Symptom**: App crashes with `FileNotFoundError` during RAG initialization

**Solution**:
```bash
# Check file exists
ls constitution_chunks.json

# If missing, download it:
# https://github.com/yourrepo/constitutional-helper/raw/main/constitution_chunks.json

# Or verify it's in the right location:
pwd  # Print working directory
ls -la  # List all files (should include constitution_chunks.json)
```

### Issue: "Connection timeout when calling Groq API"

**Symptom**: Queries timeout or return 500 error

**Causes**:
- Internet connection down
- API key invalid or expired
- Groq API temporarily unavailable
- Network firewall blocking requests

**Solution**:
```bash
# 1. Check internet connection
ping 8.8.8.8

# 2. Verify API key in console.groq.com is still active
# (Regenerate if needed)

# 3. Check network firewall (corporate proxy?)
curl -X GET https://api.groq.com/health

# 4. Restart app:
streamlit run app.py

# 5. Try again after a few minutes
```

### Issue: "Embeddings cache corrupted"

**Symptom**: App crashes with pickle error, or semantic search returns garbage results

**Solution**:
```bash
# Delete corrupted cache
rm constitution_embeddings.pkl

# App will rebuild cache on next startup (takes 1-2 minutes)
streamlit run app.py

# Monitor logs for:
# INFO - Building semantic embeddings from scratch...
# INFO - Embeddings built and cached. Shape: (300, 384)
```

### Issue: "App runs slowly (10+ second responses)"

**Causes**:
- First query after startup (embeddings still loading)
- Network latency to Groq API
- Weak CPU
- Too many concurrent users

**Solution**:
```bash
# 1. Restart app and wait for initialization (2-3 minutes)
streamlit run app.py

# 2. Pre-warm the embeddings:
python -c "from rag import load_chunks, load_or_build_embeddings; chunks = load_chunks(); load_or_build_embeddings(chunks)"

# 3. Monitor logs:
# DEBUG - Encoded query time: 12ms
# DEBUG - Similarity search time: 140ms
# DEBUG - LLM inference time: 3200ms

# 4. If LLM slow, check Groq service status
```

---

## Development vs Production

### Development Setup

```bash
# Use virtual environment with all dependencies
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run with hot reload (changes take effect immediately)
streamlit run app.py

# Check logs (verbose mode)
streamlit run app.py --logger.level=debug

# Open browser to: http://localhost:8501
```

**Development Features**:
- Debug logging enabled
- Detailed error messages
- Hot reload on code changes
- No caching in Streamlit

### Production Setup

```bash
# Install production dependencies only
pip install -r requirements.txt

# Set environment for production
export STREAMLIT_LOGGER_LEVEL=info
export GROQ_API_KEY=your_production_key

# Run with production settings
streamlit run app.py \
  --server.port=8501 \
  --server.headless=true \
  --logger.level=warning
```

**Production Checklist**:
- [ ] API key set in environment (not in code)
- [ ] SSL certificate configured (if behind reverse proxy)
- [ ] API key rotation scheduled
- [ ] Logging enabled and monitored
- [ ] Rate limiting implemented (if needed)
- [ ] Database backups scheduled (if applicable)
- [ ] Security audit completed
- [ ] Performance tested under load

---

## Deployment

### Local Machine

```bash
# 1. Clone and setup
git clone https://github.com/yourrepo/constitutional-helper.git
cd constitutional-helper

# 2. Create environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add .env file
echo "GROQ_API_KEY=your_key" > .env

# 5. Run
streamlit run app.py

# 6. Open browser
# Navigate to http://localhost:8501
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Don't store API key in image!
# Use environment variable at runtime

CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t constitutional-helper .
docker run -p 8501:8501 -e GROQ_API_KEY=$GROQ_API_KEY constitutional-helper
```

### Streamlit Cloud

1. Push code to GitHub (excluding `.env`)
2. Go to https://streamlit.io/cloud
3. Click "New app"
4. Select GitHub repo and `app.py`
5. Click "Deploy"
6. Add secrets in Streamlit Cloud dashboard:
   - Go to Settings → Secrets
   - Add: `GROQ_API_KEY = gsk_...`

### Heroku Deployment

```bash
# 1. Create Procfile
echo "web: streamlit run app.py --server.port=\$PORT" > Procfile

# 2. Create runtime.txt
echo "python-3.11.0" > runtime.txt

# 3. Deploy
heroku create your-app-name
heroku config:set GROQ_API_KEY=your_key
git push heroku main
```

---

## Performance Tuning

### Optimize for Speed

```python
# config.py
LLM_MAX_TOKENS = 300  # Shorter responses = faster
RAG_TOP_N = 3         # Fewer articles to search = faster
CACHE_ENABLED = True  # Cache calculations
```

### Monitor Performance

```bash
# Run with profiling
streamlit run app.py --logger.level=debug

# Watch for:
# - "Encoded query time: 12ms"
# - "Similarity search time: 140ms"
# - "LLM inference time: 3200ms"
```

### Load Testing

```bash
# Test with 10 concurrent users
locust -f locustfile.py -u 10 -r 2 -t 5m
```

---

## Security Checklist

- [ ] `.env` file in `.gitignore` (CRITICAL)
- [ ] API key never logged or exposed
- [ ] Input validation enabled (prevents injection attacks)
- [ ] HTML escaping enabled (prevents XSS)
- [ ] HTTPS enabled for deployment
- [ ] Rate limiting configured (if public)
- [ ] Regular security updates for dependencies

Track with:
```bash
pip list --outdated
pip-audit  # Check for known vulnerabilities
```

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Run tests: `pytest test_constitutional_helper.py -v`
3. Check logs for error details
4. Review [CODE_REVIEW.md](CODE_REVIEW.md) for known issues
5. Open GitHub issue with error details and logs

---

## Next Steps

After successful setup:
1. ✅ Test with sample questions (see [Verification](#verification))
2. ✅ Customize theme in `config.py` (colors, fonts)
3. ✅ Add custom constitutional questions to FAQ
4. ✅ Deploy to production (Streamlit Cloud / Docker / custom server)
5. ✅ Set up monitoring and alerting

Happy questioning! 🏛️
