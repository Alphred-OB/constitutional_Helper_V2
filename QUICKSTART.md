# Quick Start Guide - Constitutional Helper

Get the app running in **2 minutes** for users.

---

## **For Users: Just Want to Use It**

### Online (Easiest - Recommended)
1. **Visit**: [https://ghanalex.streamlit.app](https://ghanalex.streamlit.app)
2. **Start asking** constitutional questions
3. **That's it!** Works on any device

No downloads, no installation, just a link.

---

## **For Developers: Want to Modify**

### Setup (Windows)

**1. Prerequisites**
- Python 3.9+ installed
- Git installed

**2. Clone & install**
```bash
git clone https://github.com/your-username/ghanalex.git
cd ghanalex
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**3. Get Groq API key**
- Sign up: [console.groq.com](https://console.groq.com)
- Copy your API key (free $5/month)

**4. Create `.env` file**
```
GROQ_API_KEY=your_api_key_here
```

**5. Run locally**
```bash
streamlit run app.py
```

Visit: `http://localhost:8501`

---

## **Deploy Online (5 minutes)**

Once working locally:

**1. Push to GitHub**
```bash
git add .
git commit -m "Ready to deploy"
git push
```

**2. Go to** [share.streamlit.io](https://share.streamlit.io)

**3. Click "New app"** and select:
- Repository: `your-username/ghanalex`
- Branch: `main`
- Main file: `app.py`

**4. Click Deploy!**

**5. Add API key in app settings** → Secrets:
```
GROQ_API_KEY = your-key-here
```

**Done!** Your app is now live at a public URL.

---

## **What You Can Ask**

✅ **Questions about Ghana's Constitution:**
- "What are my rights as a citizen?"
- "How do elections work?"
- "What does the Constitution say about education?"
- "Who can become President?"

✅ **Available in:**
- 🇬🇭 English
- 🗣️ Asante Twi

✅ **Features:**
- 📖 Instant answers from actual constitutional text
- 🗣️ Responses in English or Twi
- 📥 Download the full constitution

---

## **Common Tasks**

### Test local setup
```bash
python check_setup.py
```

### Update dependencies
```bash
pip freeze > requirements.txt
```

### Clear cache (if something feels stuck)
```bash
streamlit cache clear
streamlit run app.py
```

### Push updates to Streamlit Cloud
```bash
git add .
git commit -m "New changes"
git push
# Cloud auto-deploys in ~3 minutes
```

---

## **Troubleshooting**

**"Module not found"**
```bash
.venv\Scripts\activate  # on Windows
pip install -r requirements.txt
```

**"GROQ_API_KEY not set"**
- Check `.env` file has: `GROQ_API_KEY=gsk_...`
- Restart Streamlit app

**"App won't start"**
```bash
streamlit cache clear
streamlit run app.py
```

**Slow first run?**
- Normal - models load once
- First run: 5-10 seconds
- Next runs: ~1 second

---

## **Deployment & Architecture**

- **Frontend**: Streamlit (web interface)
- **Search**: SentenceTransformers (vector search)
- **LLM**: Groq API (fast cloud inference)
- **Data**: Constitution chunks (JSON + embeddings)

---

## **Support**

- Issues? [GitHub Issues](https://github.com/your-username/ghanalex/issues)
- Questions? [GitHub Discussions](https://github.com/your-username/ghanalex/discussions)
- Full guide: [DEPLOY.md](DEPLOY.md)
- README: [README.md](README.md)
