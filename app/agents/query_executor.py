"""
Simple BigQuery query execution
"""

from google.cloud import bigquery
from app.core.state import State
from app.db.connection import get_bigquery_client

class QueryExecutor:
    def __init__(self):
        self.client = get_bigquery_client()
    
    def execute_query(self, state: State) -> State:
        if not state["query"]:
            state["result"] = [["No query to execute"]]
            return state
        
        try:
            # Execute query with safety limits
            job_config = bigquery.QueryJobConfig()
            job_config.maximum_bytes_billed = 5 * 10**8  # 500MB limit (reduced from 1GB)
            job_config.use_query_cache = True  # Use cached results when possible
            
            query_job = self.client.query(state["query"], job_config=job_config)
            results = query_job.result(timeout=30)
            
            # Format results
            columns = [field.name for field in results.schema]
            rows = list(results)
            
            if rows:
                formatted_result = [columns]
                for row in rows[:10]:  # Limit to 10 rows
                    formatted_result.append([str(cell) for cell in row])
                state["result"] = formatted_result
            else:
                state["result"] = [["No data found"]]
                
        except Exception as e:
            error_msg = str(e)
            state["result"] = [["Error"], [error_msg]]
            
            # Provide helpful suggestions for common errors
            if "bytes billed" in error_msg.lower():
                state["answer"] = "Query too large for processing limits. Try asking for a smaller date range or specific subset of data."
            elif "timeout" in error_msg.lower():
                state["answer"] = "Query timed out. Try simplifying the question or asking for less data."
            else:
                state["answer"] = f"Query execution failed: {error_msg}"
        
        return state

def execute_query(state: State) -> State:
    executor = QueryExecutor()
    return executor.execute_query(state) 