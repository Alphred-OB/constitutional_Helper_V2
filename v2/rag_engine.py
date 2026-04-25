
import json
import os
import pickle
import logging
import numpy as np
from typing import List, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CHUNKS_PATH = "../constitution_chunks.json"
EMBEDDINGS_PATH = "../constitution_embeddings.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.15
DEFAULT_TOP_N = 5

class RAGEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.model = SentenceTransformer(MODEL_NAME)
        self.chunks = self._load_chunks()
        self.embeddings = self._load_or_build_embeddings()
        self._initialized = True
        logger.info("RAG Engine initialized successfully")

    def _load_chunks(self) -> List[Dict]:
        if not os.path.exists(CHUNKS_PATH):
            logger.error(f"Chunks file not found: {CHUNKS_PATH}")
            return []
        
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_or_build_embeddings(self) -> np.ndarray:
        if os.path.exists(EMBEDDINGS_PATH):
            with open(EMBEDDINGS_PATH, "rb") as f:
                embeddings = pickle.load(f)
            # Normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            return embeddings / (norms + 1e-10)
        
        # Build if not exists
        texts = [chunk.get("text", "") for chunk in self.chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-10)
        
        with open(EMBEDDINGS_PATH, "wb") as f:
            pickle.dump(embeddings, f)
        return embeddings

    def search(self, query: str, top_n: int = DEFAULT_TOP_N) -> List[Dict]:
        query_embedding = self.model.encode([query.strip()]).flatten()
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 1e-10:
            query_embedding = query_embedding / query_norm
            
        scores = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(scores)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < SIMILARITY_THRESHOLD:
                continue
            
            results.append({
                "chapter": self.chunks[idx].get("chapter", "Unknown"),
                "article": self.chunks[idx].get("article", ""),
                "text": self.chunks[idx].get("text", ""),
                "score": round(score, 4)
            })
        return results

    def build_context(self, results: List[Dict]) -> str:
        if not results:
            return "No specific constitutional provisions found."
        
        lines = ["=== RELEVANT SECTIONS FROM GHANA'S 1992 CONSTITUTION ===\n"]
        for i, result in enumerate(results, 1):
            label = result.get("article") or result.get("chapter")
            lines.append(f"[{i}] {label} ({result.get('chapter')})")
            lines.append(result.get("text"))
            lines.append("")
        return "\n".join(lines)
