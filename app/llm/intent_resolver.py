from app.llm.bedrock_client import BedrockClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.queries.query_registry import QUERY_REGISTRY
import json

class IntentResolver:
    def __init__(self, llm=None):
        self.llm = llm or BedrockClient()
        self.query_registry = QUERY_REGISTRY

    def _build_system_prompt(self) -> str:
        # Dynamically generate the EXECUTE decision format based on the query registry
        execute_formats = []
        for query_id, query_info in self.query_registry.items():
            params_str = ", ".join([f'"{param}": "{details.get("type", "string")}"' for param, details in query_info["parameters"].items()])
            execute_formats.append(f"""
{{
  "decision": "EXECUTE",
  "query_id": "{query_id}",
  "params": {{
    {params_str}
  }}
}}""")
        
        # Add descriptions to the registry for the LLM
        registry_for_llm = {
            qid: {
                "description": qinfo["description"],
                "parameters": {
                    pname: pinfo["description"] for pname, pinfo in qinfo["parameters"].items()
                }
            }
            for qid, qinfo in self.query_registry.items()
        }

        return SYSTEM_PROMPT + "\n\n" + \
               f"QUERY_REGISTRY:\n{json.dumps(registry_for_llm, indent=2)}\n\n" + \
               "Valid response formats:\n\n" + \
               "1) OUT OF SCOPE\n{\"decision\": \"OUT_OF_SCOPE\"}\n\n" + \
               "2) NEED MORE INFO\n{\n  \"decision\": \"NEED_MORE_INFO\",\n  \"clarification_question\": \"string\"\n}\n\n" + \
               "3) EXECUTE (choose one of the following formats based on query_id)\n" + \
               "\n".join(execute_formats)

    def resolve(self, question: str, context: dict | None) -> dict:
        system_prompt = self._build_system_prompt()
        user_prompt = build_user_prompt(question, list(self.query_registry.keys()), context)
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
