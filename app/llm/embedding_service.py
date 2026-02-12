"""
Embedding service for semantic query matching.
Generates embeddings for queries and performs similarity search.
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Dict
import os
import pickle
from app.queries.query_registry import QUERY_REGISTRY


class EmbeddingService:
    """Service for generating embeddings and finding similar queries."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use.
                       'all-MiniLM-L6-v2' is fast and good for semantic similarity.
                       'all-mpnet-base-v2' is more accurate but slower.
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.query_embeddings: np.ndarray = None
        self.query_metadata: List[Dict] = []
        self._embeddings_loaded = False
        
    def _build_query_text(self, query_id: str, query_info: dict, example_question: str = None) -> str:
        """
        Build a rich text representation of a query for embedding.
        
        Args:
            query_id: The query identifier
            query_info: Query information from registry
            example_question: Optional example question for this query
            
        Returns:
            Combined text for embedding
        """
        parts = []
        
        # Add query description
        parts.append(query_info.get("description", ""))
        
        # Add query ID as context
        parts.append(f"Query ID: {query_id}")
        
        # Add parameter descriptions
        params = query_info.get("parameters", {})
        if params:
            param_descs = []
            for param_name, param_info in params.items():
                desc = param_info.get("description", "")
                required = param_info.get("required", False)
                if required:
                    param_descs.append(f"{param_name} (required): {desc}")
                else:
                    default = param_info.get("default", "none")
                    param_descs.append(f"{param_name} (optional, default={default}): {desc}")
            if param_descs:
                parts.append("Parameters: " + "; ".join(param_descs))
        
        # Add example question if available
        if example_question:
            parts.append(f"Example question: {example_question}")
        
        return ". ".join(parts)
    
    def load_example_questions(self) -> Dict[str, str]:
        """
        Load example questions from the markdown file.
        Maps query number to example question text.
        
        Returns:
            Dictionary mapping query number (1-50) to question text
        """
        examples = {}
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Avahi Sample Queries - Questions Only.md"
        )
        
        if not os.path.exists(file_path):
            return examples
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse the markdown to extract numbered questions
        lines = content.split('\n')
        current_number = None
        
        for line in lines:
            line = line.strip()
            # Match numbered questions like "1. **What is..."
            if line and line[0].isdigit() and '**' in line:
                # Extract number
                try:
                    current_number = int(line.split('.')[0])
                    # Extract question text (remove markdown formatting)
                    question = line.split('**')[1] if '**' in line else line.split('.', 1)[1].strip()
                    question = question.replace('**', '').strip()
                    if question:
                        examples[current_number] = question
                except (ValueError, IndexError):
                    continue
        
        return examples
    
    def build_embeddings(self, force_rebuild: bool = False):
        """
        Build embeddings for all queries in the registry.
        
        Args:
            force_rebuild: If True, rebuild even if cached embeddings exist
        """
        cache_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            ".embeddings_cache.pkl"
        )
        
        # Try to load from cache
        if not force_rebuild and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    cached_ids = set(m['query_id'] for m in cache_data.get('metadata', []))
                    registry_ids = set(QUERY_REGISTRY.keys())
                    if (cache_data.get('model_name') == self.model_name and 
                        cached_ids == registry_ids):
                        self.query_embeddings = cache_data['embeddings']
                        self.query_metadata = cache_data['metadata']
                        self._embeddings_loaded = True
                        print(f"✅ Loaded {len(self.query_metadata)} query embeddings from cache")
                        return
                    else:
                        print(f"⚠️  Cache is stale (query IDs changed). Rebuilding embeddings...")
            except Exception as e:
                print(f"⚠️  Failed to load cache: {e}. Rebuilding embeddings...")
        
        # Build embeddings
        print("🔄 Building query embeddings...")
        example_questions = self.load_example_questions()
        
        texts = []
        metadata = []
        
        # Map query registry keys to numbers (1-50) for example matching
        # We'll match by order in the registry
        query_ids = list(QUERY_REGISTRY.keys())
        
        for idx, (query_id, query_info) in enumerate(QUERY_REGISTRY.items(), 1):
            # Try to find matching example question
            example_question = example_questions.get(idx)
            
            # Build rich text representation
            query_text = self._build_query_text(query_id, query_info, example_question)
            
            texts.append(query_text)
            metadata.append({
                'query_id': query_id,
                'description': query_info.get('description', ''),
                'example_question': example_question
            })
        
        # Generate embeddings
        print(f"📊 Generating embeddings for {len(texts)} queries...")
        self.query_embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        self.query_metadata = metadata
        self._embeddings_loaded = True
        
        # Cache embeddings
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'model_name': self.model_name,
                    'query_count': len(QUERY_REGISTRY),
                    'embeddings': self.query_embeddings,
                    'metadata': self.query_metadata
                }, f)
            print(f"💾 Cached embeddings to {cache_file}")
        except Exception as e:
            print(f"⚠️  Failed to cache embeddings: {e}")
    
    def find_similar_queries(
        self, 
        question: str, 
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Tuple[str, float, Dict]]:
        """
        Find the most similar queries to a given question.
        
        Args:
            question: User's natural language question
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of tuples: (query_id, similarity_score, metadata)
            Sorted by similarity (highest first)
        """
        if not self._embeddings_loaded:
            self.build_embeddings()
        
        # Generate embedding for the question
        question_embedding = self.model.encode(question, convert_to_numpy=True)
        
        # Calculate cosine similarities
        similarities = np.dot(self.query_embeddings, question_embedding) / (
            np.linalg.norm(self.query_embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= min_similarity:
                results.append((
                    self.query_metadata[idx]['query_id'],
                    similarity,
                    self.query_metadata[idx]
                ))
        
        return results
    
    def get_confidence_level(self, similarity_score: float) -> str:
        """
        Categorize confidence level based on similarity score.
        
        Args:
            similarity_score: Similarity score (0.0 to 1.0)
            
        Returns:
            Confidence level: 'high', 'medium', 'low'
        """
        if similarity_score >= 0.80:
            return 'high'
        elif similarity_score >= 0.65:
            return 'medium'
        else:
            return 'low'


# Global instance (lazy-loaded)
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        _embedding_service.build_embeddings()
    return _embedding_service
