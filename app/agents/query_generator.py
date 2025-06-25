"""
Simple BigQuery SQL generation
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State
from app.db.connection import get_db_connection, get_bigquery_client, get_dataset_info, get_schema_info
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class QueryGenerator:
    def __init__(self):
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.encoding = tiktoken.encoding_for_model(LLM_MODEL)
        self.db = get_db_connection()
        self.client = get_bigquery_client()
        self.dataset_info = get_dataset_info()
        self.schema_info = get_schema_info()
    
    def _format_schema_info(self):
        """Format schema information for the LLM"""
        info = f"""Dataset: {self.dataset_info['full_dataset']}\n\nAVAILABLE TABLES:\n"""
        
        for table_name, table_info in self.schema_info.items():
            info += f"\n{table_name}"
            if table_info['description']:
                info += f" - {table_info['description']}"
            info += "\nColumns:\n"
            
            for col in table_info['columns']:
                info += f"  - {col['name']} ({col['type']})"
                if col['description']:
                    info += f": {col['description']}"
                info += "\n"
            
            if table_info['num_rows'] is not None:
                info += f"Row count: {table_info['num_rows']:,}\n"
        
        return info
    
    def generate_query(self, state: State) -> State:
        try:
            question = state['question']
            schema_info = self._format_schema_info()
            
            prompt = f"""You are a SQL query generator. Your ONLY task is to generate a BigQuery SQL query.

IMPORTANT: Return ONLY the SQL query. NO explanations, NO markdown, NO comments, NO text before or after the query.

Question to answer: {question}

Available tables and their schema:
{schema_info}

STRICT RULES:
1. ONLY use tables listed above - NO OTHER TABLES
2. ALWAYS use the exact table names as shown
3. NEVER create or reference tables that don't exist
4. ALWAYS use proper field names from the schema
5. ALWAYS use backticks: `{self.dataset_info['project_id']}.{self.dataset_info['dataset_id']}.table_name`
6. Keep queries simple and efficient
7. Add LIMIT 10 for safety
8. Use date filters to reduce data processing
9. For trends, focus on recent data (last 30 days)
10. Keep joins simple and minimize their number
11. Use DATE() function for datetime comparisons

Remember: Output ONLY the SQL query. Nothing else."""
            
            # Count tokens and generate query
            prompt_tokens = len(self.encoding.encode(prompt))
            response = self.llm.invoke(prompt)
            response_tokens = len(self.encoding.encode(response.content))
            
            query = response.content.strip()
            
            # Clean up the query - remove markdown if present
            if query.startswith('```sql'):
                query = query.replace('```sql', '').replace('```', '').strip()
            elif query.startswith('```'):
                query = query.replace('```', '').strip()
            
            # Add LIMIT if not present
            if 'LIMIT' not in query.upper():
                query = query.rstrip(';') + ' LIMIT 10'
            
            state["query"] = query
            state["token_usage"]["query_tokens"] = prompt_tokens + response_tokens
            
        except Exception as e:
            state["query"] = ""
            state["answer"] = f"Error generating query: {str(e)}"
        
        return state

def generate_query(state: State) -> State:
    generator = QueryGenerator()
    return generator.generate_query(state) 