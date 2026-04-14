# Deployment Guide - Constitutional Helper

Deploy your app online where users can access it from anywhere. Simple, no downloads needed.

---

## **The Easiest Way: Streamlit Cloud**

Users just visit a link in their browser. No installation, no downloads.

```
https://your-username-ghanalex.streamlit.app
```

### Prerequisites
- GitHub repository with your code (free account)
- Streamlit Cloud account (free signup)
- Groq API key ($5 free credits monthly, plenty for testing)

### Deployment Steps

**1. Get your API key**
- Sign up: [console.groq.com](https://console.groq.com)
- Copy your GROQ_API_KEY

**2. Push code to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ghanalex.git
git branch -M main
git push -u origin main
```

**3. Create local secrets file** (for local testing)
```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "your-groq-api-key-here"
```

**4. Add to `.gitignore`** (don't push secrets!)
```
.streamlit/secrets.toml
.env
```

**5. Deploy on Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Click "New app"
- Select your GitHub repo: `your-username/ghanalex`
- Branch: `main`
- Main file: `app.py`
- Click "Deploy"

**6. Add Groq API key in Streamlit Cloud**
- In app settings → "Secrets"
- Add: 
  ```
  GROQ_API_KEY = your-api-key-here
  ```
- App auto-redeploys

### Done!
Your app is now live and shareable.

---

## **For Local Testing**

Before deploying, test locally:

```bash
# Create .env file
echo GROQ_API_KEY=your-api-key > .env

# Run the app
streamlit run app.py
```

Visit: http://localhost:8501

---

## **Groq API Pricing**

- **Free tier**: $5/month in credits (plenty for testing & light production)
- **Pay as you go**: Very cheap (~$0.001 per query)

To check usage:
1. Go to [console.groq.com](https://console.groq.com)
2. Click "Billing" → "Usage"

---

## **Updating Your App**

1. Make changes to code
2. Test locally: `streamlit run app.py`
3. Push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push
   ```
4. Streamlit Cloud auto-deploys (2-5 minutes)

---

## **Performance**

- **Instant startup**: No model loading
- **Fast responses**: 2-5 seconds per question
- **No limits**: Handle unlimited users (Streamlit Cloud manages scaling)

---

## **Sharing with Users**

Just share the URL:
```
https://your-username-ghanalex.streamlit.app
```

Users can:
- ✅ Click the link
- ✅ Start asking questions immediately
- ✅ Use on phone/tablet/computer
- ✅ No downloads, no installation, no configuration

---

## **Troubleshooting**

| Problem | Solution |
|---------|----------|
| **Cloud deployment fails** | Check `requirements.txt` has all packages |
| **App won't start locally** | `pip install -r requirements.txt` |
| **"GROQ_API_KEY not found"** | Check `.env` file or Streamlit secrets |
| **Slow responses** | Check Groq API status: [status.groq.com](https://status.groq.com) |
| **Help, my app crashed** | Check logs: Settings → "Logs" in Streamlit Cloud |

---

## **Free Alternatives** (if you don't want to pay)

If you want completely free hosting, consider:
- **Railway** or **Render** (free tier available)
- **Hugging Face Spaces** (very easy)
- **Heroku** (paid now, but affordable)

All work the same way—just connect your GitHub repo.

---

## **Summary**

✅ Sign up on [share.streamlit.io](https://share.streamlit.io)
✅ Connect your GitHub
✅ Add Groq API key
✅ Done! Share the link

That's deployment. Simple.
