"""
Generador de embeddings para productos usando OpenAI.
"""
import openai
import logging
from typing import List, Optional, Dict, Any
import tiktoken
import numpy as np
from datetime import datetime

from ...config import ai_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generador de embeddings usando modelos de OpenAI.
    """
    
    def __init__(self):
        self.client = None
        self.model = ai_settings.embedding_model
        self.dimension = ai_settings.embedding_dimension
        
        # Initialize tokenizer for text processing
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # fallback
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available."""
        if ai_settings.openai_api_key:
            self.client = openai.OpenAI(api_key=ai_settings.openai_api_key)
            logger.info(f"OpenAI client initialized with model: {self.model}")
        else:
            logger.warning("OpenAI API key not found. Embedding generation will be disabled.")
    
    def is_available(self) -> bool:
        """Check if embedding generation is available."""
        return self.client is not None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """
        Truncate text to fit within token limit.
        """
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate and decode back to text
        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens)
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better embeddings.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long
        text = self.truncate_text(text)
        
        return text
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        """
        if not self.is_available():
            logger.error("OpenAI client not available")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
        
        try:
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            # Generate embedding
            response = self.client.embeddings.create(
                input=processed_text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_batch_embeddings(self, texts: List[str]) -> Dict[int, Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        Returns dict with index -> embedding mapping.
        """
        if not self.is_available():
            logger.error("OpenAI client not available")
            return {}
        
        if not texts:
            return {}
        
        # Preprocess all texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        # Filter out empty texts but keep track of original indices
        valid_texts = []
        index_mapping = {}
        
        for i, text in enumerate(processed_texts):
            if text and text.strip():
                index_mapping[len(valid_texts)] = i
                valid_texts.append(text)
        
        if not valid_texts:
            logger.warning("No valid texts found for batch embedding")
            return {}
        
        try:
            # Generate embeddings in batch
            response = self.client.embeddings.create(
                input=valid_texts,
                model=self.model
            )
            
            # Map results back to original indices
            results = {}
            for i, embedding_data in enumerate(response.data):
                original_index = index_mapping[i]
                results[original_index] = embedding_data.embedding
            
            logger.info(f"Generated {len(results)} embeddings in batch")
            return results
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return {}
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm_a = np.linalg.norm(vec1)
            norm_b = np.linalg.norm(vec2)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]],
        threshold: float = 0.7
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to the query.
        Returns list of (index, similarity) tuples, sorted by similarity.
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.calculate_similarity(query_embedding, candidate)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities


# Global instance
embedding_generator = EmbeddingGenerator()
