"""
Query Execution Agent
Executes SQL queries against BigQuery and handles errors
"""

from google.cloud import bigquery
from app.core.state import State
from app.db.connection import get_bigquery_client
from app.core.config import MAX_BYTES_BILLED, QUERY_TIMEOUT

class QueryExecutor:
    """Executes BigQuery SQL queries with safety limits"""
    
    def __init__(self):
        self.client = get_bigquery_client()
        self.bytes_limit = MAX_BYTES_BILLED  # Use config setting
        
    def execute_query(self, state: State) -> State:
        """Execute the SQL query and return results"""
        
        # Check if we have a query to execute
        if not state["query"]:
            state["result"] = [["No query to execute"]]
            return state
        
        try:
            # Configure query job with safety limits
            job_config = bigquery.QueryJobConfig()
            job_config.maximum_bytes_billed = self.bytes_limit
            job_config.use_query_cache = True  # Use cached results when possible
            
            # Execute the query
            query_job = self.client.query(state["query"], job_config=job_config)
            results = query_job.result(timeout=QUERY_TIMEOUT)
            
            # Format results as list of lists
            columns = [field.name for field in results.schema]
            rows = list(results)
            
            if rows:
                # Add column headers as first row
                formatted_result = [columns]
                # Add data rows (limit to 10 for display)
                for row in rows[:10]:
                    formatted_result.append([str(cell) for cell in row])
                state["result"] = formatted_result
            else:
                state["result"] = [["No data found"]]
                
        except Exception as e:
            # Handle execution errors
            error_msg = str(e)
            state["result"] = [["Error"], [error_msg]]
            
            # Provide helpful error messages
            if "bytes billed" in error_msg.lower():
                state["answer"] = self._get_bytes_error_message(error_msg)
            elif "timeout" in error_msg.lower():
                state["answer"] = "Query timed out. Try asking for less data or a simpler question."
            elif "not found" in error_msg.lower():
                state["answer"] = "Table or column not found. Please check your question refers to available data."
            else:
                state["answer"] = f"Query failed: {error_msg}"
        
        return state
    
    def _get_bytes_error_message(self, error_msg: str) -> str:
        """Generate helpful message for bytes limit errors"""
        return (
            f"Query requires too much data processing (limit: {self.bytes_limit / 10**9:.1f}GB). "
            "Try:\n"
            "• Add date filters (e.g., 'last 7 days')\n"
            "• Ask for specific content types or regions\n"
            "• Request top N results instead of all data\n"
            "• Use more specific criteria in your question"
        )

def execute_query(state: State) -> State:
    """Entry point for query execution"""
    executor = QueryExecutor()
    return executor.execute_query(state) 