from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None
    dry_run: bool = False  # If True, return query + params instead of executing

class QueryResponse(BaseModel):
    decision: str
    data: list | None = None
    summary: str | None = None
    clarification_question: str | None = None
    # Dry run fields
    query_id: str | None = None
    sql: str | None = None
    params: dict | None = None
