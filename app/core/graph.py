"""
Simple LangGraph workflow
"""

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from app.core.state import State
from app.agents.intent_detector import detect_intent
from app.agents.query_generator import generate_query
from app.agents.query_executor import execute_query
from app.agents.answer_generator import generate_answer

class SQLAgent:
    def __init__(self):
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        graph_builder = StateGraph(State)
        
        # Add nodes
        graph_builder.add_node("detect_intent", detect_intent)
        graph_builder.add_node("generate_query", generate_query)
        graph_builder.add_node("execute_query", execute_query)
        graph_builder.add_node("generate_answer", generate_answer)
        
        # Add edges
        graph_builder.add_edge(START, "detect_intent")
        graph_builder.add_conditional_edges(
            "detect_intent",
            lambda state: "end" if state["intent"] in ["greeting", "out_of_scope"] else "continue",
            {"end": END, "continue": "generate_query"}
        )
        graph_builder.add_edge("generate_query", "execute_query")
        graph_builder.add_edge("execute_query", "generate_answer")
        graph_builder.add_edge("generate_answer", END)
        
        return graph_builder.compile(checkpointer=self.memory)
    
    def process(self, state: State) -> State:
        config = {"configurable": {"thread_id": state["session_id"]}}
        
        final_state = None
        for step in self.graph.stream(state, config, stream_mode="updates"):
            final_state = step
        
        # Extract final state
        if final_state:
            step_name = list(final_state.keys())[-1]
            return final_state[step_name]
        
        return state

# Global instance
_agent = None

def get_sql_agent():
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent 