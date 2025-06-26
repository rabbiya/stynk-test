"""
Intent Detection Agent
Classifies user questions as: greeting, sql_query, or out_of_scope
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class IntentDetector:
    """Detects the intent of user questions"""
    
    def __init__(self):
        # Initialize the LLM
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.encoding = tiktoken.encoding_for_model(LLM_MODEL)
    
    def detect_intent(self, state: State) -> State:
        """Classify the user's question intent"""
        
        # Enhanced prompt for better cinema/entertainment classification
        prompt = f"""Classify this question as one word: greeting, sql_query, or out_of_scope

The user has a movie/entertainment BigQuery database with these tables:
- content_dimension (movies, shows, TV series)
- showtime_fact (cinema showings, theater screenings)  
- streamings_fact (streaming platform data)
- cinema_dimension (theaters, cinema chains, locations)
- channel_dimension (streaming platforms, TV channels)

This system can answer questions about:
- Movies, shows, content performance
- Cinema chains, theaters, showtimes
- Streaming platforms and viewing data
- Geographic analysis (UK, regions, countries)
- Time-based trends and analytics

Question: {state['question']}

Examples:
- "Hi there!" → greeting
- "Hello" → greeting
- "Show me trending movies" → sql_query
- "What movies are popular?" → sql_query
- "Which cinema chain has most showings?" → sql_query
- "Most active cinema in the UK?" → sql_query
- "Top streaming platforms?" → sql_query
- "Content performance by region?" → sql_query
- "Movie trends last month?" → sql_query
- "Theater attendance data?" → sql_query
- "Tell me a joke" → out_of_scope
- "What's the weather?" → out_of_scope
- "How to cook pasta?" → out_of_scope

Answer:"""
        
        # Get LLM response and count tokens
        prompt_tokens = len(self.encoding.encode(prompt))
        response = self.llm.invoke(prompt)
        response_tokens = len(self.encoding.encode(response.content))
        
        # Parse intent (default to sql_query if unclear)
        intent = response.content.strip().lower()
        if intent not in ["greeting", "sql_query", "out_of_scope"]:
            intent = "sql_query"
        
        # Update state
        state["intent"] = intent
        state["token_usage"]["intent_tokens"] = prompt_tokens + response_tokens
        
        # Handle non-SQL intents with predefined responses
        if intent == "greeting":
            state["answer"] = "Hello! I can help you analyze your movie and entertainment data. What would you like to know about your content, cinemas, or streaming metrics?"
            state["query"] = ""
            state["result"] = []
        elif intent == "out_of_scope":
            state["answer"] = "I specialize in analyzing movie and entertainment data. Please ask questions about your content, cinemas, theaters, streaming platforms, or viewing metrics."
            state["query"] = ""
            state["result"] = []
        
        return state

def detect_intent(state: State) -> State:
    """Entry point for intent detection"""
    detector = IntentDetector()
    return detector.detect_intent(state) 