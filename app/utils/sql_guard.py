def validate_sql(sql: str):
    """
    Safety check for SQL templates.

    Rules:
    - Must be SELECT-only
    - No modifying statements
    """

    sql_lower = sql.strip().lower()

    # Must start with select
    if not sql_lower.startswith("select"):
        raise ValueError("Only SELECT statements are allowed")

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
