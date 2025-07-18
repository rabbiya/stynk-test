"""
State management for SQL Agent conversations
Tracks question, query, results, and conversation history
"""

from typing_extensions import TypedDict, List, Dict, Any
from typing import Optional
from datetime import datetime

class State(TypedDict):
    """State object that passes through the agent workflow"""
    question: str                           # User's original question
    query: str                             # Generated SQL query
    result: List[List[Any]]                # Query results from BigQuery
    answer: str                            # Final formatted answer
    intent: str                            # Detected intent (greeting/sql_query/out_of_scope)
    session_id: str                        # User session identifier
    conversation_history: List[Dict[str, Any]]  # Previous conversations
    token_usage: Dict[str, int]            # LLM token consumption tracking
    needs_visualization: bool              # Whether the query requires a chart
    chart_type: Optional[str]              # Type of chart to generate (pie, bar, line, etc.)
    chart_data: Optional[Dict[str, Any]]   # Chart configuration and data (JSON format)
    visualization_html: Optional[str]      # Generated chart HTML

def create_initial_state(question: str, session_id: str = "default") -> State:
    """Create a new state object for a user question"""
    return State(
        question=question,
        query="",
        result=[],
        answer="",
        intent="",
        session_id=session_id,
        conversation_history=[],
        token_usage={},
        needs_visualization=False,
        chart_type=None,
        chart_data=None,
        visualization_html=None
    )

def add_to_history(state: State):
    """Add current conversation to history (keep last 5 only)"""
    # Remove old conversations if we have too many
    if len(state["conversation_history"]) >= 5:
        state["conversation_history"] = state["conversation_history"][-4:]
    
    # Add current conversation
    state["conversation_history"].append({
        "question": state["question"],
        "answer": state["answer"],
        "timestamp": datetime.now().isoformat()
    })
    return state 