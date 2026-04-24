"""
Privacy Policy - Constitutional Helper
"""
import streamlit as st

st.set_page_config(page_title="Privacy Policy — Constitutional Helper", page_icon="favicon.png", layout="wide")

# Load shared CSS
import os
css_file = os.path.join(os.path.dirname(__file__), "..", "styles.css")
if os.path.exists(css_file):
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="page-container">

<a href="/" target="_self" class="back-link">← Back to Constitutional Helper</a>

# Privacy Policy

**Effective Date:** January 1, 2026  
**Last Updated:** April 23, 2026

---

## 1. Introduction

Constitutional Helper ("the Service") is operated by the GhanaLex Team ("we", "us", "our"). 
This Privacy Policy explains how we collect, use, and protect information when you use our Service.

We are committed to protecting your privacy and handling your data transparently.

---

## 2. Information We Collect

### 2.1 Information You Provide
- **Questions submitted:** The constitutional questions you type into the chat interface
- **Language preference:** Your selected language (English or Twi)

### 2.2 Information Collected Automatically
- **Usage data:** Pages visited, features used, and interaction patterns
- **Device information:** Browser type, operating system, and screen resolution
- **Log data:** IP address, access times, and referring URLs

### 2.3 Information We Do NOT Collect
- We do **not** require account creation or login
- We do **not** collect personal identification information (name, email, phone)
- We do **not** use cookies for advertising or tracking

---

## 3. How We Use Your Information

We use collected information solely to:
- Provide accurate constitutional answers to your questions
- Improve the accuracy and relevance of AI-generated responses
- Monitor and maintain the security and performance of the Service
- Analyze usage patterns to improve user experience

---

## 4. Data Processing

### 4.1 AI Processing
Your questions are processed through:
- **Semantic search:** Your question is compared against constitutional text locally
- **Language model:** Questions are sent to Groq API for response generation

### 4.2 Third-Party Services
We use the following third-party services:
| Service | Purpose | Data Shared |
|---|---|---|
| Groq API | AI response generation | Question text only |
| Google TTS | Audio generation (when enabled) | Response text |

We do not sell, rent, or share your data with third parties for marketing purposes.

---

## 5. Data Retention

- Chat messages are stored only in your browser session and are **not** persisted on our servers
- Session data is automatically cleared when you close your browser or clear your chat
- Server logs are retained for a maximum of 30 days for security and debugging purposes

---

## 6. Data Security

We implement appropriate technical measures to protect your information:
- All communications are encrypted in transit (HTTPS)
- Input validation and sanitization to prevent injection attacks
- XSRF protection enabled on all endpoints
- No persistent storage of user queries on our infrastructure

---

## 7. Your Rights

You have the right to:
- **Access:** Know what data we process about you
- **Deletion:** Request deletion of any stored data
- **Opt-out:** Stop using the Service at any time without consequence
- **Transparency:** Receive clear information about our data practices

---

## 8. Children's Privacy

The Service is not directed at children under 13 years of age. We do not knowingly collect 
personal information from children.

---

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. Changes will be posted on this page with 
an updated "Last Updated" date. Continued use of the Service after changes constitutes acceptance.

---

## 10. Contact

For privacy-related questions or concerns, contact the **GhanaLex Team**.

</div>
""")

# Footer
st.markdown("""
<div class="app-footer">
  <div>
    <a href="/Documentation" target="_self">Documentation</a>
    <a href="/Privacy_Policy" target="_self">Privacy Policy</a>
    <a href="/Terms_of_Service" target="_self">Terms of Service</a>
  </div>
  <div class="footer-brand">© 2026 Constitutional Helper</div>
  <div>Powered by GhanaLex AI • 1992 Constitution of Ghana</div>
</div>
""", unsafe_allow_html=True)
