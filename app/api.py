from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse
from app.llm.intent_resolver import IntentResolver
from app.context.memory import (
    get_or_create_context, 
    save_context, 
    ConversationTurn,
    SessionContext
)
from app.db.executor import execute_query
from app.queries.sql_templates import *  # Import all SQL templates
from app.queries.query_registry import QUERY_REGISTRY
from app.utils.sql_guard import validate_sql
from app.utils.intent_helpers import resolve_project, resolve_location

router = APIRouter()
resolver = IntentResolver()

# Maximum number of data rows to store in context for follow-up reference
MAX_DATA_PREVIEW_ROWS = 5


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    # 🔍 Log input
    print("📥 Incoming question:", req.question)
    print("🧠 Session ID:", req.session_id)

    # Get or create session context
    context = None
    if req.session_id:
        context = get_or_create_context(req.session_id)
        print("📚 Context last_params:", context.last_params)
        print("📚 Context history length:", len(context.history))

    # Resolve intent with context
    decision = resolver.resolve(req.question, context)

    # 🔍 Log raw LLM output
    print("🤖 LLM decision:", decision)

    decision_type = decision.get("decision")

    # ---- OUT OF SCOPE ----
    if decision_type == "OUT_OF_SCOPE":
        # Save turn even for out of scope (helps with conversation flow)
        if req.session_id and context:
            turn = ConversationTurn(
                question=req.question,
                summary="Question was out of scope for this API."
            )
            context.add_turn(turn)
            save_context(req.session_id, context)
        
        message = decision.get("message", "This question is out of scope for this API.")
        similarity_score = decision.get("similarity_score")
        
        response = QueryResponse(
            decision="OUT_OF_SCOPE",
            message=message,
            similarity_score=similarity_score
        )
        print("📤 API response:", response.dict())
        return response

    # ---- NEED MORE INFO ----
    if decision_type == "NEED_MORE_INFO": 
        clarification = decision.get(
            "clarification_question",
            "Could you provide more details?"
        )
        
        # Save turn with pending clarification
        if req.session_id and context:
            turn = ConversationTurn(
                question=req.question,
                summary=f"Asked for clarification: {clarification}"
            )
            context.add_turn(turn)
            save_context(req.session_id, context)
        
        response = QueryResponse(
            decision="NEED_MORE_INFO",
            clarification_question=clarification
        )
        print("📤 API response:", response.dict())
        return response

    # ---- EXECUTE QUERY ----
    if decision_type == "EXECUTE":
        query_id = decision.get("query_id")
        params = decision.get("params")
        similarity_score = decision.get("similarity_score")
        confidence = decision.get("confidence")
        
        # Log confidence information
        if similarity_score is not None:
            print(f"📊 Similarity score: {similarity_score:.3f}, Confidence: {confidence}")
            
            # If confidence is low, we could optionally ask for confirmation
            # For now, we'll proceed but log it
            if confidence == "low":
                print(f"⚠️  Low confidence match ({similarity_score:.3f}). Proceeding with execution.")

        if not query_id:
            raise HTTPException(status_code=400, detail="Missing query_id in LLM decision.")
        if query_id not in QUERY_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Unknown query_id: {query_id}")

        query_info = QUERY_REGISTRY[query_id]
        sql_template_name = query_info["sql_template_name"]
        sql = globals()[sql_template_name]  # Get SQL template by name

        if not params:
            params = {}

        # Validate and prepare parameters
        # Also check context.last_params for missing required params (follow-up support)
        prepared_params = {}
        missing_params = []
        context_last_params = context.last_params if context else {}
        
        for param_name, param_info in query_info["parameters"].items():
            # Special handling for project_name and location to keep behavior deterministic
            if param_name == "project_name":
                # Always resolve via helper (currently always 'ercot_generic')
                prepared_params[param_name] = resolve_project(context_last_params)
                continue
            
            if param_name == "location":
                raw_location = params.get("location")
                prepared_params[param_name] = resolve_location(
                    raw_from_llm=raw_location,
                    last_params=context_last_params,
                )
                continue

            if param_name in params:
                param_value = params[param_name]
                # Check if the LLM flagged this param as needing more info
                if param_value == "NEED_MORE_INFO":
                    # Try to get from context first
                    if param_name in context_last_params:
                        prepared_params[param_name] = context_last_params[param_name]
                    elif param_info.get("required"):
                        missing_params.append((param_name, param_info['description']))
                    elif "default" in param_info:
                        prepared_params[param_name] = param_info["default"]
                else:
                    prepared_params[param_name] = param_value
            elif param_name in context_last_params:
                # Parameter not in LLM response but available in context - reuse it
                prepared_params[param_name] = context_last_params[param_name]
            elif param_info.get("required"):
                # Required parameter is missing entirely
                missing_params.append((param_name, param_info['description']))
            elif "default" in param_info:
                prepared_params[param_name] = param_info["default"]
        
        # If any required params are missing, ask for clarification
        if missing_params:
            descriptions = "; ".join([f"{p[0]}: {p[1]}" for p in missing_params])
            clarification = f"I need the following information to execute this query: {descriptions}"
            
            # Save turn
            if req.session_id and context:
                turn = ConversationTurn(
                    question=req.question,
                    query_id=query_id,
                    summary=f"Missing params: {[p[0] for p in missing_params]}"
                )
                context.add_turn(turn)
                save_context(req.session_id, context)
            
            response = QueryResponse(
                decision="NEED_MORE_INFO",
                clarification_question=clarification
            )
            print("📤 API response:", response.dict())
            return response
        
        validate_sql(sql)

        # Execute the query
        data = execute_query(sql, prepared_params)

        # Save successful turn with full context
        if req.session_id and context:
            # Store a preview of the data for follow-up reference
            data_preview = data[:MAX_DATA_PREVIEW_ROWS] if data else None
            
            turn = ConversationTurn(
                question=req.question,
                query_id=query_id,
                params=prepared_params,
                summary=f"Returned {len(data)} records from {query_id}.",
                data_preview=data_preview
            )
            context.add_turn(turn)
            save_context(req.session_id, context)

        response = QueryResponse(
            decision="EXECUTE",
            query_id=query_id,
            sql=sql.strip(),
            params=prepared_params,
            data=data,
            summary=f"Successfully executed query '{query_id}' and returned {len(data)} records.",
            similarity_score=similarity_score,
            confidence=confidence
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