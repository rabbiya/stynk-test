"""
Simple state management for the SQL agent
"""

from typing_extensions import TypedDict, List, Dict, Any
from typing import Optional
from datetime import datetime

class State(TypedDict):
    question: str
    query: str
    result: List[List[Any]]
    answer: str
    intent: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    token_usage: Dict[str, int]

def create_initial_state(question: str, session_id: str = "default") -> State:
    return State(
        question=question,
        query="",
        result=[],
        answer="",
        intent="",
        session_id=session_id,
        conversation_history=[],
        token_usage={}
    )

def add_to_history(state: State):
    """Add current interaction to conversation history"""
    if len(state["conversation_history"]) >= 5:  # Keep last 5 conversations
        state["conversation_history"] = state["conversation_history"][-4:]
    
    state["conversation_history"].append({
        "question": state["question"],
        "answer": state["answer"],
        "timestamp": datetime.now().isoformat()
    })
    return state 