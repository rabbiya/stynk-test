"""
Simple intent detection
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class IntentDetector:
    def __init__(self):
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.encoding = tiktoken.encoding_for_model(LLM_MODEL)
    
    def detect_intent(self, state: State) -> State:
        prompt = f"""Classify this question as one word: greeting, sql_query, or out_of_scope

The user has a movie/content BigQuery database with tables like:
- content_dimension (movies, shows)
- showtime_fact (cinema showings)
- streamings_fact (streaming data)
- cinema_dimension (theaters)
- channel_dimension (streaming platforms)

Question: {state['question']}

Examples:
- "Hi there!" → greeting
- "What's the sales by region?" → sql_query
- "Show me trending movies" → sql_query
- "What movies are popular in Germany?" → sql_query
- "List all content in the database" → sql_query
- "What are the top streaming platforms?" → sql_query
- "Tell me a joke" → out_of_scope
- "What's the weather?" → out_of_scope

Answer:"""
        
        # Count tokens and get response
        prompt_tokens = len(self.encoding.encode(prompt))
        response = self.llm.invoke(prompt)
        response_tokens = len(self.encoding.encode(response.content))
        
        intent = response.content.strip().lower()
        if intent not in ["greeting", "sql_query", "out_of_scope"]:
            intent = "sql_query"  # Default to sql_query for ambiguous cases
        
        state["intent"] = intent
        state["token_usage"]["intent_tokens"] = prompt_tokens + response_tokens
        
        # Handle non-SQL intents
        if intent == "greeting":
            state["answer"] = "Hello! I can help you analyze your movie and streaming data. What would you like to know about your content, showings, or streaming metrics?"
            state["query"] = ""
            state["result"] = []
        elif intent == "out_of_scope":
            state["answer"] = "I can help you analyze your movie and streaming data. Please ask questions about your content, theaters, streaming platforms, or viewing metrics."
            state["query"] = ""
            state["result"] = []
        
        return state

def detect_intent(state: State) -> State:
    detector = IntentDetector()
    return detector.detect_intent(state) 