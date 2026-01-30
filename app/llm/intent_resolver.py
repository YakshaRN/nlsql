from app.llm.bedrock_client import BedrockClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.queries.query_registry import QUERY_REGISTRY
from app.context.memory import SessionContext
import json


class IntentResolver:
    def __init__(self, llm=None):
        self.llm = llm or BedrockClient()
        self.query_registry = QUERY_REGISTRY

    def _build_system_prompt(self) -> str:
        """Build the system prompt with query registry information."""
        # Build detailed registry info for the LLM with required/optional markers
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

        return SYSTEM_PROMPT + "\n\n" + \
               f"QUERY_REGISTRY:\n{json.dumps(registry_for_llm, indent=2)}\n\n" + \
               "RESPONSE FORMATS:\n\n" + \
               "1) OUT OF SCOPE - question not related to any query:\n" + \
               '{"decision": "OUT_OF_SCOPE"}\n\n' + \
               "2) NEED MORE INFO - required parameter missing and cannot be inferred from context:\n" + \
               '{"decision": "NEED_MORE_INFO", "clarification_question": "What initialization/start timestamp should I use for this query?"}\n\n' + \
               "3) EXECUTE - all required params available (from question, context, or defaults):\n" + \
               '{"decision": "EXECUTE", "query_id": "GSI_PEAK_PROBABILITY_14_DAYS", "params": {"initialization": "2026-01-15 12:00", "gsi_threshold": 0.60, "days_ahead": 14}}\n\n' + \
               "NOTE: params must contain ACTUAL VALUES, not type names. Reuse values from LAST USED PARAMETERS when appropriate for follow-ups."

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
        
        user_prompt = build_user_prompt(
            question, 
            list(self.query_registry.keys()), 
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
