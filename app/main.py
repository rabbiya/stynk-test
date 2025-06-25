"""
Simple BigQuery SQL Agent with LangGraph, LangSmith, and tiktoken
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models import QuestionRequest, QueryResponse
from app.core.state import create_initial_state
from app.core.graph import get_sql_agent
from app.db.connection import get_bigquery_client, get_dataset_info

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="BigQuery SQL Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Test connections on startup"""
    try:
        client = get_bigquery_client()
        dataset_info = get_dataset_info()
        
        # Test connection
        list(client.query("SELECT 1").result())
        
        logger.info("✅ BigQuery connection successful")
        logger.info(f"📊 Connected to: {dataset_info['full_dataset']}")
        
    except Exception as e:
        logger.error(f"❌ BigQuery connection failed: {e}")

@app.get("/")
async def root():
    dataset_info = get_dataset_info()
    return {
        "message": "BigQuery SQL Agent is running",
        "project": dataset_info["project_id"],
        "dataset": dataset_info["dataset_id"]
    }

@app.get("/health")
async def health():
    try:
        client = get_bigquery_client()
        dataset_info = get_dataset_info()
        
        # Test connection
        list(client.query("SELECT 1").result())
        
        return {
            "status": "healthy",
            "database": "connected",
            "project": dataset_info["project_id"],
            "dataset": dataset_info["dataset_id"],
            "full_dataset": dataset_info["full_dataset"]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QuestionRequest):
    """Main endpoint - ask questions about your BigQuery data"""
    
    logger.info(f"Question from {request.session_id}: {request.question}")
    
    try:
        # Create initial state
        state = create_initial_state(request.question, request.session_id)
        
        # Process through LangGraph workflow
        agent = get_sql_agent()
        final_state = agent.process(state)
        
        # Calculate total tokens
        total_tokens = sum(final_state.get("token_usage", {}).values())
        
        # Return response
        return QueryResponse(
            query=final_state.get("query", ""),
            result=final_state.get("result", []),
            insights=final_state.get("answer", "No answer generated"),
            token_usage={
                "total_tokens": total_tokens,
                **final_state.get("token_usage", {})
            },
            session_id=request.session_id,
            conversation_count=len(final_state.get("conversation_history", []))
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a session"""
    try:
        agent = get_sql_agent()
        config = {"configurable": {"thread_id": session_id}}
        checkpoint = agent.graph.get_state(config)
        
        if checkpoint and checkpoint.values:
            history = checkpoint.values.get("conversation_history", [])
            return {"session_id": session_id, "history": history}
        
        return {"session_id": session_id, "history": []}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
