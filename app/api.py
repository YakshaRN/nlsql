from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse
from app.llm.intent_resolver import IntentResolver
from app.context.memory import get_context, save_context
from app.db.executor import execute_query
from app.queries.sql_templates import WEATHER_SINGLE_PATH_TS_SQL
from app.utils.sql_guard import validate_sql

router = APIRouter()
resolver = IntentResolver()

@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    context = get_context(req.session_id) if req.session_id else None
    decision = resolver.resolve(req.question, context)

    if decision["decision"] == "OUT_OF_SCOPE":
        return QueryResponse(decision="OUT_OF_SCOPE")

    if decision["decision"] == "NEED_MORE_INFO":
        return QueryResponse(
            decision="NEED_MORE_INFO",
            clarification_question=decision["clarification_question"]
        )

    params = decision["params"]

    sql = WEATHER_SINGLE_PATH_TS_SQL
    validate_sql(sql)

    data = execute_query(sql, {
        "forecast_init": params["initialization"],
        "seasonal_init": "2025-12-04 00:00+00",
        "location": params["location"],
        "variable": params["variable"],
        "ensemble_path": params["ensemble_path"]
    })

    save_context(req.session_id, decision)

    return QueryResponse(
        decision="EXECUTE",
        data=data,
        summary=f"Returned {len(data)} hourly values for {params['variable']}."
    )
