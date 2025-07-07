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
        # print({a: self.schema_info})
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
    
    def _extract_limit_from_question(self, question: str) -> int:
        """Extracts a limit from the user's question if specified."""
        import re
        
        question_lower = question.lower()
        
        # Patterns to look for numbers that indicate limit
        patterns = [
            r'top\s+(\d+)',           # "top 5", "top 100"
            r'first\s+(\d+)',         # "first 20", "first 50" 
            r'show\s+me\s+(\d+)',     # "show me 10", "show me 50"
            r'give\s+me\s+(\d+)',     # "give me 5", "give me 25"
            r'list\s+(\d+)',          # "list 10", "list 20"
            r'get\s+(\d+)',           # "get 15", "get 30"
            r'(\d+)\s+most',          # "5 most popular", "10 most"
            r'(\d+)\s+best',          # "3 best", "7 best"
            r'(\d+)\s+worst',         # "5 worst", "8 worst"
            r'(\d+)\s+highest',       # "10 highest", "20 highest"
            r'(\d+)\s+lowest',        # "5 lowest", "15 lowest"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                limit = int(match.group(1))
                # Reasonable limits to prevent huge queries
                if 1 <= limit <= 10000:
                    return limit
        
        return 10  # Default limit

    def generate_query(self, state: State) -> State:
        """Generate SQL query from user question"""
        try:
            question = state['question']
            schema_text = self._get_schema_text()
            print({schema_text})
            
            # Extract limit from question
            limit_from_question = self._extract_limit_from_question(question)
            
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

SPECIFIC ARRAY COLUMNS IN CONTENT_DIMENSION:
12. These columns are ARRAY<STRING> and need special handling:
    - cd.genres (movie genres like "Drama", "Comedy")
    - cd.production_countries (countries like "France", "Germany") 
    - cd.production_companies (company names)
    - cd.languages (language codes like "English", "French")
    - cd.tags (various tags and keywords)
13. NEVER use LIKE directly on these columns - always use UNNEST first
14. For country filtering: 'France' IN UNNEST(cd.production_countries)
15. For genre filtering: 'Drama' IN UNNEST(cd.genres)
16. To select array values: Use ARRAY_TO_STRING(cd.genres, ', ') to display as text

DATE/TIME HANDLING - CRITICAL:
17. For DATETIME columns (like local_show_datetime), use DATE() function first:
    - ✅ CORRECT: DATE(sf.local_show_datetime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    - ❌ WRONG: sf.local_show_datetime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)
18. For date range comparisons, ALWAYS use:
    - DATE_SUB(CURRENT_DATE(), INTERVAL X DAY/MONTH/YEAR) for past dates
    - DATE_ADD(CURRENT_DATE(), INTERVAL X DAY/MONTH/YEAR) for future dates
19. Never use TIMESTAMP_SUB with YEAR intervals - it's not supported in BigQuery
20. Convert DATETIME to DATE before comparison with DATE functions

STAR/CREW RELATIONSHIP HANDLING - IMPORTANT:
21. For director/actor/crew queries, use these tables:
    - star_dimension (sd): Contains star_name and star_id
    - content_star_mapping (csm): Links content to stars with crew_role
22. Common crew_role values: 'Director', 'Actor', 'Producer', 'Cinematographer', etc.
23. To find directors: JOIN content_star_mapping WHERE crew_role = 'Director'
24. Director names come from star_dimension.star_name, NOT content_dimension
25. Example pattern for director queries:
    ```sql
    JOIN content_star_mapping AS csm ON cd.content_id = csm.content_id
    JOIN star_dimension AS sd ON csm.star_id = sd.star_id
    WHERE csm.crew_role = 'Director'
    ```

LIMIT HANDLING:
26. If question mentions specific numbers like "top 5", "top 100", "first 20", use that number for LIMIT
27. If no specific number is mentioned, use LIMIT 10 as default
28. For "top N" questions, always include ORDER BY to make the ranking meaningful

COUNTRY NAME MAPPING:
29. CRITICAL: Use correct country names in streaming_country column:
    - ✅ CORRECT: sr.streaming_country = 'United States' (for US/USA)
    - ✅ CORRECT: sr.streaming_country = 'United Kingdom' (for UK)
    - ✅ CORRECT: sr.streaming_country = 'Germany' (for Germany/DE)
    - ❌ WRONG: sr.streaming_country = 'US' or 'USA'
30. Common country mappings for streaming_country:
    - US/USA → 'United States'
    - UK → 'United Kingdom'  
    - Canada → 'Canada'
    - Germany → 'Germany'
    - France → 'France'

GENRE MATCHING:
31. For exact genre matching, use these exact values:
    - Action/Adventure, Animation, Biopic, Classic, Comedy, Concert
    - Documentary, Drama, Family, History, Horror, Musical
    - Program, Romance, SciFi/Fantasy, Suspense/Thriller, War, Western
32. Use exact matching: 'Horror' IN UNNEST(cd.genres) AND 'Comedy' IN UNNEST(cd.genres)
33. ❌ WRONG: LIKE patterns on genres ('%horror%', '%comedy%')

GENRE NAME MAPPING:
34. CRITICAL: Use correct genre names - common user terms map to database genres:
    - Mystery/Detective/Crime → 'Suspense/Thriller'
    - SciFi/Science Fiction → 'SciFi/Fantasy'
    - Action/Adventure movies → 'Action/Adventure'
    - Kids/Children films → 'Family'
35. ❌ WRONG: Using user terms directly: 'Mystery', 'SciFi', 'Kids'
36. ✅ CORRECT: Using database genre names: 'Suspense/Thriller', 'SciFi/Fantasy', 'Family'

GENDER VALUE MAPPING:
37. CRITICAL: Use lowercase gender values in star_dimension.gender column:
    - Female/FEMALE → 'female'
    - Male/MALE → 'male'  
    - Non-binary/NON-BINARY → 'non-binary'
38. ❌ WRONG: Using capitalized values: 'Female', 'Male', 'Non-Binary'
39. ✅ CORRECT: Using lowercase values: 'female', 'male', 'non-binary'

SMART SEARCH STRATEGY:
34. Start with exact search terms for precision
35. The system will automatically retry with broader searches if no results found:
    - Attempt 1: Exact term matching (e.g., 'Wedding' IN UNNEST(cd.tags))
    - Attempt 2: Case-insensitive partial matching (e.g., LOWER(item) LIKE '%wedding%')
    - Attempt 3: Related terms (e.g., wedding -> romance, romantic, marriage, bride, love)
    - Attempt 4: Genre fallback (e.g., wedding-related -> Romance genre)
36. Don't pre-optimize queries - let the retry system handle broadening automatically

EFFICIENCY GUIDELINES:
32. Add date/time filters ONLY when:
    - Question mentions time periods ("last month", "recent", "this year")
    - Question asks for trends or time-based analysis
33. Add geographic filters ONLY when:
    - Question mentions specific locations ("UK", "London", "Europe")
    - Question asks for regional analysis
34. For "top N" or "most/least" questions, use ORDER BY with LIMIT
35. Select only the columns needed to answer the question
36. Use COUNT(*) for counting records

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

❌ WRONG - using LIKE on production_countries array:
```sql
WHERE cd.production_countries LIKE '%France%'  -- ERROR: production_countries is ARRAY<STRING>
```

✅ CORRECT - proper country filtering:
```sql
WHERE 'France' IN UNNEST(cd.production_countries)  -- For exact match
-- OR for partial match:
WHERE EXISTS(SELECT 1 FROM UNNEST(cd.production_countries) AS country WHERE country LIKE '%France%')
```

❌ WRONG - selecting array column directly:
```sql
SELECT cd.genres  -- Will show as array format, not readable
```

✅ CORRECT - displaying array as readable text:
```sql
SELECT ARRAY_TO_STRING(cd.genres, ', ') AS genres  -- Shows as "Drama, Comedy, Action"
```

❌ WRONG - using TIMESTAMP_SUB with YEAR interval:
```sql
WHERE sf.local_show_datetime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)  -- ERROR: Not supported!
```

✅ CORRECT - proper date handling:
```sql
WHERE DATE(sf.local_show_datetime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)  -- Convert to DATE first
```

❌ WRONG - trying to get director from content_dimension:
```sql
SELECT cd.director_name  -- ERROR: director_name doesn't exist in content_dimension!
```

✅ CORRECT - proper director query using star tables:
```sql
JOIN content_star_mapping AS csm ON cd.content_id = csm.content_id
JOIN star_dimension AS sd ON csm.star_id = sd.star_id
WHERE csm.crew_role = 'Director'
SELECT sd.star_name  -- Get director name from star_dimension
```

❌ WRONG - using wrong country code:
```sql
WHERE sr.streaming_country = 'US'  -- ERROR: Should be 'United States'
```

✅ CORRECT - proper country name:
```sql
WHERE sr.streaming_country = 'United States'  -- For US/USA queries
```

❌ WRONG - using LIKE patterns on exact genre values:
```sql
WHERE EXISTS(SELECT 1 FROM UNNEST(cd.genres) AS item WHERE LOWER(item) LIKE '%horror%')  -- Unnecessary complexity
```

✅ CORRECT - exact genre matching:
```sql
WHERE 'Horror' IN UNNEST(cd.genres) AND 'Comedy' IN UNNEST(cd.genres)  -- Direct exact match
```

❌ WRONG - using singular column names that don't exist:
```sql
WHERE cd.production_country = 'France'  -- ERROR: Column is production_countries (plural)
WHERE cd.genre = 'Mystery'              -- ERROR: Column is genres (plural)
```

✅ CORRECT - using correct plural column names with array syntax:
```sql
WHERE 'France' IN UNNEST(cd.production_countries)     -- Correct plural column name
WHERE 'Suspense/Thriller' IN UNNEST(cd.genres)        -- Correct genre name (not 'Mystery')
```

❌ WRONG - using non-existent genre names:
```sql
WHERE 'Mystery' IN UNNEST(cd.genres)  -- ERROR: Genre is 'Suspense/Thriller', not 'Mystery'
```

✅ CORRECT - using exact genre names that exist:
```sql
WHERE 'Suspense/Thriller' IN UNNEST(cd.genres)  -- Mystery/thriller content
WHERE 'SciFi/Fantasy' IN UNNEST(cd.genres)      -- Science fiction content
WHERE 'Action/Adventure' IN UNNEST(cd.genres)   -- Action content
```

❌ WRONG - using wrong gender capitalization:
```sql
WHERE sd.gender = 'Female'  -- ERROR: Gender values are lowercase in database
WHERE sd.gender = 'Male'    -- ERROR: Should be 'male'
```

✅ CORRECT - using correct lowercase gender values:
```sql
WHERE sd.gender = 'female'  -- Correct lowercase for female directors/actors
WHERE sd.gender = 'male'    -- Correct lowercase for male directors/actors
WHERE sd.gender = 'non-binary'  -- Correct lowercase for non-binary
```

Return ONLY the SQL query, no explanations."""
            
            # Get LLM response and count tokens
            prompt_tokens = len(self.encoding.encode(prompt))
            response = self.llm.invoke(prompt)
            response_tokens = len(self.encoding.encode(response.content))
            
            # Clean up the query with the extracted limit
            query = self._clean_query(response.content, question, limit_from_question)
            
            # Update state
            state["query"] = query
            state["token_usage"]["query_tokens"] = prompt_tokens + response_tokens
            
        except Exception as e:
            state["query"] = ""
            state["result"] = [["Query Generation Error"], [str(e)]]
        
        return state
    
    def _clean_query(self, raw_query: str, question: str, limit: int) -> str:
        """Clean up the generated query"""
        import re
        
        query = raw_query.strip()
        
        # Remove markdown formatting if present
        if query.startswith('```sql'):
            query = query.replace('```sql', '').replace('```', '').strip()
        elif query.startswith('```'):
            query = query.replace('```', '').strip()
        
        # Handle LIMIT clause
        if 'LIMIT' in query.upper():
            # Replace existing LIMIT with the correct one
            query = re.sub(r'LIMIT\s+\d+', f'LIMIT {limit}', query, flags=re.IGNORECASE)
        else:
            # Add LIMIT if not present
            query = query.rstrip(';') + f' LIMIT {limit}'
        
        return query

def generate_query(state: State) -> State:
    """Entry point for query generation"""
    generator = QueryGenerator()
    return generator.generate_query(state) 