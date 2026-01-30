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

MAX_HISTORY_TURNS = 5  # Keep last 5 conversation turns


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    question: str
    query_id: Optional[str] = None
    params: dict = field(default_factory=dict)
    summary: Optional[str] = None
    data_preview: Optional[list] = None  # First few rows of results
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionContext:
    """Full context for a session."""
    history: list = field(default_factory=list)  # List of ConversationTurn dicts
    last_params: dict = field(default_factory=dict)  # Most recent params for reuse
    
    def add_turn(self, turn: ConversationTurn):
        """Add a conversation turn, keeping only the last N turns."""
        self.history.append(asdict(turn))
        if len(self.history) > MAX_HISTORY_TURNS:
            self.history = self.history[-MAX_HISTORY_TURNS:]
        
        # Update last_params with any new params from this turn
        if turn.params:
            self.last_params.update(turn.params)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "history": self.history,
            "last_params": self.last_params
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionContext":
        """Create from dictionary."""
        ctx = cls()
        ctx.history = data.get("history", [])
        ctx.last_params = data.get("last_params", {})
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
