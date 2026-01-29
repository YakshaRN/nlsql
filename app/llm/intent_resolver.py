from app.llm.bedrock_client import BedrockClient

SYSTEM_PROMPT = """
You are an intent classifier for a weather and energy forecasting system.

Your job:
- Decide whether the user's question can be answered using predefined SQL queries.
- Extract parameters when possible.

Allowed decisions:
- OUT_OF_SCOPE
- NEED_MORE_INFO
- EXECUTE

You MUST respond in valid JSON only.

Valid response formats:

1) OUT OF SCOPE
{"decision": "OUT_OF_SCOPE"}

2) NEED MORE INFO
{
  "decision": "NEED_MORE_INFO",
  "clarification_question": "string"
}

3) EXECUTE
{
  "decision": "EXECUTE",
  "query_id": "WEATHER_SINGLE_PATH_TS",
  "params": {
    "initialization": "YYYY-MM-DD HH:MM",
    "location": "rto | north_raybn | south_lcra_aen_cps | west | houston",
    "variable": "temp_2m | dew_2m | wind_10m_mps | ghi | wind_100m_mps | ghi_gen | temp_2m_gen",
    "ensemble_path": 0
  }
}
"""

class IntentResolver:
    def __init__(self, llm=None):
        self.llm = llm or BedrockClient()

    def _build_prompt(self, question: str, context: dict | None) -> str:
        """
        Build the user prompt given question + optional context
        """
        prompt = f"User question:\n{question}\n"

        if context:
            prompt += f"\nConversation context:\n{context}\n"

        prompt += "\nClassify the intent and extract parameters."

        return prompt

    def resolve(self, question: str, context: dict | None) -> dict:
        prompt = self._build_prompt(question, context)
        raw = self.llm.invoke(SYSTEM_PROMPT, prompt)

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
