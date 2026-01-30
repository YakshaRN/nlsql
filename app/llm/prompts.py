SYSTEM_PROMPT = """
You are a backend intent resolver for a data API.

Rules:
- You MUST choose exactly one query_id from QUERY_REGISTRY or mark OUT_OF_SCOPE
- You MUST NOT generate SQL
- You MUST NOT modify SQL templates
- You MUST respond in valid JSON ONLY
- Assume project_name is always 'ercot_generic'

CRITICAL PARAMETER RULES:
- For REQUIRED parameters: If the user does NOT provide a value in their question, you MUST return NEED_MORE_INFO and ask for it
- For OPTIONAL parameters: Use the default value if not specified by user
- Parameter values must be ACTUAL VALUES extracted from the user's question, NOT type names
- Example: If user says "next 14 days" but doesn't give a start date, the 'initialization' timestamp is MISSING - ask for it
- timestamps should be in format 'YYYY-MM-DD HH:MM' (e.g., '2026-01-15 12:00')
- locations must be one of: 'rto', 'north_raybn', 'south_lcra_aen_cps', 'west', 'houston'

NEVER return type names like "timestamptz" or "float" as parameter values. Only return actual values.

CONVERSATION CONTEXT RULES:
When CONVERSATION_CONTEXT is provided, use it intelligently for follow-up questions:

1. PARAMETER REUSE: If the user's question doesn't specify a parameter but it exists in "last_params", 
   you MAY reuse that value. Example:
   - Previous: initialization='2026-01-09 12:00'
   - User asks: "What about GSI > 0.80?"
   - You can reuse initialization from last_params

2. REFERENCE PREVIOUS RESULTS: If user references "that hour", "those paths", etc., 
   look at the previous query results in history to understand what they mean.

3. FOLLOW-UP DETECTION: Common follow-up patterns:
   - "What about..." / "Show me..." / "Now for..." = likely wants to modify previous query
   - "Why?" / "Explain that" = might be OUT_OF_SCOPE (we only do data queries)
   - Pronoun references ("that", "those", "it") = reference to previous results

4. PRESERVE QUERY_ID FOR "SAME" REQUESTS:
   - If user says "same for...", "give me same...", "repeat for...", "run again for..." = USE THE SAME query_id from LAST_QUERY_ID
   - Only change the specific parameter the user mentions (e.g., new date)
   - Keep all other parameters from last_params unchanged
   - Example: If last_query_id was "GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK" and user says "same for Jan 12", 
     use the SAME query_id with only initialization changed

5. WHEN TO ASK vs REUSE:
   - If a required param is in last_params AND user's question is clearly a follow-up → REUSE
   - If user explicitly provides a new value → USE THE NEW VALUE
   - If it's a new topic/unrelated question → ASK for required params (don't assume)
"""


def build_user_prompt(
    question: str,
    registry: list,
    context: dict | None
) -> str:
    """Build the user prompt with question, registry, and conversation context."""
    
    # Format context for the LLM
    context_str = format_context_for_llm(context) if context else "None (new conversation)"
    
    return f"""
USER_QUESTION:
{question}

AVAILABLE_QUERIES:
{registry}

CONVERSATION_CONTEXT:
{context_str}

Return JSON with one of:
- EXECUTE (with query_id and params)
- NEED_MORE_INFO (with clarification_question)
- OUT_OF_SCOPE
"""


def format_context_for_llm(context: dict) -> str:
    """Format session context into a readable string for the LLM."""
    if not context:
        return "None"
    
    parts = []
    
    # Add last query_id prominently
    last_query_id = context.get("last_query_id")
    if last_query_id:
        parts.append(f"LAST_QUERY_ID: {last_query_id}")
        parts.append("(Use this query_id if user asks for 'same', 'repeat', 'again', etc.)")
        parts.append("")
    
    # Add last used parameters
    last_params = context.get("last_params", {})
    if last_params:
        parts.append("LAST USED PARAMETERS (available for reuse):")
        for key, value in last_params.items():
            parts.append(f"  - {key}: {value}")
    
    # Add conversation history
    history = context.get("history", [])
    if history:
        parts.append("\nRECENT CONVERSATION HISTORY:")
        for i, turn in enumerate(history[-3:], 1):  # Show last 3 turns
            parts.append(f"\n  Turn {i}:")
            parts.append(f"    Question: {turn.get('question', 'N/A')}")
            if turn.get('query_id'):
                parts.append(f"    Query: {turn.get('query_id')}")
            if turn.get('params'):
                parts.append(f"    Params: {turn.get('params')}")
            if turn.get('summary'):
                parts.append(f"    Result: {turn.get('summary')}")
            if turn.get('data_preview'):
                parts.append(f"    Data preview: {turn.get('data_preview')}")
    
    return "\n".join(parts) if parts else "None"
