"""
Intent classification using semantic similarity (not keyword matching).

This approach is MUCH more robust than keyword matching because it:
1. Uses embeddings to understand MEANING, not just exact words
2. Handles variations naturally ("same", "redo", "once more" all similar)
3. Provides confidence scores for better decisions
4. Learns from examples, doesn't rely on exhaustive keyword lists
"""

from typing import Tuple
from app.llm.embedding_service import get_embedding_service


# Intent examples - these define what each intent "looks like"
# Add more examples over time to improve accuracy!
INTENT_EXAMPLES = {
    "FOLLOW_UP": [
        # Direct reuse
        "same for different value",
        "again with new parameter",
        "repeat that query",
        "do it again",
        "one more time",
        "redo the previous",
        "once more",
        
        # Parameter modifications
        "same but for 7 days",
        "give me same data for Houston",
        "show me same with threshold 0.80",
        "now with different hours",
        "also for next week",
        "but with HB05 instead",
        "change to 21 days",
        
        # Natural variations
        "could you run that again",
        "do the same thing",
        "similar but different threshold",
        "rerun with changes",
    ],
    
    "SYSTEM_INFO": [
        # Project questions
        "what projects do you have",
        "which project is this",
        "tell me about the project",
        "what data is available",
        "describe your capabilities",
        
        # Location questions
        "what locations do you serve",
        "which zones are available",
        "list the locations",
        "what areas do you cover",
        
        # Capability questions
        "what can you help me with",
        "what do you support",
        "what kind of queries can you do",
        "tell me what you can do",
        "explain your features",
    ],
    
    "DATA_QUERY": [
        # These are actual data queries
        "what is the GSI probability",
        "show me load forecast",
        "calculate wind ramp",
        "find peak temperature",
        "give me solar generation data",
        "compare zones",
    ]
}


class IntentClassifier:
    """
    Semantic intent classification using embeddings.
    
    Much more robust than keyword matching!
    """
    
    def __init__(self, confidence_threshold: float = 0.65):
        """
        Initialize the intent classifier.
        
        Args:
            confidence_threshold: Minimum confidence to accept classification
        """
        self.embedding_service = get_embedding_service()
        self.confidence_threshold = confidence_threshold
        self.intent_examples = INTENT_EXAMPLES
        
        # Cache embeddings for examples (performance optimization)
        self._example_embeddings = {}
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """Pre-compute embeddings for all examples (faster classification)."""
        print("📚 Pre-computing intent example embeddings...")
        for intent, examples in self.intent_examples.items():
            self._example_embeddings[intent] = []
            for example in examples:
                embedding = self.embedding_service.embed_text(example)
                self._example_embeddings[intent].append((example, embedding))
        print(f"✅ Precomputed embeddings for {sum(len(v) for v in self._example_embeddings.values())} examples")
    
    def classify(self, question: str) -> Tuple[str, float]:
        """
        Classify the intent of a question using semantic similarity.
        
        Args:
            question: User's question
            
        Returns:
            Tuple of (intent, confidence)
            - intent: "FOLLOW_UP", "SYSTEM_INFO", or "DATA_QUERY"
            - confidence: 0.0-1.0 (how confident we are)
        """
        # Embed the question
        question_embedding = self.embedding_service.embed_text(question)
        
        # Calculate similarity to each intent's examples
        intent_scores = {}
        
        for intent, cached_examples in self._example_embeddings.items():
            max_similarity = 0.0
            
            for example_text, example_embedding in cached_examples:
                # Calculate cosine similarity
                similarity = self.embedding_service.calculate_similarity(
                    question_embedding,
                    example_embedding
                )
                max_similarity = max(max_similarity, similarity)
            
            intent_scores[intent] = max_similarity
        
        # Get best intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        print(f"🎯 Intent classification:")
        for intent, score in sorted(intent_scores.items(), key=lambda x: x[1], reverse=True):
            emoji = "🟢" if intent == best_intent else "⚪"
            print(f"   {emoji} {intent}: {score:.3f}")
        
        return best_intent, confidence, intent_scores
    
    def is_follow_up(self, question: str, min_confidence: float = 0.65) -> Tuple[bool, float]:
        """
        Check if question is a follow-up query.
        
        Args:
            question: User's question
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (is_follow_up, confidence)
        """
        intent, confidence, _ = self.classify(question)
        is_follow_up = (intent == "FOLLOW_UP" and confidence >= min_confidence)
        return is_follow_up, confidence
    
    def is_system_info(self, question: str, min_confidence: float = 0.65) -> Tuple[bool, float]:
        """
        Check if question is asking for system information.
        
        Args:
            question: User's question
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (is_system_info, confidence)
        """
        intent, confidence, _ = self.classify(question)
        is_system_info = (intent == "SYSTEM_INFO" and confidence >= min_confidence)
        return is_system_info, confidence
    
    def add_examples(self, intent: str, new_examples: list):
        """
        Dynamically add new examples for an intent (learn over time!).
        
        Args:
            intent: Intent type ("FOLLOW_UP", "SYSTEM_INFO", "DATA_QUERY")
            new_examples: List of example questions
        """
        if intent not in self.intent_examples:
            self.intent_examples[intent] = []
        
        self.intent_examples[intent].extend(new_examples)
        
        # Recompute embeddings for new examples
        for example in new_examples:
            embedding = self.embedding_service.embed_text(example)
            self._example_embeddings[intent].append((example, embedding))
        
        print(f"✅ Added {len(new_examples)} examples for {intent}")


# Singleton instance
_classifier_instance = None

def get_intent_classifier() -> IntentClassifier:
    """Get or create the intent classifier singleton."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance
