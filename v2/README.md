
# GhanaLex v2 - Premium Constitutional AI

This version replaces the Streamlit interface with a high-performance FastAPI backend and a custom, god-tier HTML/Tailwind frontend.

## Improvements
- **Zero White Flashes**: Asynchronous loading states with beautiful animations.
- **Full Customization**: Complete control over the UI/UX.
- **Speed**: Built on FastAPI for ultra-low latency API responses.
- **Premium Aesthetics**: Dark mode, glassmorphism, and modern typography.

## How to Run

### 1. Install Dependencies
Make sure you have the required packages installed:
```bash
pip install fastapi uvicorn sentence-transformers scikit-learn groq python-dotenv
```

### 2. Start the API
Navigate to the `v2` folder and run the FastAPI server:
```bash
cd v2
python api.py
```
The API will start at `http://localhost:8000`.

### 3. Open the UI
Simply open `v2/index.html` in your browser. You can also use a simple server:
```bash
# In another terminal
cd v2
python -m http.server 3000
```
Then visit `http://localhost:3000`.

## Directory Structure
- `api.py`: FastAPI server handling chat requests.
- `rag_engine.py`: Standalone semantic search logic (reused from root).
- `index.html`: The premium chat interface.
- `app.js`: Frontend logic and API integration.
