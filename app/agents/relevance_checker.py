"""
Result Relevance Checker Agent
Analyzes if query results are relevant to user's question and retries if not
"""

import logging
from typing import List, Dict, Any
from langchain.chat_models import init_chat_model
from app.core.state import State
from app.agents.query_generator import generate_query
from app.agents.query_executor import execute_query
from app.core.config import LLM_MODEL, LLM_PROVIDER, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

class RelevanceChecker:
    """Checks if query results are relevant to user's question and retries if needed"""
    
    def __init__(self):
        self.llm = init_chat_model(
            model=LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=LLM_TEMPERATURE
        )
        self.max_retries = 3
        
    def check_and_retry(self, state: State) -> State:
        """Main logic: check relevance and retry if needed"""
        
        original_question = state.get("question", "")
        original_query = state.get("query", "")
        current_results = state.get("result", [])
        
        if not original_question or not current_results:
            return state
            
        logger.info(f"Checking relevance for question: {original_question[:100]}...")
        
        for attempt in range(self.max_retries):
            # Check if current results are relevant
            relevance_score, feedback = self._analyze_relevance(
                original_question, 
                state.get("query", ""), 
                current_results
            )
            
            logger.info(f"Attempt {attempt + 1}: Relevance score = {relevance_score}")
            
            # If relevance is good, return results
            if relevance_score >= 7:  # Scale of 1-10
                if attempt > 0:
                    state["relevance_info"] = {
                        "attempts": attempt + 1,
                        "final_score": relevance_score,
                        "message": f"Found relevant results on attempt {attempt + 1}"
                    }
                return state
            
            # If relevance is poor and we have retries left, try to improve
            if attempt < self.max_retries - 1:
                logger.info(f"Poor relevance ({relevance_score}/10). Attempting to refine query...")
                
                # Generate a refined query based on feedback
                refined_query = self._refine_query(original_question, state.get("query", ""), feedback)
                
                if refined_query and refined_query != state.get("query", ""):
                    # Execute the refined query
                    state["query"] = refined_query
                    state = execute_query(state)
                    current_results = state.get("result", [])
                    logger.info(f"Refined query executed, got {len(current_results)} result rows")
                else:
                    logger.info("Could not generate meaningful refinement, stopping retries")
                    break
            else:
                logger.info(f"Max retries reached. Final relevance: {relevance_score}/10")
                state["relevance_info"] = {
                    "attempts": self.max_retries,
                    "final_score": relevance_score,
                    "message": f"Results may not fully match your question after {self.max_retries} attempts"
                }
        
        return state
    
    def _analyze_relevance(self, question: str, query: str, results: List) -> tuple[float, str]:
        """Analyze how well the results match the original question"""
        
        # Format results for analysis (limit to first few rows)
        results_sample = self._format_results_for_analysis(results)
        
        prompt = f"""Analyze if these SQL query results are relevant to the user's question.

USER'S QUESTION: {question}

SQL QUERY USED: {query}

RESULTS SAMPLE:
{results_sample}

Please evaluate:
1. Do the results directly answer the user's question?
2. Are the column names/data types what the user would expect?
3. Does the query seem to have targeted the right tables/concepts?

Rate the relevance on a scale of 1-10 where:
- 10 = Perfect match, exactly what user asked for
- 7-9 = Good match, mostly relevant with minor issues
- 4-6 = Partially relevant but missing key aspects
- 1-3 = Poor match, results don't answer the question

Respond in this format:
SCORE: [number 1-10]
FEEDBACK: [brief explanation of why this score, and what could be improved if score < 7]"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse the response
            score_line = [line for line in content.split('\n') if line.startswith('SCORE:')]
            feedback_line = [line for line in content.split('\n') if line.startswith('FEEDBACK:')]
            
            score = 5  # Default medium score
            if score_line:
                try:
                    score = float(score_line[0].replace('SCORE:', '').strip())
                    score = max(1, min(10, score))  # Clamp to 1-10
                except:
                    pass
            
            feedback = ""
            if feedback_line:
                feedback = feedback_line[0].replace('FEEDBACK:', '').strip()
            
            return score, feedback
            
        except Exception as e:
            logger.error(f"Error analyzing relevance: {e}")
            return 5.0, "Could not analyze relevance"
    
    def _format_results_for_analysis(self, results: List) -> str:
        """Format results for LLM analysis (limit size)"""
        
        if not results or len(results) == 0:
            return "No results returned"
        
        if results == [["No data found"]]:
            return "No data found"
        
        # Take first row (headers) and up to 3 data rows
        sample_results = results[:4] if len(results) > 4 else results
        
        formatted = []
        for i, row in enumerate(sample_results):
            if i == 0:
                formatted.append(f"Headers: {row}")
            else:
                formatted.append(f"Row {i}: {row}")
        
        if len(results) > 4:
            formatted.append(f"... and {len(results) - 4} more rows")
        
        return "\n".join(formatted)
    
    def _refine_query(self, question: str, current_query: str, feedback: str) -> str:
        """Generate a refined query based on relevance feedback"""
        
        prompt = f"""The current SQL query doesn't fully answer the user's question. Please generate a better query.

USER'S ORIGINAL QUESTION: {question}

CURRENT QUERY:
{current_query}

RELEVANCE FEEDBACK: {feedback}

Please generate an improved SQL query that better addresses the user's question. Consider:
1. Are we querying the right tables?
2. Are we selecting the right columns?
3. Are the filters appropriate?
4. Is the aggregation/grouping correct?

Return ONLY the improved SQL query, no explanations."""

        try:
            response = self.llm.invoke(prompt)
            refined_query = response.content.strip()
            
            # Clean up the query
            if refined_query.startswith('```sql'):
                refined_query = refined_query.replace('```sql', '').replace('```', '').strip()
            elif refined_query.startswith('```'):
                refined_query = refined_query.replace('```', '').strip()
            
            logger.info(f"Generated refined query: {refined_query[:100]}...")
            return refined_query
            
        except Exception as e:
            logger.error(f"Error refining query: {e}")
            return ""

def check_relevance_and_retry(state: State) -> State:
    """Entry point for relevance checking and retry"""
    checker = RelevanceChecker()
    return checker.check_and_retry(state) 