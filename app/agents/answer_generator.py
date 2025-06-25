"""
Simple answer generation
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State, add_to_history
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class AnswerGenerator:
    def __init__(self):
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.encoding = tiktoken.encoding_for_model(LLM_MODEL)
    
    def generate_answer(self, state: State) -> State:
        # Skip if already have an answer
        if state.get("answer") and state["intent"] in ["greeting", "out_of_scope"]:
            add_to_history(state)
            return state
        
        try:
            # Format results for prompt
            results_text = "No data" if len(state["result"]) <= 1 else str(state["result"][:6])  # First 5 rows
            
            prompt = f"""Answer the user's question based on the SQL query results.

Question: {state['question']}
SQL Query: {state['query']}
Results: {results_text}

Provide a clear, helpful answer explaining what the data shows:"""
            
            # Count tokens and generate answer
            prompt_tokens = len(self.encoding.encode(prompt))
            response = self.llm.invoke(prompt)
            response_tokens = len(self.encoding.encode(response.content))
            
            state["answer"] = response.content
            state["token_usage"]["answer_tokens"] = prompt_tokens + response_tokens
            
        except Exception as e:
            state["answer"] = f"Error generating answer: {str(e)}"
        
        # Add to conversation history
        add_to_history(state)
        return state

def generate_answer(state: State) -> State:
    generator = AnswerGenerator()
    return generator.generate_answer(state) 