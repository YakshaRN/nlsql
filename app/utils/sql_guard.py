def validate_sql(sql: str):
    """
    Safety check for SQL templates.

    Rules:
    - Must be SELECT-only (or CTE starting with WITH)
    - No modifying statements
    """

    sql_lower = sql.strip().lower()
    
    # Remove leading comments (/* ... */ or -- style)
    import re
    sql_cleaned = re.sub(r'/\*.*?\*/', '', sql_lower, flags=re.DOTALL).strip()
    sql_cleaned = re.sub(r'--.*$', '', sql_cleaned, flags=re.MULTILINE).strip()

    # Must start with SELECT or WITH (for CTEs)
    if not (sql_cleaned.startswith("select") or sql_cleaned.startswith("with")):
        raise ValueError("Only SELECT statements (or CTEs with WITH) are allowed")

    # Explicitly forbidden operations
    forbidden = [
        " drop ",
        " delete ",
        " update ",
        " insert ",
        " alter ",
        " truncate ",
        " create ",
        " grant ",
        " revoke "
    ]

    for word in forbidden:
        if word in sql_lower:
            raise ValueError("Unsafe SQL detected")

    return True
