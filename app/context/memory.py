"""
Session-based conversation memory for follow-up questions.

Stores:
- Conversation history (last N turns)
- Last used parameters (for reuse in follow-ups)
- Last query results summary
"""

from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

MAX_HISTORY_TURNS = 25  # Keep last 25 conversation turns for extended sessions


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    question: str
    query_id: Optional[str] = None
    sql: Optional[str] = None
    params: dict = field(default_factory=dict)
    summary: Optional[str] = None
    data_preview: Optional[list] = None  # First few rows of results
    explanation: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionContext:
    """Full context for a session."""
    history: list = field(default_factory=list)  # List of ConversationTurn dicts
    last_params: dict = field(default_factory=dict)  # Most recent params for reuse
    last_query_id: Optional[str] = None  # Most recent query_id for follow-ups
    last_sql: Optional[str] = None  # Most recent SQL for follow-ups
    
    def add_turn(self, turn: ConversationTurn):
        """Add a conversation turn, keeping only the last N turns."""
        self.history.append(asdict(turn))
        if len(self.history) > MAX_HISTORY_TURNS:
            self.history = self.history[-MAX_HISTORY_TURNS:]
        
        # Update last_params with any new params from this turn
        if turn.params:
            self.last_params.update(turn.params)
        
        # Track last query_id for follow-up questions
        if turn.query_id:
            self.last_query_id = turn.query_id
        
        # Track last SQL for follow-up questions
        if turn.sql:
            self.last_sql = turn.sql
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "history": self.history,
            "last_params": self.last_params,
            "last_query_id": self.last_query_id,
            "last_sql": self.last_sql
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionContext":
        """Create from dictionary."""
        ctx = cls()
        ctx.history = data.get("history", [])
        ctx.last_params = data.get("last_params", {})
        ctx.last_query_id = data.get("last_query_id")
        return ctx


# In-memory session store
SESSION_STORE: dict[str, SessionContext] = {}


def get_context(session_id: str) -> Optional[SessionContext]:
    """Retrieve session context."""
    return SESSION_STORE.get(session_id)


def save_context(session_id: str, context: SessionContext):
    """Save session context."""
    SESSION_STORE[session_id] = context


def get_or_create_context(session_id: str) -> SessionContext:
    """Get existing context or create a new one."""
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = SessionContext()
    return SESSION_STORE[session_id]


def clear_context(session_id: str):
    """Clear a session's context."""
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]
