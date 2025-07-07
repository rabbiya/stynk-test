"""
Simple workflow orchestrator for SQL Agent
Manages the flow: Intent Detection → Query Generation → Execution → Relevance Check → Answer Generation
"""

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from app.core.state import State
from app.agents.intent_detector import detect_intent
from app.agents.query_generator import generate_query
from app.agents.query_executor import execute_query
from app.agents.relevance_checker import check_relevance_and_retry
from app.agents.answer_generator import generate_answer

class SQLAgent:
    """Main SQL Agent that orchestrates the workflow"""
    
    def __init__(self):
        self.memory = MemorySaver()  # Stores conversation history
        self.graph = self._build_workflow()
    
    def _build_workflow(self):
        """Build the agent workflow graph"""
        builder = StateGraph(State)
        
        # Add processing steps
        builder.add_node("detect_intent", detect_intent)
        builder.add_node("generate_query", generate_query)
        builder.add_node("execute_query", execute_query)
        builder.add_node("check_relevance", check_relevance_and_retry)
        builder.add_node("generate_answer", generate_answer)
        
        # Define the workflow path
        builder.add_edge(START, "detect_intent")
        
        # Branch based on intent: if greeting/out_of_scope, skip to end
        builder.add_conditional_edges(
            "detect_intent",
            self._should_continue_to_sql,
            {"end": END, "continue": "generate_query"}
        )
        
        # Linear flow for SQL queries with relevance checking
        builder.add_edge("generate_query", "execute_query")
        builder.add_edge("execute_query", "check_relevance")
        builder.add_edge("check_relevance", "generate_answer")
        builder.add_edge("generate_answer", END)
        
        return builder.compile(checkpointer=self.memory)
    
    def _should_continue_to_sql(self, state: State) -> str:
        """Decide whether to continue with SQL generation or end early"""
        return "end" if state["intent"] in ["greeting", "out_of_scope"] else "continue"
    
    def process(self, state: State) -> State:
        """Process a user question through the workflow"""
        config = {"configurable": {"thread_id": state["session_id"]}}
        
        # Run the workflow
        final_state = None
        for step in self.graph.stream(state, config, stream_mode="updates"):
            final_state = step
        
        # Extract the final result
        if final_state:
            step_name = list(final_state.keys())[-1]
            return final_state[step_name]
        
        return state

# Global agent instance (singleton pattern)
_agent = None

def get_sql_agent():
    """Get or create the global SQL agent instance"""
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent 