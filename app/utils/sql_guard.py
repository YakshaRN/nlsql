def validate_sql(sql: str):
    forbidden = ["insert", "update", "delete", "drop", ";"]
    lower = sql.lower()
    for word in forbidden:
        if word in lower:
            raise ValueError("Unsafe SQL detected")
