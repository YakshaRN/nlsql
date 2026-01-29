from sqlalchemy.sql import text
from .connection import ENGINE

def execute_query(sql: str, params: dict):
    with ENGINE.connect() as conn:
        result = conn.execute(text(sql), params)
        return [dict(row._mapping) for row in result.fetchall()]
