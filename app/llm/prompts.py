SYSTEM_PROMPT = """
You are a backend intent resolver for a data API.

Rules:
- You MUST choose exactly one query_id from QUERY_REGISTRY or mark OUT_OF_SCOPE
- You MUST NOT generate SQL
- You MUST NOT modify SQL templates
- You MUST ask for missing required parameters
- You MUST respond in valid JSON ONLY
- Assume project_name is always 'ercot_generic'
"""

def build_user_prompt(
    question: str,
    registry: list,
    context: dict | None
) -> str:
    return f"""
USER_QUESTION:
{question}

AVAILABLE_QUERIES:
{registry}

CONVERSATION_CONTEXT:
{context if context else "None"}

Return JSON with one of:
- EXECUTE
- NEED_MORE_INFO
- OUT_OF_SCOPE
"""
