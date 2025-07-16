"""
Visualization Detection Agent
Determines if a user query requires a chart and what type of chart would be most appropriate
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class VisualizationDetector:
    """Detects if visualization is needed and determines chart type"""
    
    def __init__(self):
        # Initialize the LLM
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.encoding = tiktoken.encoding_for_model(LLM_MODEL)
    
    def detect_visualization(self, state: State) -> State:
        """Determine if visualization is needed and what type"""
        
        # Skip if intent is not sql_query
        if state["intent"] != "sql_query":
            state["needs_visualization"] = False
            state["chart_type"] = None
            return state
        
        prompt = f"""Analyze this question and determine if it needs a visualization chart.

Question: {state['question']}

Visualization keywords that indicate charts are needed:
- chart, graph, plot, visualize, visualization
- show me, display, see, view
- pie chart, bar chart, line chart, histogram
- trend, comparison, distribution, breakdown
- percentage, proportion, ratio
- top, bottom, ranking, list
- over time, by month, by year, by region

Chart type recommendations:
- pie: for percentages, proportions, parts of a whole
- bar: for comparisons, rankings, categories
- line: for trends over time, time series data
- histogram: for distributions, frequency data

You must respond with ONLY valid JSON in this exact format:
{{
    "needs_visualization": true/false,
    "chart_type": "pie" or "bar" or "line" or "histogram" or null,
    "reasoning": "brief explanation"
}}

Examples:
- "Show me a pie chart of movie genres" → {{"needs_visualization": true, "chart_type": "pie", "reasoning": "explicitly requests pie chart"}}
- "What are the top 5 movies?" → {{"needs_visualization": true, "chart_type": "bar", "reasoning": "ranking data best shown as bar chart"}}
- "Show trends over time" → {{"needs_visualization": true, "chart_type": "line", "reasoning": "time series data"}}
- "How many movies are there?" → {{"needs_visualization": false, "chart_type": null, "reasoning": "simple count query"}}

Answer:"""
        
        # Get LLM response and count tokens
        prompt_tokens = len(self.encoding.encode(prompt))
        response = self.llm.invoke(prompt)
        response_tokens = len(self.encoding.encode(response.content))
        
        # Parse response with better error handling
        try:
            import json
            import re
            
            # Clean the response - remove any markdown formatting
            cleaned_response = response.content.strip()
            
            # Try to extract JSON if it's wrapped in markdown
            json_match = re.search(r'```json\s*(.*?)\s*```', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(1).strip()
            
            # Remove any leading/trailing text that's not JSON
            cleaned_response = re.sub(r'^[^{]*', '', cleaned_response)
            cleaned_response = re.sub(r'[^}]*$', '', cleaned_response)
            
            result = json.loads(cleaned_response)
            
            state["needs_visualization"] = result.get("needs_visualization", False)
            state["chart_type"] = result.get("chart_type")
            
            print(f"Visualization detection result: {result}")
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw response: {response.content}")
            
            # Fallback: use simple keyword detection
            question_lower = state['question'].lower()
            
            # Check for explicit chart requests
            if any(keyword in question_lower for keyword in ['pie chart', 'pie']):
                state["needs_visualization"] = True
                state["chart_type"] = "pie"
            elif any(keyword in question_lower for keyword in ['bar chart', 'bar']):
                state["needs_visualization"] = True
                state["chart_type"] = "bar"
            elif any(keyword in question_lower for keyword in ['line chart', 'line']):
                state["needs_visualization"] = True
                state["chart_type"] = "line"
            elif any(keyword in question_lower for keyword in ['histogram']):
                state["needs_visualization"] = True
                state["chart_type"] = "histogram"
            elif any(keyword in question_lower for keyword in ['chart', 'graph', 'plot', 'visualize', 'visualization', 'show me', 'display']):
                # Default to bar chart for general visualization requests
                state["needs_visualization"] = True
                state["chart_type"] = "bar"
            else:
                state["needs_visualization"] = False
                state["chart_type"] = None
        
        # Update token usage
        state["token_usage"]["visualization_detection_tokens"] = prompt_tokens + response_tokens
        
        return state

def detect_visualization(state: State) -> State:
    """Entry point for visualization detection"""
    detector = VisualizationDetector()
    return detector.detect_visualization(state) 