"""
Dynamic SQL generator using LLM.

Translates natural language questions into PostgreSQL queries
by providing the LLM with full database schema and query rules.
"""

import json
import re
from app.llm.bedrock_client import BedrockClient
from app.config.system_info import get_system_info_for_type


# Load the system prompt from file
def _load_system_prompt() -> str:
    """Load the SQL generation system prompt."""
    import os
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'newcase_prompt.txt')
    prompt_path = os.path.normpath(prompt_path)
    
    with open(prompt_path, 'r') as f:
        return f.read()


# System info question patterns (handled before LLM call)
SYSTEM_INFO_PATTERNS = {
    'project': ['what project', 'which project', 'projects do you', 'project available',
                'project information', 'tell me about project', 'what data do you have'],
    'locations': ['what location', 'which location', 'locations served', 'location available',
                 'what zones', 'which zones', 'what regions', 'which regions', 'regions do you',
                 'what areas', 'which areas'],
    'capabilities': ['what can you', 'what do you', 'help me with', 'capabilities',
                    'what kind of', 'what type of'],
}


class SQLGenerator:
    """
    Generates SQL dynamically from natural language using LLM.
    
    Architecture:
        User Question → LLM (with schema + rules) → SQL + Explanation
    """
    
    def __init__(self, llm=None):
        self.llm = llm or BedrockClient()
        self.system_prompt = _load_system_prompt()
    
    def _detect_system_info(self, question: str) -> dict | None:
        """Check if question is about system capabilities (not a data query)."""
        question_lower = question.lower()
        
        for category, patterns in SYSTEM_INFO_PATTERNS.items():
            if any(pattern in question_lower for pattern in patterns):
                message = get_system_info_for_type(category)
                return {
                    "decision": "SYSTEM_INFO",
                    "message": message,
                    "info_type": category
                }
        return None
    
    def _build_user_prompt(self, question: str, context: dict | None) -> str:
        """Build the user prompt with question and conversation context."""
        parts = []
        
        # Add conversation history for follow-ups
        if context:
            history = context.get("history", [])
            last_sql = context.get("last_sql")
            
            if history:
                parts.append("## CONVERSATION HISTORY (for follow-up context)")
                for turn in history[-5:]:  # Last 5 turns
                    parts.append(f"\nUser: {turn.get('question', 'N/A')}")
                    if turn.get('sql'):
                        parts.append(f"SQL used: {turn['sql'][:200]}...")
                    if turn.get('summary'):
                        parts.append(f"Result: {turn['summary']}")
            
            if last_sql:
                parts.append(f"\n## LAST SQL QUERY (for reference if this is a follow-up)")
                parts.append(f"```sql\n{last_sql}\n```")
        
        # Add the current question
        parts.append(f"\n## USER QUESTION\n{question}")
        
        # Add response format instructions
        parts.append("""
## RESPONSE FORMAT
You MUST respond in valid JSON with this exact structure:
{
    "explanation": "Brief plain-English explanation of what the query does",
    "sql": "The complete PostgreSQL query",
    "assumptions": "Any assumptions made (e.g., default location, time range)"
}

CRITICAL RULES:
- Return ONLY valid JSON, no markdown, no code blocks around the JSON
- The "sql" field must contain a complete, executable PostgreSQL query
- If the question is ambiguous, still generate the best query with assumptions noted
- If the question truly cannot be answered with the available data, return:
  {"explanation": "Cannot answer", "sql": "", "assumptions": "Reason why this cannot be answered with the available data"}
- For follow-up questions (e.g., "same for Houston", "now with 7 days"), modify the last SQL query accordingly
""")
        
        return "\n".join(parts)
    
    def generate(self, question: str, context: dict | None = None) -> dict:
        """
        Generate SQL from natural language question.
        
        Args:
            question: User's natural language question
            context: Conversation context with history
            
        Returns:
            Dict with keys: decision, sql, explanation, assumptions, message
        """
        # Step 1: Check for system info questions
        system_info = self._detect_system_info(question)
        if system_info:
            return system_info
        
        # Step 2: Build prompt and call LLM
        user_prompt = self._build_user_prompt(question, context)
        
        try:
            result = self.llm.invoke(self.system_prompt, user_prompt)
            print(f"🤖 LLM raw result: {result}")
        except json.JSONDecodeError:
            # LLM returned non-JSON, try to extract
            return {
                "decision": "ERROR",
                "message": "Failed to parse LLM response. Please rephrase your question."
            }
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return {
                "decision": "ERROR",
                "message": f"LLM error: {str(e)}"
            }
        
        # Step 3: Parse LLM response
        sql = result.get("sql", "")
        explanation = result.get("explanation", "")
        assumptions = result.get("assumptions", "")
        
        # Step 4: Check if LLM said it can't answer
        if not sql or not sql.strip():
            return {
                "decision": "CANNOT_ANSWER",
                "message": explanation or "I couldn't generate a query for this question.",
                "assumptions": assumptions
            }
        
        # Step 5: Return the generated SQL for validation and execution
        return {
            "decision": "EXECUTE",
            "sql": sql.strip(),
            "explanation": explanation,
            "assumptions": assumptions
        }
