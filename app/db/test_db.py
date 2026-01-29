from app.db.connection import ENGINE

with ENGINE.connect() as conn:
    result = conn.execute("SELECT 1;")
    print(result.fetchone())
