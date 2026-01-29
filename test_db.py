from sqlalchemy import text
from app.db.connection import ENGINE

with ENGINE.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchone())

