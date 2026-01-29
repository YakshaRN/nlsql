from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None

class QueryResponse(BaseModel):
    decision: str
    data: list | None = None
    summary: str | None = None
    clarification_question: str | None = None
