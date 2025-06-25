from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"

class QueryResponse(BaseModel):
    query: str
    result: List[List[Any]]
    insights: str
    token_usage: Dict[str, int]
    session_id: str
    conversation_count: int 