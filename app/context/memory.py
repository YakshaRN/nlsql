SESSION_STORE = {}

def get_context(session_id: str):
    return SESSION_STORE.get(session_id)

def save_context(session_id: str, context: dict):
    SESSION_STORE[session_id] = context
