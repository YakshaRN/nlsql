from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse
from app.llm.intent_resolver import IntentResolver
from app.context.memory import get_context, save_context
from app.db.executor import execute_query
from app.queries.sql_templates import *  # Import all SQL templates
from app.queries.query_registry import QUERY_REGISTRY
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
        query_id = decision.get("query_id")
        params = decision.get("params")

        if not query_id:
            raise HTTPException(status_code=400, detail="Missing query_id in LLM decision.")
        if query_id not in QUERY_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Unknown query_id: {query_id}")

        query_info = QUERY_REGISTRY[query_id]
        sql_template_name = query_info["sql_template_name"]
        sql = globals()[sql_template_name] # Get SQL template by name

        if not params:
            params = {}

        # Validate and prepare parameters
        prepared_params = {}
        for param_name, param_info in query_info["parameters"].items():
            if param_name in params:
                prepared_params[param_name] = params[param_name]
            elif param_info.get("required"):
                # If a required parameter is missing, ask for more info
                response = QueryResponse(
                    decision="NEED_MORE_INFO",
                    clarification_question=f"I need the '{param_name}' to execute this query. {param_info['description']}"
                )
                print("📤 API response:", response.dict())
                return response
            elif "default" in param_info:
                prepared_params[param_name] = param_info["default"]
        
        validate_sql(sql)

        data = execute_query(sql, prepared_params)

        if req.session_id:
            save_context(req.session_id, decision)

        response = QueryResponse(
            decision="EXECUTE",
            data=data,
            summary=f"Successfully executed query '{query_id}' and returned {len(data)} records."
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
