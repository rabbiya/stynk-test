"""
Query Execution Agent
Executes SQL queries against BigQuery and handles errors
"""

import re
from google.cloud import bigquery
from app.core.state import State
from app.db.connection import get_bigquery_client
from app.core.config import MAX_BYTES_BILLED, QUERY_TIMEOUT

class QueryExecutor:
    """Executes BigQuery SQL queries with safety limits and smart retry"""
    
    def __init__(self):
        self.client = get_bigquery_client()
        self.bytes_limit = MAX_BYTES_BILLED  # Use config setting
        
        # Related terms mapping for smart retry
        self.related_terms = {
            'wedding': ['romance', 'romantic', 'marriage', 'bride', 'groom', 'love'],
            'action': ['adventure', 'thriller', 'fight', 'chase', 'explosive'],
            'horror': ['scary', 'fear', 'terror', 'supernatural', 'ghost'],
            'comedy': ['funny', 'humor', 'laugh', 'comic', 'hilarious'],
            'drama': ['emotional', 'serious', 'life', 'family', 'relationship'],
            'sci-fi': ['science fiction', 'futuristic', 'space', 'alien', 'technology'],
            'fantasy': ['magical', 'magic', 'mythical', 'supernatural', 'fairy tale'],
            'crime': ['police', 'detective', 'murder', 'investigation', 'criminal'],
            'war': ['military', 'battle', 'soldier', 'combat', 'conflict'],
            'western': ['cowboy', 'frontier', 'wild west', 'gunfighter', 'saloon']
        }
        
    def execute_query(self, state: State) -> State:
        """Execute the SQL query with smart retry mechanism"""
        
        # Check if we have a query to execute
        if not state["query"]:
            state["result"] = [["No query to execute"]]
            return state

        original_query = state["query"]
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Execute the query
                result = self._execute_single_query(state["query"])
                
                # Check if we got meaningful results
                if self._has_meaningful_results(result):
                    state["result"] = result
                    if retry_count > 0:
                        state["retry_info"] = f"Found results on attempt {retry_count + 1} using broader search terms"
                    return state
                else:
                    # No results, try to broaden the search
                    if retry_count < max_retries - 1:
                        broader_query = self._broaden_search_query(original_query, retry_count + 1)
                        if broader_query != state["query"]:
                            state["query"] = broader_query
                            retry_count += 1
                            continue
                    
                    # If we can't broaden further, return no results
                    state["result"] = result
                    return state
                    
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
        
        return state
    
    def _execute_single_query(self, query: str) -> list:
        """Execute a single query and return formatted results"""
        # Configure query job with safety limits
        job_config = bigquery.QueryJobConfig()
        job_config.maximum_bytes_billed = self.bytes_limit
        job_config.use_query_cache = True  # Use cached results when possible
        
        # Execute the query
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result(timeout=QUERY_TIMEOUT)
        
        # Format results as list of lists
        columns = [field.name for field in results.schema]
        rows = list(results)
        
        if rows:
            # Add column headers as first row
            formatted_result = [columns]
            # Add data rows - respect the LIMIT from SQL query
            # Safety limit to prevent huge responses (max 1000 rows)
            max_rows = min(len(rows), 1000)
            for row in rows[:max_rows]:
                formatted_result.append([str(cell) for cell in row])
            return formatted_result
        else:
            return [["No data found"]]
    
    def _has_meaningful_results(self, result: list) -> bool:
        """Check if the query returned meaningful results"""
        return len(result) > 1 or (len(result) == 1 and result[0] != ["No data found"])
    
    def _broaden_search_query(self, original_query: str, attempt: int) -> str:
        """Broaden the search query by using related terms"""
        
        # Strategy 1: Replace exact matches with case-insensitive LIKE searches
        if attempt == 1:
            return self._convert_to_case_insensitive_search(original_query)
        
        # Strategy 2: Add related terms 
        elif attempt == 2:
            return self._add_related_terms(original_query)
        
        # Strategy 3: Fallback to genre/category search
        elif attempt == 3:
            return self._fallback_to_genre_search(original_query)
        
        return original_query
    
    def _convert_to_case_insensitive_search(self, query: str) -> str:
        """Convert exact IN UNNEST searches to case-insensitive LIKE searches"""
        
        # Pattern to find: 'Term' IN UNNEST(column)
        pattern = r"'([^']+)'\s+IN\s+UNNEST\(([^)]+)\)"
        
        def replace_with_like(match):
            term = match.group(1)
            column = match.group(2)
            return f"EXISTS(SELECT 1 FROM UNNEST({column}) AS item WHERE LOWER(item) LIKE '%{term.lower()}%')"
        
        return re.sub(pattern, replace_with_like, query, flags=re.IGNORECASE)
    
    def _add_related_terms(self, query: str) -> str:
        """Add related terms to the search"""
        
        # Find search terms in the query
        pattern = r"'([^']+)'\s+IN\s+UNNEST\(([^)]+)\)"
        matches = re.findall(pattern, query, flags=re.IGNORECASE)
        
        if not matches:
            return query
        
        # Build broader search with related terms
        modified_query = query
        for term, column in matches:
            term_lower = term.lower()
            related = self.related_terms.get(term_lower, [])
            
            if related:
                # Create a broader condition with related terms
                all_terms = [term_lower] + related
                conditions = []
                for t in all_terms:
                    conditions.append(f"LOWER(item) LIKE '%{t}%'")
                
                broader_condition = f"EXISTS(SELECT 1 FROM UNNEST({column}) AS item WHERE {' OR '.join(conditions)})"
                
                # Replace the original condition
                original_condition = f"'{term}' IN UNNEST({column})"
                modified_query = modified_query.replace(original_condition, broader_condition)
        
        return modified_query
    
    def _fallback_to_genre_search(self, query: str) -> str:
        """Fallback to genre-based search for very broad results"""
        
        # If searching for wedding-related content, try romance genre
        if any(term in query.lower() for term in ['wedding', 'marriage', 'bride', 'romantic']):
            # Add or modify to include romance genre
            if 'cd.genres' not in query:
                # Add genre condition if WHERE clause exists
                if 'WHERE' in query.upper():
                    query = query.replace('WHERE', "WHERE ('Romance' IN UNNEST(cd.genres) OR 'Romantic Comedy' IN UNNEST(cd.genres)) AND", 1)
                else:
                    # Add WHERE clause before GROUP BY
                    query = query.replace('GROUP BY', "WHERE ('Romance' IN UNNEST(cd.genres) OR 'Romantic Comedy' IN UNNEST(cd.genres)) GROUP BY")
        
        return query
    
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