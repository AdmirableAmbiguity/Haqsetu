"""
Session-based conversation memory for HaqSetu / Vachan Setu.
Tracks multi-turn context, active intent, selected scheme, and extracted citizen profile.
"""

import time
import threading
from typing import Dict, Any, List, Optional

class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.updated_at = time.time()
        self.active_section: str = "haqguide"  # "haqguide", "scheme_finder", "scheme_expert"
        self.active_scheme: Optional[Dict[str, Any]] = None
        self.user_profile: Dict[str, Any] = {}
        self.pending_clarification: Optional[str] = None
        self.history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, intent: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.updated_at = time.time()
        self.history.append({
            "role": role,
            "content": content,
            "intent": intent,
            "metadata": metadata or {},
            "timestamp": time.time()
        })
        # Keep maximum 20 conversation turns per session
        if len(self.history) > 20:
            self.history = self.history[-20:]

    def update_profile(self, new_data: Dict[str, Any]):
        self.updated_at = time.time()
        for k, v in new_data.items():
            if v is not None and v != "":
                self.user_profile[k] = v

    def set_scheme(self, scheme_dict: Optional[Dict[str, Any]]):
        self.updated_at = time.time()
        self.active_scheme = scheme_dict
        if scheme_dict:
            self.active_section = "scheme_expert"

    def get_recent_history(self, limit: int = 6) -> List[Dict[str, str]]:
        """Return formatted messages for LLM context."""
        recent = self.history[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in recent]


class ConversationMemoryManager:
    """Thread-safe session memory manager."""

    def __init__(self, ttl_seconds: int = 3600):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()
        self.ttl_seconds = ttl_seconds

    def get_session(self, session_id: Optional[str] = None) -> SessionState:
        with self._lock:
            self._cleanup_expired()
            if not session_id or session_id not in self._sessions:
                new_id = session_id or f"sess_{int(time.time()*1000)}"
                session = SessionState(new_id)
                self._sessions[new_id] = session
                return session
            session = self._sessions[session_id]
            session.updated_at = time.time()
            return session

    def reset_session(self, session_id: str) -> SessionState:
        with self._lock:
            session = SessionState(session_id)
            self._sessions[session_id] = session
            return session

    def _cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, sess in self._sessions.items() if now - sess.updated_at > self.ttl_seconds]
        for sid in expired:
            del self._sessions[sid]


conversation_memory = ConversationMemoryManager()
