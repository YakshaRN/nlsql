from app.llm.bedrock_client import BedrockClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.embedding_service import get_embedding_service
from app.queries.query_registry import QUERY_REGISTRY
from app.context.memory import SessionContext
from app.config.initialization_config import get_initialization_for_query
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

    def _detect_follow_up_query(self, question: str, context: SessionContext | dict | None) -> dict | None:
        """
        Detect if this is a follow-up query that wants to reuse the last query with modifications.
        
        Uses smart detection:
        1. Check for follow-up keywords ("same", "again", etc.)
        2. Check if CORE CONCEPT changed (solar→wind, GSI→load)
        3. Only treat as follow-up if concept is SAME or compatible
        
        Args:
            question: The user's question
            context: Session context with last query info
            
        Returns:
            Decision dict if follow-up detected, None otherwise
        """
        if not context:
            return None
        
        # Extract last_query_id from context
        last_query_id = None
        if isinstance(context, SessionContext):
            last_query_id = context.last_query_id
        elif isinstance(context, dict):
            last_query_id = context.get("last_query_id")
        
        if not last_query_id:
            return None
        
        question_lower = question.lower()
        
        # Follow-up detection patterns (case-insensitive)
        follow_up_patterns = [
            # Direct reuse
            "same", "again", "repeat", "also", 
            # Now variations
            "now for", "now with", "now use", "now change",
            # But variations
            "but with", "but for", "but using", "but instead",
            # Change variations
            "change to", "change threshold", "change the",
            # Time references
            "this time", "next time",
            # Run variations
            "run again", "rerun", "do it again",
            # Explicit same
            "same query", "same data", "previous query", 
            "give me same", "show me same",
            # Additional patterns
            "instead of", "rather than", "instead", " instead"
        ]
        
        # Check if any follow-up pattern exists
        has_follow_up_keyword = any(pattern in question_lower for pattern in follow_up_patterns)
        
        if not has_follow_up_keyword:
            return None
        
        # CRITICAL: Check if core concept changed (concept switching)
        # If user mentions a different primary concept, treat as NEW query
        concept_switch_keywords = {
            'gsi': ['gsi', 'grid stress', 'scarcity'],
            'load': ['load', 'demand'],
            'temperature': ['temperature', 'temp', 'cold', 'hot', 'freezing'],
            'wind': ['wind'],
            'solar': ['solar'],
            'renewable': ['renewable', 'dunkelflaute'],
            'zone': ['zone', 'zonal', 'north', 'south', 'west', 'houston'],
        }
        
        # Determine concept of last query
        last_query_concept = None
        for concept, keywords in concept_switch_keywords.items():
            if any(kw in last_query_id.lower() for kw in keywords):
                last_query_concept = concept
                break
        
        # Check if current question mentions a DIFFERENT concept
        if last_query_concept:
            for concept, keywords in concept_switch_keywords.items():
                if concept != last_query_concept:
                    # Check if question explicitly mentions this different concept
                    if any(kw in question_lower for kw in keywords):
                        print(f"⚠️  Concept switch detected: {last_query_concept} → {concept}")
                        print(f"   Treating as NEW query (not follow-up)")
                        return None  # Not a follow-up, concept changed!
        
        print(f"🔄 Follow-up query detected! Reusing last query: {last_query_id}")
        print(f"   Same concept maintained: {last_query_concept or 'unknown'}")
        
        # Return a decision to reuse the last query
        return {
            "is_follow_up": True,
            "last_query_id": last_query_id,
            "last_concept": last_query_concept,
            "hint": "This is a follow-up query. Reuse the last query_id and last_params, only change parameters mentioned in the question."
        }
    
    def _ensure_correct_initialization(self, decision: dict) -> dict:
        """
        Ensure initialization parameters use correct fixed timestamps.
        
        This method automatically fills in or corrects initialization parameters
        based on the query_id to use the correct data timestamps instead of 
        current date.
        
        Args:
            decision: The decision dict with query_id and params
            
        Returns:
            Updated decision dict with correct initialization values
        """
        if decision.get("decision") != "EXECUTE":
            return decision
            
        query_id = decision.get("query_id")
        if not query_id:
            return decision
            
        params = decision.get("params", {})
        
        # Get the correct initialization values for this query
        correct_init_params = get_initialization_for_query(query_id)
        
        # Update or add the initialization parameters
        for param_name, param_value in correct_init_params.items():
            if param_name not in params or not params[param_name]:
                # Parameter missing or empty - add it
                params[param_name] = param_value
                print(f"✅ Auto-filled {param_name} = '{param_value}' for {query_id}")
            elif params[param_name] != param_value:
                # Parameter exists but has wrong value - correct it
                old_value = params[param_name]
                params[param_name] = param_value
                print(f"🔧 Corrected {param_name} from '{old_value}' to '{param_value}' for {query_id}")
        
        decision["params"] = params
        return decision

    def resolve(self, question: str, context: SessionContext | dict | None) -> dict:
        """
        Resolve user question to a query decision using hybrid approach.
        
        Args:
            question: The user's natural language question
            context: Either a SessionContext object or dict with conversation history
            
        Returns:
            Decision dict with 'decision' key and relevant data, including similarity scores
        """
        # Step 0: Check if this is a follow-up query
        follow_up_info = self._detect_follow_up_query(question, context)
        
        # Step 1: Retrieve top-K candidates using embeddings
        print(f"🔍 Retrieving top-{self.top_k_candidates} similar queries via embeddings...")
        candidate_queries = self.embedding_service.find_similar_queries(
            question,
            top_k=self.top_k_candidates,
            min_similarity=self.min_similarity
        )
        
        # If this is a follow-up query, ensure the last query is included as top candidate
        if follow_up_info and follow_up_info.get("last_query_id"):
            last_qid = follow_up_info["last_query_id"]
            if last_qid in self.query_registry:
                # Check if last_query_id is already in candidates
                candidate_ids = [q[0] for q in candidate_queries] if candidate_queries else []
                
                if last_qid not in candidate_ids:
                    # Add it as the top candidate with high similarity
                    metadata = {
                        "description": self.query_registry[last_qid].get("description", ""),
                        "is_follow_up_match": True
                    }
                    # If no candidates at all, create list with just this one
                    if not candidate_queries:
                        candidate_queries = [(last_qid, 0.95, metadata)]
                        print(f"🔄 No semantic matches found, but follow-up detected!")
                        print(f"   Using last query '{last_qid}' as sole candidate")
                    else:
                        # Add to existing candidates as top
                        candidate_queries = [(last_qid, 0.95, metadata)] + candidate_queries
                        print(f"🔄 Added last query '{last_qid}' as top candidate for follow-up")
        
        if not candidate_queries:
            # No candidates found - check if user might have meant a follow-up
            # Extract context info for helpful suggestion
            last_query_id = None
            if context:
                if isinstance(context, SessionContext):
                    last_query_id = context.last_query_id
                elif isinstance(context, dict):
                    last_query_id = context.get("last_query_id")
            
            # If context exists, provide helpful follow-up suggestion
            if last_query_id:
                return {
                    "decision": "OUT_OF_SCOPE",
                    "message": f"I couldn't find any matching queries for your question. If you wanted to modify the previous query ({last_query_id}), try phrasing it like:\n\n• 'same for [new value]'\n• 'repeat with [new parameter]'\n• 'now with [change]'\n• 'also for [modification]'\n\nOtherwise, I specialize in ERCOT forecast data including GSI, load, temperature, wind, solar, and renewable generation.",
                    "similarity_score": 0.0,
                    "suggestion": "use_follow_up_keywords"
                }
            else:
                # No context - truly out of scope
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
        # Filter out any candidates whose IDs are not in the current registry
        candidate_queries = [q for q in candidate_queries if q[0] in self.query_registry]
        
        if not candidate_queries:
            return {
                "decision": "OUT_OF_SCOPE",
                "message": "I couldn't find any matching queries for your question.",
                "similarity_score": 0.0
            }
        
        candidate_registry = {q[0]: self.query_registry[q[0]] for q in candidate_queries}
        
        # Pass candidate registry instead of full registry
        user_prompt = build_user_prompt(
            question, 
            candidate_registry,  # Pass only candidate queries
            context_dict,
            follow_up_info  # Pass follow-up detection info
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
                    # Auto-fill initialization parameters with correct values
                    raw = self._ensure_correct_initialization(raw)
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
                    # Auto-fill initialization parameters with correct values
                    normalized = self._ensure_correct_initialization(normalized)
                return normalized

        # Case 3: unknown shape - fallback to top candidate if similarity is high
        if top_similarity >= 0.75:
            print(f"⚠️  LLM output unclear, but high similarity ({top_similarity:.3f}). Using top candidate.")
            top_query_id = candidate_queries[0][0]
            result = {
                "decision": "EXECUTE",
                "query_id": top_query_id,
                "params": {},
                "similarity_score": top_similarity,
                "confidence": confidence,
                "note": "LLM output was unclear, but high similarity match found"
            }
            # Auto-fill initialization parameters with correct values
            result = self._ensure_correct_initialization(result)
            return result

        # Case 4: unknown shape and low similarity
        return {
            "decision": "ERROR",
            "reason": "Unrecognized LLM output format",
            "raw": raw,
            "top_candidates": [(q[0], q[1]) for q in candidate_queries[:3]],
            "similarity_score": top_similarity
        }
