from app.llm.bedrock_client import BedrockClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.queries.query_registry import QUERY_REGISTRY
from app.context.memory import SessionContext
import json


class IntentResolver:
    def __init__(self, llm=None):
        self.llm = llm or BedrockClient()
        self.query_registry = QUERY_REGISTRY

    def _build_registry_for_llm(self) -> dict:
        """Build a detailed registry representation for the LLM."""
        registry_for_llm = {}
        for qid, qinfo in self.query_registry.items():
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

    def _build_system_prompt(self) -> str:
        """Build the system prompt with query registry information."""
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
        Resolve user question to a query decision.
        
        Args:
            question: The user's natural language question
            context: Either a SessionContext object or dict with conversation history
            
        Returns:
            Decision dict with 'decision' key and relevant data
        """
        system_prompt = self._build_system_prompt()
        
        # Convert SessionContext to dict for the prompt
        context_dict = None
        if context:
            if isinstance(context, SessionContext):
                context_dict = context.to_dict()
            else:
                context_dict = context
        
        # Pass full registry dict for categorized summary
        user_prompt = build_user_prompt(
            question, 
            self.query_registry,  # Pass full dict, not just keys
            context_dict
        )
        
        raw = self.llm.invoke(system_prompt, user_prompt)

        print("🔍 LLM RAW RESULT:", raw)

        # ---- NORMALIZE OUTPUT ----

        # Case 1: already normalized
        if "decision" in raw:
            return raw

        # Case 2: nested decision
        for key in ("EXECUTE", "OUT_OF_SCOPE", "NEED_MORE_INFO"):
            if key in raw:
                normalized = {"decision": key}
                if isinstance(raw[key], dict):
                    normalized.update(raw[key])
                return normalized

        # Case 3: unknown shape
        return {
            "decision": "ERROR",
            "reason": "Unrecognized LLM output format",
            "raw": raw
        }
