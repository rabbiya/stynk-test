"""
Answer Generation Agent
Converts query results into natural language responses
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State, add_to_history
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class AnswerGenerator:
    """Generates natural language answers from query results"""
    
    def __init__(self):
        # Initialize the LLM
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.encoding = tiktoken.encoding_for_model(LLM_MODEL)
    
    def generate_answer(self, state: State) -> State:
        """Generate a natural language answer from query results"""
        
        # Skip if we already have an answer (from greeting/out_of_scope)
        if state.get("answer") and state["intent"] in ["greeting", "out_of_scope"]:
            add_to_history(state)
            return state
        
        try:
            # Prepare results for the prompt (limit to first 5 rows for context)
            results_text = "No data found"
            if state["result"] and len(state["result"]) > 1:
                results_text = str(state["result"][:6])  # Headers + 5 data rows
            
            # Simple prompt for answer generation
            prompt = f"""Based on the SQL query results, provide a clear answer to the user's question.

User Question: {state['question']}
SQL Query: {state['query']}
Results: {results_text}

Provide a helpful, conversational answer that explains what the data shows:
after that double check response with real data (present on internet) and show with heading double check:
"""
            
            # Get LLM response and count tokens
            prompt_tokens = len(self.encoding.encode(prompt))
            response = self.llm.invoke(prompt)
            response_tokens = len(self.encoding.encode(response.content))
            
            # Update state
            state["answer"] = response.content
            state["token_usage"]["answer_tokens"] = prompt_tokens + response_tokens
            
        except Exception as e:
            state["answer"] = f"Error generating answer: {str(e)}"
        
        # Add this conversation to history
        add_to_history(state)
        return state

def generate_answer(state: State) -> State:
    """Entry point for answer generation"""
    generator = AnswerGenerator()
    return generator.generate_answer(state) 