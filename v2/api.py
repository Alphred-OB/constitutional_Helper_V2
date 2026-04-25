import os
import json
import base64
import asyncio
import logging
import edge_tts
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from dotenv import load_dotenv
from rag_engine import RAGEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Constitutional Helper API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from groq import AsyncGroq

# Initialize RAG and AsyncGroq
rag = RAGEngine()
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    language: str = "English"

@app.get("/audio")
async def get_audio(text: str, language: str = "English"):
    try:
        voice_map = {
            "English": "en-NG-AbeoNeural",
            "Twi": "en-NG-AbeoNeural"
        }
        voice = voice_map.get(language, "en-NG-AbeoNeural")
        if language == "Twi":
            text = text.replace("ɛ", "e").replace("Ɛ", "E").replace("ɔ", "o").replace("Ɔ", "O")
            
        communicate = edge_tts.Communicate(text[:1000], voice)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        
        return {"audio_b64": base64.b64encode(audio_bytes).decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-constitution")
async def download_constitution():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Try parent directory
    pdf_path = os.path.join(os.path.dirname(current_dir), "Ghana Constitution.pdf")
    if not os.path.exists(pdf_path):
        # Try current directory
        pdf_path = os.path.join(current_dir, "Ghana Constitution.pdf")
    
    if os.path.exists(pdf_path):
        from fastapi.responses import FileResponse
        return FileResponse(pdf_path, filename="1992_Constitution_of_Ghana.pdf", media_type="application/pdf")
    
    raise HTTPException(status_code=404, detail="Constitution PDF not found")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        # 1. Read file
        contents = await file.read()
        
        # 2. Call Groq Whisper
        # Note: Groq expects a file-like object with a name
        import io
        audio_file = io.BytesIO(contents)
        audio_file.name = "audio.wav"
        
        transcription = await groq_client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="json",
        )
        
        return {"text": transcription.text}
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 1. Search (Blocking for now, but fast)
        results = rag.search(request.message)
        context = rag.build_context(results)
        
        # 2. Build Prompt
        if request.language == "Twi":
            lang_note = "Reply in simple Asante Twi. Write 'Ghana' as 'Gaana'. Keep sentences short."
        else:
            lang_note = "Reply in simple, straightforward English without legal jargon."

        prompt = f"""You are Constitutional Helper, an expert on the 1992 Constitution of Ghana.
        Answer the question based ONLY on the constitutional articles provided below.
        
        {context}
        
        STRICT RESPONSE STRUCTURE:
        1. ### ANALYSIS
           Provide a clear, simple explanation in {request.language}.
        
        2. ### REFERENCES
           List each article used as a bullet point. Include the Article number in **bold** followed by the exact verbatim quote in "quotes".
        
        STRICT RULES:
        1. Answer using ONLY the provided articles. If not found, say it's not available.
        2. NO EXTERNAL DATA.
        
        {lang_note}
        Question: {request.message}"""

        async def stream_generator():
            # Send context as first 'hidden' chunk or just send tokens
            # We'll use a special delimiter for context if needed, but let's keep it simple: 
            # Send context as a JSON-encoded prefix line
            yield json.dumps({"context": results}) + "\n--CONTEXT_END--\n"
            
            chat_stream = await groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                stream=True,
            )
            async for chunk in chat_stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- STATIC FILE SERVING (For Deployment) ---
@app.get("/")
async def serve_home():
    # Relative to the root project directory
    home_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "homepage", "index.html")
    return FileResponse(home_path)

@app.get("/app")
async def serve_app():
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    return FileResponse(app_path)

# Mount the entire v2 directory for assets (js, css, etc.)
app.mount("/v2", StaticFiles(directory="v2"), name="v2")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
