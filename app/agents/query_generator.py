"""
SQL Query Generation Agent
Converts natural language questions into BigQuery SQL queries
"""

import tiktoken
from langchain.chat_models import init_chat_model
from app.core.state import State
from app.db.connection import get_db_connection, get_bigquery_client, get_dataset_info, get_schema_info
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

class QueryGenerator:
    """Generates BigQuery SQL from natural language questions"""
    
    def __init__(self):
        # Initialize LLM and connections
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
    
    def _get_schema_text(self):
        """Format database schema for the LLM prompt"""
        info = f"Dataset: {self.dataset_info['full_dataset']}\n\nAVAILABLE TABLES AND COLUMNS:\n"
        
        for table_name, table_info in self.schema_info.items():
            info += f"\n📋 {table_name}:\n"
            
            # Add column information with clear formatting and array indicators
            for col in table_info['columns']:
                col_type = col['type']
                # Highlight array columns for better visibility
                if col_type.startswith('ARRAY'):
                    info += f"   • {col['name']} ({col_type}) ⚠️ ARRAY COLUMN\n"
                else:
                    info += f"   • {col['name']} ({col_type})\n"
            
            # Add row count if available
            if table_info['num_rows']:
                info += f"   Rows: {table_info['num_rows']:,}\n"
        
        return info
    
    def generate_query(self, state: State) -> State:
        """Generate SQL query from user question"""
        try:
            question = state['question']
            schema_text = self._get_schema_text()
            
            # Enhanced prompt with strict alias validation
            prompt = f"""Generate a BigQuery SQL query to answer this question.

Question: {question}

{schema_text}

CRITICAL RULES - FOLLOW EXACTLY:
1. Use ONLY the column names listed above - DO NOT make up column names
2. Use ONLY the table names listed above - DO NOT make up table names  
3. Always use full table names: `{self.dataset_info['project_id']}.{self.dataset_info['dataset_id']}.table_name`
4. ALWAYS use table aliases: `full_table_name` AS alias_name
5. In SELECT, JOINs and WHERE clauses, use ONLY the alias names defined in FROM/JOIN

ALIAS AND COLUMN VALIDATION:
6. Every column reference MUST use an alias that exists in the FROM/JOIN clauses
7. Before using alias.column, make sure:
   - The table with that alias is included in FROM or JOIN
   - The column exists in that specific table's schema above
8. Common aliases: cd = content_dimension, sf = showtime_fact, c = cinema_dimension
9. Only reference columns from tables that are actually included in the query

ARRAY COLUMN HANDLING:
10. For ARRAY<STRING> columns (like languages, genres, cast):
    - Use 'English' IN UNNEST(cd.languages) instead of cd.languages LIKE '%English%'
    - Use EXISTS(SELECT 1 FROM UNNEST(cd.languages) AS lang WHERE lang LIKE '%English%') for partial matches
    - Use ARRAY_LENGTH(cd.languages) > 0 to check if array is not empty
11. Common array columns: languages, genres, cast, directors, countries

EFFICIENCY GUIDELINES:
12. Add date/time filters ONLY when:
    - Question mentions time periods ("last month", "recent", "this year")
    - Question asks for trends or time-based analysis
13. Add geographic filters ONLY when:
    - Question mentions specific locations ("UK", "London", "Europe")
    - Question asks for regional analysis
14. For "top N" or "most/least" questions, use ORDER BY with LIMIT
15. Select only the columns needed to answer the question
16. Use COUNT(*) for counting records

VALIDATION EXAMPLES:
❌ WRONG - using cd.city without including content_dimension:
```sql
FROM showtime_fact AS sf
JOIN cinema_dimension AS c ON sf.cinema_id = c.cinema_id
SELECT cd.city  -- ERROR: cd alias not defined!
```

✅ CORRECT - only use aliases that are defined:
```sql
FROM showtime_fact AS sf
JOIN cinema_dimension AS c ON sf.cinema_id = c.cinema_id
SELECT c.city  -- CORRECT: c alias is defined and city exists in cinema_dimension
```

❌ WRONG - using LIKE on array column:
```sql
WHERE cd.languages LIKE '%English%'  -- ERROR: languages is ARRAY<STRING>
```

✅ CORRECT - proper array handling:
```sql
WHERE 'English' IN UNNEST(cd.languages)  -- For exact match
-- OR for partial match:
WHERE EXISTS(SELECT 1 FROM UNNEST(cd.languages) AS lang WHERE lang LIKE '%English%')
```

Return ONLY the SQL query, no explanations."""
            
            # Get LLM response and count tokens
            prompt_tokens = len(self.encoding.encode(prompt))
            response = self.llm.invoke(prompt)
            response_tokens = len(self.encoding.encode(response.content))
            
            # Clean up the query
            query = self._clean_query(response.content)
            
            # Update state
            state["query"] = query
            state["token_usage"]["query_tokens"] = prompt_tokens + response_tokens
            
        except Exception as e:
            state["query"] = ""
            state["result"] = [["Query Generation Error"], [str(e)]]
        
        return state
    
    def _clean_query(self, raw_query: str) -> str:
        """Clean up the generated query"""
        query = raw_query.strip()
        
        # Remove markdown formatting if present
        if query.startswith('```sql'):
            query = query.replace('```sql', '').replace('```', '').strip()
        elif query.startswith('```'):
            query = query.replace('```', '').strip()
        
        # Add LIMIT if not present
        if 'LIMIT' not in query.upper():
            query = query.rstrip(';') + ' LIMIT 10'
        
        return query

def generate_query(state: State) -> State:
    """Entry point for query generation"""
    generator = QueryGenerator()
    return generator.generate_query(state) 