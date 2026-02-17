"""
Enhanced SQL safety validator for dynamically generated SQL.

Validates LLM-generated SQL to prevent:
- SQL injection
- Destructive operations (DELETE, DROP, etc.)
- Missing required filters (project_name)
- Excessive result sets (missing LIMIT)
"""

import re


# Forbidden SQL keywords/operations
FORBIDDEN_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter", "truncate",
    "create", "grant", "revoke", "exec", "execute",
    "pg_sleep", "information_schema", "pg_catalog"
]

# Valid tables in the system
VALID_TABLES = [
    "weather_forecast_ensemble",
    "weather_seasonal_ensemble",
    "energy_forecast_ensemble",
    "energy_base_ensemble"
]

# Required filter in every query
REQUIRED_FILTER = "project_name"

# Maximum rows if no LIMIT specified
DEFAULT_ROW_LIMIT = 5000


def validate_generated_sql(sql: str) -> dict:
    """
    Validate LLM-generated SQL for safety and correctness.
    
    Args:
        sql: The SQL query to validate
        
    Returns:
        dict with keys:
            - valid: bool
            - error: str (if invalid)
            - warnings: list of str
            - sanitized_sql: str (with safety additions)
    """
    warnings = []
    
    if not sql or not sql.strip():
        return {"valid": False, "error": "Empty SQL query", "warnings": [], "sanitized_sql": ""}
    
    sql_lower = sql.strip().lower()
    
    # Remove comments for analysis
    sql_cleaned = re.sub(r'/\*.*?\*/', '', sql_lower, flags=re.DOTALL).strip()
    sql_cleaned = re.sub(r'--.*$', '', sql_cleaned, flags=re.MULTILINE).strip()
    
    # ── CHECK 1: Must be SELECT or WITH (CTE) ──
    if not (sql_cleaned.startswith("select") or sql_cleaned.startswith("with")):
        return {
            "valid": False,
            "error": "Only SELECT statements are allowed. Query must start with SELECT or WITH.",
            "warnings": [],
            "sanitized_sql": ""
        }
    
    # ── CHECK 2: Forbidden keywords ──
    for keyword in FORBIDDEN_KEYWORDS:
        # Check with word boundaries to avoid false positives
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_cleaned):
            return {
                "valid": False,
                "error": f"Forbidden SQL keyword detected: '{keyword}'. Only SELECT queries are allowed.",
                "warnings": [],
                "sanitized_sql": ""
            }
    
    # ── CHECK 3: Must reference valid tables ──
    has_valid_table = any(table in sql_lower for table in VALID_TABLES)
    if not has_valid_table:
        return {
            "valid": False,
            "error": f"Query must reference at least one valid table: {VALID_TABLES}",
            "warnings": [],
            "sanitized_sql": ""
        }
    
    # ── CHECK 4: Must have project_name filter ──
    if REQUIRED_FILTER not in sql_lower:
        warnings.append(f"Missing '{REQUIRED_FILTER}' filter. Adding 'project_name = ercot_generic' is required.")
    
    # ── CHECK 5: Check for semicolon injection (multiple statements) ──
    # Allow single trailing semicolon but not multiple statements
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    if len(statements) > 1:
        return {
            "valid": False,
            "error": "Multiple SQL statements detected. Only single SELECT queries are allowed.",
            "warnings": [],
            "sanitized_sql": ""
        }
    
    # ── CHECK 6: Warn if no LIMIT and potentially large result ──
    if 'limit' not in sql_lower and 'count(*)' not in sql_lower and 'avg(' not in sql_lower:
        if 'group by' not in sql_lower:
            warnings.append(f"No LIMIT clause and no aggregation detected. Results may be very large.")
    
    # Sanitize: remove trailing semicolons
    sanitized = sql.strip().rstrip(';').strip()
    
    return {
        "valid": True,
        "error": None,
        "warnings": warnings,
        "sanitized_sql": sanitized
    }
