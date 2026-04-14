# Constitutional Helper - Quick Deployment Guide

**Time to Production**: ~10 minutes  
**Technical Level**: Intermediate  
**Risk Level**: 🟢 Low (all fixes verified)

---

## Pre-Deployment Checklist (5 minutes)

```bash
# 1. Verify environment
python verify_setup.py

# Expected output:
# [PASS] ALL VALIDATION TESTS PASSED
```

```bash
# 2. Check dependencies installed
pip list | grep -E "streamlit|groq|sentence-transformers"

# Expected: All installed with versions
```

```bash
# 3. Confirm API key is set
cat .env | grep GROQ_API_KEY

# Expected: GROQ_API_KEY=gsk_...
```

```bash
# 4. Test core functionality (optional)
python -c "from app import validate_question, escape_and_format_html; print('[OK] Core functions loaded')"

# Expected: [OK] Core functions loaded
```

---

## Deployment Paths

### 🟢 Path 1: Streamlit Cloud (Recommended - Easiest)

**Time**: 5 minutes | **Cost**: Free | **Maintenance**: Minimal

```bash
# 1. Push to GitHub (skip .env file)
git add app.py config.py rag.py icons.py requirements.txt
git commit -m "Production deployment v1"
git push origin main

# 2. Go to streamlit.io/cloud
# 3. Click "New App" > Select your repo > Select app.py
# 4. Click "Deploy"

# 5. Once deployed, add secret:
# - Go to Settings (gear icon)
# - Click "Secrets"
# - Add: GROQ_API_KEY = gsk_...

# 6. Your app is live!
# - URL: https://your-app-name.streamlit.app
```

### 🟡 Path 2: Docker (Recommended - Production)

**Time**: 10 minutes | **Cost**: Depends on hosting | **Maintenance**: Moderate

```bash
# 1. Build Docker image
docker build -t constitutional-helper:latest .

# 2. Test locally
docker run -p 8501:8501 \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  constitutional-helper:latest

# 3. Visit http://localhost:8501 to verify

# 4. Push to Docker Hub (optional)
docker tag constitutional-helper:latest yourusername/constitutional-helper:latest
docker push yourusername/constitutional-helper:latest

# 5. Deploy to your server:
docker run -d \
  -p 8501:8501 \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  --restart unless-stopped \
  constitutional-helper:latest
```

Required file `Dockerfile` (create if doesn't exist):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### 🟠 Path 3: Self-Hosted (Advanced)

**Time**: 15 minutes | **Cost**: Server expenses | **Maintenance**: High

```bash
# 1. SSH into your server
ssh user@your-server.com

# 2. Clone repository
git clone https://github.com/yourrepo/constitutional-helper.git
cd constitutional-helper

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment
echo "GROQ_API_KEY=your_key" > .env
chmod 600 .env

# 6. Run with systemd service (optional but recommended)
sudo tee /etc/systemd/system/constitutional-helper.service > /dev/null <<EOF
[Unit]
Description=Constitutional Helper
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/user/constitutional-helper
Environment="GROQ_API_KEY=your_key"
ExecStart=/home/user/constitutional-helper/venv/bin/streamlit run app.py --server.port=8501 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Enable and start service
sudo systemctl enable constitutional-helper
sudo systemctl start constitutional-helper
sudo systemctl status constitutional-helper

# 8. Configure reverse proxy (nginx)
# [See nginx example below]
```

#### Nginx Reverse Proxy (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Post-Deployment Verification (1 minute)

```bash
# 1. Check app is running
curl http://localhost:8501 2>&1 | head -1

# Expected: Something like "<!DOCTYPE html>"
```

```bash
# 2. Test API endpoint
curl -X GET http://localhost:8501/_stcore/health

# Expected: 200 response
```

```bash
# 3. Open in browser
# Navigate to http://localhost:8501
# Expected: Constitutional Helper interface loads
```

```bash
# 4. Test a question
# Ask: "What are my arrest rights?"
# Expected: Answer grounded in Articles 14-15 of Ghana Constitution
```

---

## Monitoring (Ongoing)

### View Logs
```bash
# Docker
docker logs constitutional-helper

# Systemd service
sudo journalctl -u constitutional-helper -f

# Direct output
tail -f /var/log/constitutional-helper.log
```

### Health Check
```bash
# Simple endpoint check
watch -n 30 "curl -s http://localhost:8501/_stcore/health | jq '.'"

# Response time test
time curl -s http://localhost:8501 > /dev/null
```

### Performance Baseline
- API response: Should be 3-6 seconds
- Page load: Should be <2 seconds
- First startup: Should be <3 minutes

---

## Rollback Plan

### If Something Goes Wrong

```bash
# Docker - Revert to previous version
docker run -p 8501:8501 \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  constitutional-helper:previous

# Systemd - Revert to previous deployment
cd /home/user/constitutional-helper
git revert HEAD
git push
sudo systemctl restart constitutional-helper

# Manual - Go back to old code
cp app_old.py app.py
streamlit run app.py
```

### Debugging Checklist
1. ✅ Check logs for error messages
2. ✅ Verify API key is valid
3. ✅ Check internet connection
4. ✅ Verify Groq API status (https://status.groq.com)
5. ✅ Review SETUP.md troubleshooting section
6. ✅ Restart the app

---

## Security Reminders

- **Never commit `.env` file** - It contains API key
- **Rotate API key** every 30 days
- **Monitor API usage** in Groq console
- **Keep dependencies updated** - Run `pip install --upgrade -r requirements.txt` monthly
- **Review logs regularly** - Look for unusual patterns
- **Use HTTPS** in production - Set up SSL certificate
- **Rate limit (optional)** - Add if deployed publicly

---

## Useful Commands

```bash
# Stop app
streamlit run app.py  # Then Ctrl+C

# Check Python version
python --version

# View active processes
ps aux | grep streamlit

# Kill process on port 8501
sudo lsof -ti:8501 | xargs kill -9

# View disk usage
du -sh *

# Monitor memory
watch -n 1 'ps aux | grep python'
```

---

## Performance Optimization (Optional)

If you need faster response times:

```python
# In config.py, reduce these:
LLM_MAX_TOKENS = 300  # Shorter responses
RAG_TOP_N = 3         # Fewer articles to search
```

If you need more accurate results:

```python
# In config.py, increase these:
RAG_SIMILARITY_THRESHOLD = 0.20  # Higher threshold (more strict)
LLM_MAX_TOKENS = 800             # Longer responses
```

---

## Support Contacts

- **Groq API Issues**: support@groq.com or https://console.groq.com
- **Streamlit Issues**: documentation at https://docs.streamlit.io
- **Python Issues**: Stack Overflow or https://python.org
- **This Project**: Check CODE_REVIEW.md or SETUP.md

---

## Next Steps After Deployment

1. ✅ Share deployment URL with stakeholders
2. ✅ Gather user feedback on answer quality
3. ✅ Monitor response times and API usage
4. ✅ Plan for model updates (monthly)
5. ✅ Schedule knowledge base updates (as-needed)
6. ✅ Set up automated backups (if applicable)

---

**Congratulations! Your Constitutional Helper is now in production! 🎉**

Questions? See [SETUP.md](SETUP.md) or [CODE_REVIEW.md](CODE_REVIEW.md)
