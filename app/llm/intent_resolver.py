from app.llm.bedrock_client import BedrockClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.embedding_service import get_embedding_service
from app.queries.query_registry import QUERY_REGISTRY
from app.context.memory import SessionContext
import json


class IntentResolver:
    def __init__(self, llm=None, top_k_candidates: int = 5, min_similarity: float = 0.5):
        """
        Initialize the IntentResolver with hybrid approach.
        
        Args:
            llm: LLM client (defaults to BedrockClient)
            top_k_candidates: Number of top candidates to retrieve via embeddings
            min_similarity: Minimum similarity threshold for candidate retrieval
        """
        self.llm = llm or BedrockClient()
        self.query_registry = QUERY_REGISTRY
        self.embedding_service = get_embedding_service()
        self.top_k_candidates = top_k_candidates
        self.min_similarity = min_similarity

    def _build_registry_for_llm(self, candidate_query_ids: list = None) -> dict:
        """
        Build a detailed registry representation for the LLM.
        
        Args:
            candidate_query_ids: If provided, only include these query IDs.
                                If None, include all queries.
        """
        registry_for_llm = {}
        query_ids_to_include = candidate_query_ids if candidate_query_ids else self.query_registry.keys()
        
        for qid in query_ids_to_include:
            if qid not in self.query_registry:
                continue
                
            qinfo = self.query_registry[qid]
            params_info = {}
            for pname, pinfo in qinfo["parameters"].items():
                is_required = pinfo.get("required", False)
                param_desc = pinfo["description"]
                if is_required:
                    param_desc = f"[REQUIRED] {param_desc}"
                else:
                    default = pinfo.get("default", "none")
                    param_desc = f"[OPTIONAL, default={default}] {param_desc}"
                params_info[pname] = param_desc
            
            registry_for_llm[qid] = {
                "description": qinfo["description"],
                "parameters": params_info
            }
        return registry_for_llm

    def _build_system_prompt(self, candidate_queries: list = None) -> str:
        """
        Build the system prompt with query registry information.
        
        Args:
            candidate_queries: List of (query_id, similarity_score, metadata) tuples.
                             If provided, only include these candidates.
        """
        if candidate_queries:
            # Hybrid approach: only include top-K candidates
            candidate_ids = [q[0] for q in candidate_queries]
            registry_for_llm = self._build_registry_for_llm(candidate_ids)
            
            # Build candidate summary with similarity scores
            candidate_summary = "TOP CANDIDATE QUERIES (retrieved via semantic similarity):\n"
            for query_id, similarity, metadata in candidate_queries:
                confidence = self.embedding_service.get_confidence_level(similarity)
                candidate_summary += f"\n  - {query_id} (similarity: {similarity:.3f}, confidence: {confidence}):\n"
                candidate_summary += f"    {metadata.get('description', '')}\n"
                if metadata.get('example_question'):
                    candidate_summary += f"    Example: {metadata['example_question']}\n"
            
            response_format = f"""
==============================================================================
{candidate_summary}
==============================================================================
FULL DETAILS OF CANDIDATE QUERIES:
==============================================================================
""" + json.dumps(registry_for_llm, indent=2) + """

==============================================================================
RESPONSE FORMAT EXAMPLES
==============================================================================
1) EXECUTE - matched query with all required params available:
{{"decision": "EXECUTE", "query_id": "GSI_PEAK_PROBABILITY_14_DAYS", "params": {{"initialization": "2026-01-15 12:00", "gsi_threshold": 0.60, "days_ahead": 14}}, "similarity_score": 0.85}}

2) NEED_MORE_INFO - question is valid but missing required parameter:
{{"decision": "NEED_MORE_INFO", "clarification_question": "What forecast initialization timestamp should I use? Please provide a date/time like '2026-01-15 12:00'."}}

3) NEED_MORE_INFO - question is vague, needs primary concept:
{{"decision": "NEED_MORE_INFO", "clarification_question": "I can help with GSI stress indices, load/temperature forecasts, or renewable generation. Which area interests you?"}}

4) OUT_OF_SCOPE - not answerable by any of the candidate queries:
{{"decision": "OUT_OF_SCOPE", "message": "I specialize in ERCOT forecast data including GSI, load, temperature, and renewables. I can't help with [X], but I'd be happy to show you forecast data in one of these areas."}}

CRITICAL REMINDERS:
- You MUST select one of the candidate queries above (or return OUT_OF_SCOPE if none match)
- params must contain ACTUAL VALUES (not type names like 'timestamptz')
- Timestamps format: 'YYYY-MM-DD HH:MM'
- Reuse values from LAST USED PARAMETERS for follow-up questions
- Include similarity_score in EXECUTE responses
"""
        else:
            # Fallback: include all queries (original approach)
            registry_for_llm = self._build_registry_for_llm()
            response_format = """
==============================================================================
FULL QUERY REGISTRY (50 queries with parameters)
==============================================================================
""" + json.dumps(registry_for_llm, indent=2) + """

==============================================================================
RESPONSE FORMAT EXAMPLES
==============================================================================
1) EXECUTE - matched query with all required params available:
{"decision": "EXECUTE", "query_id": "GSI_PEAK_PROBABILITY_14_DAYS", "params": {"initialization": "2026-01-15 12:00", "gsi_threshold": 0.60, "days_ahead": 14}}

2) NEED_MORE_INFO - question is valid but missing required parameter:
{"decision": "NEED_MORE_INFO", "clarification_question": "What forecast initialization timestamp should I use? Please provide a date/time like '2026-01-15 12:00'."}

3) NEED_MORE_INFO - question is vague, needs primary concept:
{"decision": "NEED_MORE_INFO", "clarification_question": "I can help with GSI stress indices, load/temperature forecasts, or renewable generation. Which area interests you?"}

4) OUT_OF_SCOPE - not answerable by any of the 50 queries:
{"decision": "OUT_OF_SCOPE", "message": "I specialize in ERCOT forecast data including GSI, load, temperature, and renewables. I can't help with [X], but I'd be happy to show you forecast data in one of these areas."}

CRITICAL REMINDERS:
- params must contain ACTUAL VALUES (not type names like 'timestamptz')
- Timestamps format: 'YYYY-MM-DD HH:MM'
- Reuse values from LAST USED PARAMETERS for follow-up questions
- ALWAYS identify the PRIMARY CONCEPT before matching to a query
"""
        return SYSTEM_PROMPT + response_format

    def resolve(self, question: str, context: SessionContext | dict | None) -> dict:
        """
        Resolve user question to a query decision using hybrid approach.
        
        Args:
            question: The user's natural language question
            context: Either a SessionContext object or dict with conversation history
            
        Returns:
            Decision dict with 'decision' key and relevant data, including similarity scores
        """
        # Step 1: Retrieve top-K candidates using embeddings
        print(f"🔍 Retrieving top-{self.top_k_candidates} similar queries via embeddings...")
        candidate_queries = self.embedding_service.find_similar_queries(
            question,
            top_k=self.top_k_candidates,
            min_similarity=self.min_similarity
        )
        
        if not candidate_queries:
            # No candidates found - likely out of scope
            return {
                "decision": "OUT_OF_SCOPE",
                "message": "I couldn't find any matching queries for your question. I specialize in ERCOT forecast data including GSI, load, temperature, and renewable generation.",
                "similarity_score": 0.0
            }
        
        # Log top candidates
        print(f"📊 Top candidates:")
        for query_id, similarity, metadata in candidate_queries:
            print(f"   - {query_id}: {similarity:.3f} - {metadata.get('description', '')[:60]}...")
        
        top_similarity = candidate_queries[0][1]
        confidence = self.embedding_service.get_confidence_level(top_similarity)
        print(f"🎯 Top match similarity: {top_similarity:.3f} (confidence: {confidence})")
        
        # Step 2: Build system prompt with only top-K candidates
        system_prompt = self._build_system_prompt(candidate_queries)
        
        # Convert SessionContext to dict for the prompt
        context_dict = None
        if context:
            if isinstance(context, SessionContext):
                context_dict = context.to_dict()
            else:
                context_dict = context
        
        # Build candidate registry (only top-K) for user prompt
        candidate_registry = {q[0]: self.query_registry[q[0]] for q in candidate_queries}
        
        # Pass candidate registry instead of full registry
        user_prompt = build_user_prompt(
            question, 
            candidate_registry,  # Pass only candidate queries
            context_dict
        )
        
        # Step 3: LLM makes final decision from candidates
        raw = self.llm.invoke(system_prompt, user_prompt)

        print("🔍 LLM RAW RESULT:", raw)

        # ---- NORMALIZE OUTPUT ----

        # Case 1: already normalized
        if "decision" in raw:
            # Add similarity information
            if raw["decision"] == "EXECUTE":
                # Find the similarity score for the selected query
                selected_query_id = raw.get("query_id")
                if selected_query_id:
                    for qid, sim, _ in candidate_queries:
                        if qid == selected_query_id:
                            raw["similarity_score"] = sim
                            raw["confidence"] = confidence
                            break
            return raw

        # Case 2: nested decision
        for key in ("EXECUTE", "OUT_OF_SCOPE", "NEED_MORE_INFO"):
            if key in raw:
                normalized = {"decision": key}
                if isinstance(raw[key], dict):
                    normalized.update(raw[key])
                # Add similarity info if EXECUTE
                if key == "EXECUTE" and "query_id" in normalized:
                    selected_query_id = normalized["query_id"]
                    for qid, sim, _ in candidate_queries:
                        if qid == selected_query_id:
                            normalized["similarity_score"] = sim
                            normalized["confidence"] = confidence
                            break
                return normalized

        # Case 3: unknown shape - fallback to top candidate if similarity is high
        if top_similarity >= 0.75:
            print(f"⚠️  LLM output unclear, but high similarity ({top_similarity:.3f}). Using top candidate.")
            top_query_id = candidate_queries[0][0]
            return {
                "decision": "EXECUTE",
                "query_id": top_query_id,
                "params": {},
                "similarity_score": top_similarity,
                "confidence": confidence,
                "note": "LLM output was unclear, but high similarity match found"
            }

        # Case 4: unknown shape and low similarity
        return {
            "decision": "ERROR",
            "reason": "Unrecognized LLM output format",
            "raw": raw,
            "top_candidates": [(q[0], q[1]) for q in candidate_queries[:3]],
            "similarity_score": top_similarity
        }
