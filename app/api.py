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

    # 🔐 SAFE ACCESS — never index LLM output directly
    decision_type = decision.get("decision")

    # ---- OUT OF SCOPE ----
    if decision_type == "OUT_OF_SCOPE":
        return QueryResponse(decision="OUT_OF_SCOPE")

    # ---- NEED MORE INFO ----
    if decision_type == "NEED_MORE_INFO":
        return QueryResponse(
            decision="NEED_MORE_INFO",
            clarification_question=decision.get(
                "clarification_question",
                "Could you provide more details?"
            )
        )

    # ---- EXECUTE QUERY ----
    if decision_type == "EXECUTE":
        params = decision.get("params")

        # Extra safety: params must exist
        if not params:
            return QueryResponse(
                decision="ERROR",
                summary="Missing query parameters. Please rephrase your question."
            )

        sql = WEATHER_SINGLE_PATH_TS_SQL
        validate_sql(sql)

        data = execute_query(sql, {
            "forecast_init": params.get("initialization"),
            "seasonal_init": "2025-12-04 00:00+00",
            "location": params.get("location"),
            "variable": params.get("variable"),
            "ensemble_path": params.get("ensemble_path")
        })

        if req.session_id:
            save_context(req.session_id, decision)

        return QueryResponse(
            decision="EXECUTE",
            data=data,
            summary=f"Returned {len(data)} hourly values for {params.get('variable')}."
        )

    # ---- HARD FALLBACK (NO 500s EVER) ----
    return QueryResponse(
        decision="ERROR",
        summary="Unable to interpret the request. Please rephrase."
    )
