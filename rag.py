"""
rag.py — Semantic RAG for Constitutional Helper
=================================================

Semantic search over Ghana's 1992 Constitution using sentence embeddings.
The model is loaded ONCE and reused for all queries (singleton pattern).

Key Components:
  - SentenceTransformer (all-MiniLM-L6-v2): 384-dimensional vector encoder
  - Constitution chunks: ~300 articles stored as JSON
  - Embeddings cache: Pre-computed vectors for instant similarity search
  - Similarity threshold: 0.15 minimum relevance score

Architecture:
  1. load_chunks() → Load JSON articles into memory
  2. load_or_build_embeddings() → Cache vectors to disk
  3. encode_query() → Convert question to 384-D vector
  4. search() → Find top-N articles by cosine similarity (150ms)
  5. build_context() → Format articles for LLM prompt
"""

import json
import os
import pickle
import logging
import numpy as np
from typing import List, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity

# ── Configure logging ─────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CHUNKS_PATH     = "constitution_chunks.json"
EMBEDDINGS_PATH = "constitution_embeddings.pkl"
MODEL_NAME      = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.15
DEFAULT_TOP_N = 5

# ── Singleton model cache ─────────────────────────────────────────────────────
import streamlit as st

@st.cache_resource(show_spinner=False)
def _get_model():
    """Load the SentenceTransformer model ONCE and cache it in memory."""
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading SentenceTransformer model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


# ── Load constitution chunks from JSON ───────────────────────────────────────
@st.cache_data
def load_chunks(path: str = CHUNKS_PATH) -> List[Dict]:
    """
    Load constitution chunks from JSON file.
    
    Each chunk contains:
      - chapter: Constitutional chapter name (e.g., "Chapter 2")
      - article: Article identifier (e.g., "Article 12")
      - text: Full article text (1000-2000 chars)
    
    Args:
        path: Path to constitution_chunks.json file
        
    Returns:
        List of chunk dictionaries with keys: chapter, article, text
        
    Raises:
        FileNotFoundError: If chunks file does not exist
        json.JSONDecodeError: If JSON is malformed
        KeyError: If chunk is missing required fields
    """
    try:
        if not os.path.exists(path):
            logger.error(f"Chunks file not found: {path}")
            raise FileNotFoundError(f"Constitution chunks file not found at {path}")
        
        logger.info(f"Loading constitution chunks from: {path}")
        with open(path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        # Validate chunk structure
        if not isinstance(chunks, list):
            raise ValueError(f"Expected list of chunks, got {type(chunks)}")
        
        if len(chunks) == 0:
            raise ValueError("Chunks file is empty")
        
        # Validate first chunk has required fields
        required_fields = {"text"}
        for field in required_fields:
            if field not in chunks[0]:
                raise KeyError(f"Chunk missing required field: {field}")
        
        logger.info(f"Loaded {len(chunks)} constitution chunks")
        return chunks
        
    except FileNotFoundError as e:
        logger.error(f"Chunks file error: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in chunks file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading chunks: {e}")
        raise



# ── Get or create embeddings ──────────────────────────────────────────────────
@st.cache_data
def load_or_build_embeddings(chunks: List[Dict], cache_path: str = EMBEDDINGS_PATH) -> np.ndarray:
    """
    Load or build semantic embeddings for constitution chunks.
    
    First-time execution:
      1. Read all chunk texts
      2. Encode each to 384-dimensional vector using SentenceTransformer
      3. Cache embeddings to disk (2-3MB pickle file)
      4. Subsequent loads read from disk cache (instantaneous)
    
    Architecture detail:
      - Model: all-MiniLM-L6-v2 (28M parameters, 384 output dimensions)
      - Batch size: 32 texts per encoding pass
      - First-time duration: ~60-120 seconds (includes model download)
      - Cached duration: <100ms (just unpickle)
    
    Args:
        chunks: List of chunk dictionaries from load_chunks()
        cache_path: Path to save/load embeddings pickle cache
        
    Returns:
        numpy array of shape (num_chunks, 384) where each row is a chunk vector
        
    Raises:
        ValueError: If chunks list is empty
        Exception: If model loading or encoding fails
    """
    if not chunks:
        raise ValueError("Cannot build embeddings from empty chunks list")
    
    # Try to load from cache
    if os.path.exists(cache_path):
        try:
            logger.info(f"Loading cached embeddings from: {cache_path}")
            with open(cache_path, "rb") as f:
                embeddings = pickle.load(f)
            
            if len(embeddings) != len(chunks):
                logger.warning(f"Embedding cache size ({len(embeddings)}) != chunks size ({len(chunks)}). Rebuilding...")
            else:
                # Ensure they are normalized
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / (norms + 1e-10)
                logger.info(f"Embeddings loaded and normalized. Shape: {embeddings.shape}")
                return embeddings
        except Exception as e:
            logger.warning(f"Failed to load cached embeddings: {e}. Rebuilding...")
    
    # Build embeddings from scratch
    try:
        logger.info("Building semantic embeddings from scratch...")
        model = _get_model()
        
        texts = [chunk.get("text", "") for chunk in chunks]
        if not all(texts):
            logger.warning("Some chunks have empty text")
        
        logger.info(f"Encoding {len(texts)} chunks to 384-D vectors...")
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
        
        logger.info(f"Embeddings shape: {embeddings.shape}")
        
        # Normalize embeddings for faster dot-product similarity later
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-10)
        
        # Cache to disk
        try:
            logger.info(f"Caching embeddings to: {cache_path}")
            with open(cache_path, "wb") as f:
                pickle.dump(embeddings, f)
            logger.info("Embeddings cached successfully")
        except Exception as e:
            logger.warning(f"Failed to cache embeddings (will rebuild on next run): {e}")
        
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to build embeddings: {e}")
        raise



# ── Encode a query ────────────────────────────────────────────────────────────
def encode_query(query: str) -> np.ndarray:
    """
    Encode user's question using cached SentenceTransformer.
    
    Converts natural language question into 384-dimensional vector
    that can be compared to chunk embeddings using cosine similarity.
    
    Performance: ~5-10ms per query, uses cached model instance
    
    Args:
        query: Question text (e.g., "What are my arrest rights?")
        
    Returns:
        numpy array of shape (1, 384) — the question vector
        
    Raises:
        ValueError: If query is empty
        Exception: If encoding fails
    """
    if not query or not query.strip():
        raise ValueError("Cannot encode empty query")
    
    try:
        model = _get_model()
        query_vector = model.encode([query.strip()])
        logger.debug(f"Encoded query: '{query[:50]}...' to vector shape {query_vector.shape}")
        return query_vector
    except Exception as e:
        logger.error(f"Failed to encode query: {e}")
        raise



# ── Search for relevant chunks ────────────────────────────────────────────────
def search(
    query: str,
    chunks: List[Dict],
    embeddings: np.ndarray,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = SIMILARITY_THRESHOLD
) -> List[Dict]:
    """
    Find the top-N most semantically relevant constitution chunks.
    
    Algorithm:
      1. Encode query to 384-D vector using cached model
      2. Compute cosine similarity between query and all chunk embeddings
      3. Rank chunks by similarity score (0.0 to 1.0)
      4. Return top-N chunks exceeding threshold
    
    Performance: ~150ms per search (5-10ms encode + 100-120ms similarity)
    
    Args:
        query: Question text (e.g., "What are my rights if arrested?")
        chunks: List of chunk dicts from load_chunks()
        embeddings: Matrix from load_or_build_embeddings()
        top_n: Maximum results to return (default 5)
        threshold: Minimum similarity score (0.0-1.0, default 0.15)
        
    Returns:
        List of dicts with keys:
          - chapter: "Chapter 2" (constitutional section)
          - article: "Article 14" (specific article)
          - text: Full article text
          - score: Similarity score (float, 0.0-1.0)
        
        Returns empty list if no results exceed threshold.
        
    Raises:
        ValueError: If inputs are invalid
        Exception: If similarity computation fails
    """
    try:
        if not query:
            raise ValueError("Query cannot be empty")
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})")
        if top_n <= 0:
            raise ValueError("top_n must be > 0")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        
        # Encode query and normalize it
        query_embedding = encode_query(query).flatten()
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 1e-10:
            query_embedding = query_embedding / query_norm
            
        # Since chunks are pre-normalized, dot product is cosine similarity
        scores = np.dot(embeddings, query_embedding)
        
        # Sort by score and get top indices
        top_indices = np.argsort(scores)[::-1][:top_n]
        
        # Build results
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            
            # Filter by threshold
            if score < threshold:
                logger.debug(f"Skipping chunk {idx}: score {score:.4f} < threshold {threshold}")
                continue
            
            results.append({
                "chapter": chunks[idx].get("chapter", "Unknown"),
                "article": chunks[idx].get("article", ""),
                "text": chunks[idx].get("text", ""),
                "score": round(score, 4)
            })
        
        logger.info(f"Search found {len(results)} relevant chunks (threshold={threshold})")
        return results
        
    except ValueError as e:
        logger.error(f"Search validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise



# ── Format retrieved chunks as AI context ────────────────────────────────────
def build_context(results: List[Dict]) -> str:
    """
    Format retrieved constitution chunks into context for LLM prompt.
    
    Converts list of search results into readable string formatted for
    insertion into the LLM prompt, ensuring the LLM has constitutional
    context to ground its answer.
    
    Example output:
    
      === RELEVANT SECTIONS FROM GHANA'S 1992 CONSTITUTION ===
      
      [1] Article 14 (Chapter 2)
      Article 14. (1) A person shall not be arrested...
      
      [2] Article 15 (Chapter 2)
      Article 15. (1) No person shall be held in unlawful detention...
    
    Args:
        results: List of dicts from search() function
        
    Returns:
        Formatted string ready to insert into LLM prompt.
        Returns informative message if results is empty.
        
    Raises:
        TypeError: If results is not a list
    """
    try:
        if not isinstance(results, list):
            raise TypeError(f"Expected list, got {type(results)}")
        
        if not results:
            logger.debug("No results to build context from")
            return "No specific constitutional provisions found."
        
        # Build context string
        lines = ["=== RELEVANT SECTIONS FROM GHANA'S 1992 CONSTITUTION ===\n"]
        
        for i, result in enumerate(results, 1):
            if not isinstance(result, dict):
                logger.warning(f"Result {i} is not a dict: {type(result)}")
                continue
            
            article = result.get("article", "")
            chapter = result.get("chapter", "Unknown")
            text = result.get("text", "")
            score = result.get("score", 0)
            
            label = article if article else chapter
            lines.append(f"[{i}] {label} ({chapter}) [Relevance: {score}]")
            lines.append(text)
            lines.append("")
        
        context = "\n".join(lines)
        logger.debug(f"Built context from {len(results)} results ({len(context)} chars)")
        return context
        
    except TypeError as e:
        logger.error(f"Context building type error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to build context: {e}")
        raise

