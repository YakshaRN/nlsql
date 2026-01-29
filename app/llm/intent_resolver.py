from .bedrock_client import BedrockClient
from .prompts import SYSTEM_PROMPT, build_user_prompt
from app.queries.registry import QUERY_REGISTRY

class IntentResolver:
    def __init__(self, llm=None):
        self.llm = llm or BedrockClient()

    def resolve(self, question: str, context: dict | None) -> dict:
        prompt = self._build_prompt(question, context)
        raw = self.llm.invoke(SYSTEM_PROMPT, prompt)

        print("🔍 LLM RAW RESULT:", raw)

        # ---- NORMALIZE SHAPE ----

        # Case 1: already normalized
        if "decision" in raw:
            return raw

        # Case 2: nested decision (EXECUTE / OUT_OF_SCOPE / NEED_MORE_INFO)
        for key in ("EXECUTE", "OUT_OF_SCOPE", "NEED_MORE_INFO"):
            if key in raw:
                normalized = {
                    "decision": key
                }

                if isinstance(raw[key], dict):
                    normalized.update(raw[key])

                return normalized

        # Case 3: unknown output
        return {
            "decision": "ERROR",
            "reason": "Unrecognized LLM output format",
            "raw": raw
        }

