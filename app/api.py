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
        missing_params = []
        
        for param_name, param_info in query_info["parameters"].items():
            if param_name in params:
                param_value = params[param_name]
                # Check if the LLM flagged this param as needing more info
                if param_value == "NEED_MORE_INFO":
                    if param_info.get("required"):
                        missing_params.append((param_name, param_info['description']))
                    elif "default" in param_info:
                        prepared_params[param_name] = param_info["default"]
                else:
                    prepared_params[param_name] = param_value
            elif param_info.get("required"):
                # If a required parameter is missing entirely, track it
                missing_params.append((param_name, param_info['description']))
            elif "default" in param_info:
                prepared_params[param_name] = param_info["default"]
        
        # If any required params are missing or flagged as NEED_MORE_INFO, ask for clarification
        if missing_params:
            param_list = ", ".join([f"'{p[0]}'" for p in missing_params])
            descriptions = "; ".join([f"{p[0]}: {p[1]}" for p in missing_params])
            response = QueryResponse(
                decision="NEED_MORE_INFO",
                clarification_question=f"I need the following information to execute this query: {descriptions}"
            )
            print("📤 API response:", response.dict())
            return response
        
        validate_sql(sql)

        # DRY RUN MODE: Return query + params without executing
        if req.dry_run:
            response = QueryResponse(
                decision="EXECUTE",
                query_id=query_id,
                sql=sql.strip(),
                params=prepared_params,
                summary=f"Dry run: matched query '{query_id}' with {len(prepared_params)} parameters."
            )
            print("📤 API response (dry run):", response.dict())
            return response

        # EXECUTE MODE: Run the query
        data = execute_query(sql, prepared_params)

        if req.session_id:
            save_context(req.session_id, decision)

        response = QueryResponse(
            decision="EXECUTE",
            query_id=query_id,
            sql=sql.strip(),
            params=prepared_params,
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
