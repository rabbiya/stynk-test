"""
BigQuery SQL Agent API
Simple FastAPI application that converts natural language questions to SQL queries
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

# Initialize application
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BigQuery SQL Agent", 
    description="Convert natural language questions to BigQuery SQL",
    version="1.0.0"
)

# Enable CORS for web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Test BigQuery connection when server starts"""
    try:
        client = get_bigquery_client()
        dataset_info = get_dataset_info()
        
        # Simple connection test
        list(client.query("SELECT 1").result())
        
        logger.info("✅ BigQuery connection successful")
        logger.info(f"📊 Dataset: {dataset_info['full_dataset']}")
        
    except Exception as e:
        logger.error(f"❌ BigQuery connection failed: {e}")

@app.get("/")
async def root():
    """Root endpoint - shows service status"""
    dataset_info = get_dataset_info()
    return {
        "message": "BigQuery SQL Agent is running",
        "status": "active",
        "project": dataset_info["project_id"],
        "dataset": dataset_info["dataset_id"]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        client = get_bigquery_client()
        dataset_info = get_dataset_info()
        
        # Test BigQuery connection
        list(client.query("SELECT 1").result())
        
        return {
            "status": "healthy",
            "database": "connected",
            "dataset": dataset_info["full_dataset"]
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }

@app.post("/query", response_model=QueryResponse)
async def query_data(request: QuestionRequest):
    """
    Main endpoint: Ask questions about your BigQuery data
    
    Example: "What are the top 5 movies by views last month?"
    """
    logger.info(f"Question from {request.session_id}: {request.question}")
    
    try:
        # Create initial state for this question
        state = create_initial_state(request.question, request.session_id)
        
        # Process through the agent workflow
        agent = get_sql_agent()
        final_state = agent.process(state)
        
        # Calculate total token usage
        token_usage = final_state.get("token_usage", {})
        total_tokens = sum(token_usage.values())
        
        # Return structured response
        return QueryResponse(
            query=final_state.get("query", ""),
            result=final_state.get("result", []),
            insights=final_state.get("answer", "No answer generated"),
            token_usage={
                "total_tokens": total_tokens,
                **token_usage
            },
            session_id=request.session_id,
            conversation_count=len(final_state.get("conversation_history", []))
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a specific session"""
    try:
        agent = get_sql_agent()
        config = {"configurable": {"thread_id": session_id}}
        
        # Get stored conversation state
        checkpoint = agent.graph.get_state(config)
        
        if checkpoint and checkpoint.values:
            history = checkpoint.values.get("conversation_history", [])
            return {
                "session_id": session_id, 
                "history": history,
                "count": len(history)
            }
        
        return {
            "session_id": session_id, 
            "history": [],
            "count": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# For backwards compatibility
@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QuestionRequest):
    """Legacy endpoint - redirects to /query"""
    return await query_data(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
