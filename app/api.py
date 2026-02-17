from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse
from app.llm.sql_generator import SQLGenerator
from app.context.memory import (
    get_or_create_context,
    save_context,
    ConversationTurn,
    SessionContext
)
from app.db.executor import execute_query
from app.utils.sql_validator import validate_generated_sql

router = APIRouter()
generator = SQLGenerator()

MAX_DATA_PREVIEW_ROWS = 5
QUERY_TIMEOUT_SECONDS = 30


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    print("📥 Incoming question:", req.question)
    print("🧠 Session ID:", req.session_id)

    # Get or create session context
    context = None
    context_dict = None
    if req.session_id:
        context = get_or_create_context(req.session_id)
        context_dict = context.to_dict()
        print("📚 Context history length:", len(context.history))
        if context.last_sql:
            print("📚 Last SQL available for follow-up")

    # ── Generate SQL from natural language ──
    result = generator.generate(req.question, context_dict)
    print("🤖 Generator result:", result)

    decision = result.get("decision")

    # ── SYSTEM_INFO (project/location/capability questions) ──
    if decision == "SYSTEM_INFO":
        if req.session_id and context:
            turn = ConversationTurn(
                question=req.question,
                summary="System information question."
            )
            context.add_turn(turn)
            save_context(req.session_id, context)

        return QueryResponse(
            decision="SYSTEM_INFO",
            message=result.get("message", ""),
            info_type=result.get("info_type")
        )

    # ── CANNOT_ANSWER ──
    if decision == "CANNOT_ANSWER":
        if req.session_id and context:
            turn = ConversationTurn(
                question=req.question,
                summary="Question could not be answered."
            )
            context.add_turn(turn)
            save_context(req.session_id, context)

        return QueryResponse(
            decision="CANNOT_ANSWER",
            message=result.get("message", "I couldn't generate a query for this question."),
            assumptions=result.get("assumptions")
        )

    # ── ERROR ──
    if decision == "ERROR":
        return QueryResponse(
            decision="ERROR",
            message=result.get("message", "An error occurred.")
        )

    # ── EXECUTE (dynamic SQL generated) ──
    if decision == "EXECUTE":
        sql = result.get("sql", "")
        explanation = result.get("explanation", "")
        assumptions = result.get("assumptions", "")

        # ── Safety validation ──
        validation = validate_generated_sql(sql)

        if not validation["valid"]:
            print(f"🛡️ SQL validation FAILED: {validation['error']}")

            if req.session_id and context:
                turn = ConversationTurn(
                    question=req.question,
                    summary=f"SQL validation failed: {validation['error']}"
                )
                context.add_turn(turn)
                save_context(req.session_id, context)

            return QueryResponse(
                decision="ERROR",
                message=f"Generated SQL failed safety validation: {validation['error']}",
                sql=sql
            )

        # Use sanitized SQL
        safe_sql = validation["sanitized_sql"]

        # Log warnings
        for warning in validation.get("warnings", []):
            print(f"⚠️ SQL warning: {warning}")

        print(f"✅ SQL validated. Executing...")
        print(f"📝 SQL: {safe_sql[:200]}...")

        # ── Execute the query ──
        try:
            data = execute_query(safe_sql, {})
        except Exception as e:
            error_msg = str(e)
            print(f"❌ SQL execution error: {error_msg}")

            if req.session_id and context:
                turn = ConversationTurn(
                    question=req.question,
                    sql=safe_sql,
                    summary=f"SQL execution error: {error_msg[:100]}"
                )
                context.add_turn(turn)
                save_context(req.session_id, context)

            return QueryResponse(
                decision="ERROR",
                message=f"Query execution failed: {error_msg[:200]}",
                sql=safe_sql,
                explanation=explanation,
                assumptions=assumptions
            )

        # ── Success! Save context ──
        if req.session_id and context:
            data_preview = data[:MAX_DATA_PREVIEW_ROWS] if data else None

            turn = ConversationTurn(
                question=req.question,
                sql=safe_sql,
                summary=f"Returned {len(data)} records.",
                explanation=explanation,
                data_preview=data_preview
            )
            context.add_turn(turn)
            save_context(req.session_id, context)

        # Build summary
        record_count = len(data) if data else 0
        summary = f"Successfully executed and returned {record_count} records."

        return QueryResponse(
            decision="EXECUTE",
            sql=safe_sql,
            data=data,
            summary=summary,
            explanation=explanation,
            assumptions=assumptions
        )

    # ── FALLBACK ──
    return QueryResponse(
        decision="ERROR",
        summary="Unable to interpret the request. Please rephrase."
    )
