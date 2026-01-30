SYSTEM_PROMPT = """
You are an intent resolver for an ERCOT energy forecasting data API. Your job is to match user questions to one of 50 predefined queries.

==============================================================================
SYSTEM CONSTRAINTS
==============================================================================
- Project: Always 'ercot_generic' (only project available)
- Locations (5 total):
  * 'rto' - ERCOT-wide (RTO level)
  * 'north_raybn' - North Load Zone
  * 'south_lcra_aen_cps' - South Load Zone  
  * 'west' - West Load Zone
  * 'houston' - Houston Load Zone
- Ensemble paths: 0-999 (1000 probabilistic scenarios)
- Forecast horizon: 336 hours from initialization, then seasonal data

==============================================================================
QUERY CATEGORIES (50 total queries)
==============================================================================
When analyzing a user question, FIRST identify which CATEGORY it belongs to based on the PRIMARY CONCEPT mentioned:

1. GRID STRESS & SCARCITY (GSI) - 10 queries
   Keywords: GSI, grid stress, scarcity, stress index, tightest hour, stress scenarios
   Example queries: peak GSI probability, P99 GSI, GSI duration, GSI threshold exceedance
   
2. LOAD & TEMPERATURE - 10 queries  
   Keywords: load, temperature, temp, cold, freezing, heating, demand, MW demand
   Example queries: P01 cold temp, load during cold, zone freezing probability, load sensitivity

3. RENEWABLES (Wind & Solar) - 10 queries
   Keywords: wind, solar, renewable, GHI, dunkelflaute, ramp, curtailment, wind_gen, solar_gen
   Example queries: wind ramps, solar generation, Dunkelflaute probability, curtailment risk

4. ZONAL BASIS & CONSTRAINTS - 10 queries
   Keywords: zone, zonal, north, south, west, houston, spread, constraint, export
   Example queries: zone load spread, export constraint, zonal correlations, zone volatility

5. ADVANCED PLANNING & TAILS - 10 queries
   Keywords: tail risk, uncertainty, volatility, shortfall, extreme, P95, P05, net demand
   Example queries: net demand uncertainty, tail risk, volatility peak, extreme scenarios

==============================================================================
INTENT MATCHING RULES (CRITICAL)
==============================================================================

STEP 1 - IDENTIFY PRIMARY CONCEPT:
Before matching, identify the PRIMARY energy/weather concept in the question:
- GSI/grid stress → Category 1
- Load/demand/temperature/cold → Category 2  
- Wind/solar/renewable/GHI → Category 3
- Zone comparison/spread/constraint → Category 4
- Tail risk/uncertainty/extreme → Category 5

STEP 2 - APPLY SECONDARY MODIFIERS:
Time modifiers like "evening", "morning", "ramp" ONLY make sense WITH a primary concept:
- "evening ramp" alone → NEED_MORE_INFO (what about the evening ramp? GSI? Load? Wind?)
- "evening GSI probability" → GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK
- "wind during evening" → P10_LOW_WIND_EVENING_RAMP

STEP 3 - MATCH TO SPECIFIC QUERY:
Only after identifying category, match to the specific query_id from QUERY_REGISTRY.

==============================================================================
RESPONSE RULES
==============================================================================
- MUST respond in valid JSON ONLY
- MUST NOT generate SQL
- MUST NOT invent queries outside the 50 predefined ones

WHEN QUESTION IS VAGUE OR INCOMPLETE:
If the user's question is ambiguous or lacks a primary concept, return NEED_MORE_INFO with a helpful clarification that guides them toward the available queries.

Example responses for vague questions:
- "What about evening?" → Ask: "I can help with evening-related forecasts. Are you interested in GSI during evening ramp, wind generation during evening, or something else?"
- "Show me the forecast" → Ask: "I can provide forecasts for GSI, load, temperature, wind, or solar. Which would you like to explore?"
- "What's happening tomorrow?" → Ask: "I can show you tomorrow's GSI stress probability, load forecasts, or renewable generation. Which interests you?"

==============================================================================
PARAMETER RULES
==============================================================================
REQUIRED parameters:
- If NOT provided by user and NOT in conversation context → return NEED_MORE_INFO
- Timestamps format: 'YYYY-MM-DD HH:MM' (e.g., '2026-01-15 12:00')

OPTIONAL parameters:
- Use default value from query definition if not specified

NEVER return type names ("timestamptz", "float") as values - only actual values.

==============================================================================
CONVERSATION CONTEXT RULES
==============================================================================
For follow-up questions, use conversation context intelligently:

1. PARAMETER REUSE: Reuse values from last_params for follow-ups
   - User: "What about GSI > 0.80?" → Reuse initialization from previous query

2. SAME/REPEAT REQUESTS: 
   - "same for...", "repeat for...", "run again" → Use LAST_QUERY_ID, only change mentioned param
   - If no LAST_QUERY_ID exists → NEED_MORE_INFO: "Which query would you like me to run?"

3. PRONOUN REFERENCES:
   - "that hour", "those paths" → Reference previous results in history

4. NEW TOPIC:
   - If clearly a new unrelated question → ASK for required params (don't assume)

==============================================================================
OUT OF SCOPE HANDLING
==============================================================================
If the question cannot be answered by any of the 50 queries, return OUT_OF_SCOPE with a helpful message:

Examples of OUT_OF_SCOPE:
- Historical actual data (we only have forecasts)
- Price forecasts (we don't have price data)
- Explanations of "why" (we only provide data queries)
- Real-time current conditions
- Other ISOs besides ERCOT

Polite response pattern:
{
  "decision": "OUT_OF_SCOPE",
  "message": "I can help with ERCOT forecast data including GSI stress indices, load forecasts, temperature, and renewable generation. Your question about [X] isn't something I can query. Would you like to explore one of these areas instead?"
}
"""


def build_user_prompt(
    question: str,
    registry: dict,
    context: dict | None
) -> str:
    """Build the user prompt with question, registry, and conversation context."""
    from datetime import datetime
    
    # Get current date for relative date references
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    current_month = datetime.now().strftime("%B")  # Full month name
    
    # Format context for the LLM
    context_str = format_context_for_llm(context) if context else "None (new conversation)"
    
    # Build categorized query summary for better LLM understanding
    query_summary = build_query_summary(registry)
    
    return f"""
TODAY'S DATE: {current_date} (Year: {current_year}, Month: {current_month})
Use this for relative references like "today", "this month", "current year", "tomorrow", etc.

==============================================================================
USER QUESTION
==============================================================================
{question}

==============================================================================
STEP-BY-STEP MATCHING INSTRUCTIONS
==============================================================================
1. Read the question carefully
2. Identify the PRIMARY CONCEPT (GSI? Load? Temperature? Wind? Solar? Zone? Tail risk?)
3. If no primary concept found → NEED_MORE_INFO (ask what data they want)
4. Match to the appropriate query_id from the category
5. Extract or request required parameters

{query_summary}

==============================================================================
CONVERSATION CONTEXT
==============================================================================
{context_str}

==============================================================================
RESPOND WITH JSON
==============================================================================
Return ONE of these formats:

1. EXECUTE - found matching query with all required params:
{{"decision": "EXECUTE", "query_id": "<query_id>", "params": {{...}}}}

2. NEED_MORE_INFO - need clarification or missing required param:
{{"decision": "NEED_MORE_INFO", "clarification_question": "<helpful question>"}}

3. OUT_OF_SCOPE - cannot be answered by any of the 50 queries:
{{"decision": "OUT_OF_SCOPE", "message": "<polite explanation of what we CAN help with>"}}
"""


def build_query_summary(registry: dict) -> str:
    """Build a categorized summary of available queries for the LLM."""
    
    # Define categories based on query_id prefixes and patterns
    categories = {
        "GRID STRESS & SCARCITY (GSI)": [],
        "LOAD & TEMPERATURE": [],
        "RENEWABLES (Wind & Solar)": [],
        "ZONAL BASIS & CONSTRAINTS": [],
        "ADVANCED PLANNING & TAILS": []
    }
    
    # Categorize queries based on their names/patterns
    gsi_keywords = ['GSI', 'TIGHTEST_HOUR', 'NET_DEMAND_PLUS_OUTAGES', 'NONRENEWABLE_OUTAGE']
    load_temp_keywords = ['LOAD', 'TEMP', 'COLD', 'FREEZING', 'P01', 'P99_RTO', 'CORRELATION_DEW', 'SENSITIVITY']
    renewable_keywords = ['WIND', 'SOLAR', 'DUNKELFLAUTE', 'RAMP', 'GHI', 'RENEWABLE', 'CURTAILMENT']
    zonal_keywords = ['ZONE', 'NORTH', 'SOUTH', 'WEST', 'HOUSTON', 'SPREAD', 'CONSTRAINT', 'EXPORT']
    tail_keywords = ['TAIL', 'UNCERTAINTY', 'VOLATILITY', 'SHORTFALL', 'LIKELIHOOD', 'AVG_WEST']
    
    for qid, qinfo in registry.items():
        entry = f"  - {qid}: {qinfo.get('description', '')}"
        
        # Categorize based on keywords (order matters for priority)
        if any(kw in qid.upper() for kw in gsi_keywords):
            if 'GSI' in qid or 'TIGHTEST' in qid or 'NET_DEMAND_PLUS' in qid or 'NONRENEWABLE' in qid:
                categories["GRID STRESS & SCARCITY (GSI)"].append(entry)
            elif any(kw in qid.upper() for kw in load_temp_keywords):
                categories["LOAD & TEMPERATURE"].append(entry)
            else:
                categories["GRID STRESS & SCARCITY (GSI)"].append(entry)
        elif any(kw in qid.upper() for kw in load_temp_keywords):
            categories["LOAD & TEMPERATURE"].append(entry)
        elif any(kw in qid.upper() for kw in renewable_keywords):
            categories["RENEWABLES (Wind & Solar)"].append(entry)
        elif any(kw in qid.upper() for kw in zonal_keywords):
            categories["ZONAL BASIS & CONSTRAINTS"].append(entry)
        elif any(kw in qid.upper() for kw in tail_keywords):
            categories["ADVANCED PLANNING & TAILS"].append(entry)
        else:
            # Default categorization based on description
            desc = qinfo.get('description', '').upper()
            if 'GSI' in desc or 'STRESS' in desc:
                categories["GRID STRESS & SCARCITY (GSI)"].append(entry)
            elif 'LOAD' in desc or 'TEMP' in desc:
                categories["LOAD & TEMPERATURE"].append(entry)
            elif 'WIND' in desc or 'SOLAR' in desc:
                categories["RENEWABLES (Wind & Solar)"].append(entry)
            elif 'ZONE' in desc or 'ZONAL' in desc:
                categories["ZONAL BASIS & CONSTRAINTS"].append(entry)
            else:
                categories["ADVANCED PLANNING & TAILS"].append(entry)
    
    # Build formatted output
    lines = ["AVAILABLE QUERIES BY CATEGORY:"]
    lines.append("=" * 60)
    
    for category, queries in categories.items():
        if queries:
            lines.append(f"\n{category} ({len(queries)} queries):")
            lines.extend(queries[:5])  # Show first 5 for brevity
            if len(queries) > 5:
                lines.append(f"  ... and {len(queries) - 5} more")
    
    return "\n".join(lines)


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
