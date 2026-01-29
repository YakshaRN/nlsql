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
    # 🔍 Log input
    print("📥 Incoming question:", req.question)
    print("🧠 Session ID:", req.session_id)

    context = get_context(req.session_id) if req.session_id else None
    decision = resolver.resolve(req.question, context)

    # 🔍 Log raw LLM output
    print("🤖 LLM decision:", decision)

    decision_type = decision.get("decision")

    # ---- OUT OF SCOPE ----
    if decision_type == "OUT_OF_SCOPE":
        response = QueryResponse(decision="OUT_OF_SCOPE")
        print("📤 API response:", response.dict())
        return response

    # ---- NEED MORE INFO ----
    if decision_type == "NEED_MORE_INFO":
        response = QueryResponse(
            decision="NEED_MORE_INFO",
            clarification_question=decision.get(
                "clarification_question",
                "Could you provide more details?"
            )
        )
        print("📤 API response:", response.dict())
        return response

    # ---- EXECUTE QUERY ----
    if decision_type == "EXECUTE":
        params = decision.get("params")

        if not params:
            response = QueryResponse(
                decision="ERROR",
                summary="Missing query parameters. Please rephrase."
            )
            print("📤 API response:", response.dict())
            return response

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

        response = QueryResponse(
            decision="EXECUTE",
            data=data,
            summary=f"Returned {len(data)} hourly values for {params.get('variable')}."
        )

        print("📤 API response:", response.dict())
        return response

    # ---- FALLBACK ----
    response = QueryResponse(
        decision="ERROR",
        summary="Unable to interpret the request. Please rephrase."
    )
    print("📤 API response:", response.dict())
    return response
