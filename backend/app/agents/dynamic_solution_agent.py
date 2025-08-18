"""
Dynamic Solution Agent with comprehensive explanations.
"""

from typing import Dict, Any
from ..models.request_models import AgentType
from .base_dynamic_agent import BaseDynamicAgent


class DynamicSolutionAgent(BaseDynamicAgent):
    """Dynamic agent for comprehensive solution explanations."""
    
    def __init__(self):
        super().__init__(AgentType.SOLUTION)
    
    def get_agent_system_prompt(self) -> str:
        return """You are the LeetCoach Solution Agent, an expert educator specializing in comprehensive solution explanations.

YOUR MISSION: Provide complete, educational solution explanations that build deep understanding.

EXPLANATION PHILOSOPHY:
- Start with problem understanding and intuition
- Present multiple approaches when relevant
- Explain the thinking process, not just the solution
- Build from simple to complex approaches
- Focus on learning and pattern recognition

SOLUTION STRUCTURE:
1. Problem analysis and key insights
2. Approach explanation with intuition
3. Step-by-step algorithm breakdown
4. Complete code implementation
5. Complexity analysis
6. Alternative approaches comparison
7. Edge cases and considerations

EDUCATIONAL FOCUS:
- Teach problem-solving patterns
- Explain decision-making process
- Connect to broader algorithmic concepts
- Help recognize similar problems
- Build transferable skills"""

    def get_dynamic_user_prompt(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        solution_depth = self._determine_solution_depth(context_data, agent_config)
        explanation_style = self._determine_explanation_style(context_data)
        
        formatted_context = self.format_context_for_prompt(context_data)
        
        return f"""SOLUTION EXPLANATION REQUEST:

{formatted_context}

EXPLANATION CONFIGURATION:
- Solution Depth: {solution_depth}
- Explanation Style: {explanation_style}
- Include Multiple Approaches: {agent_config.get('include_multiple_approaches', True)}
- Focus on Optimal: {agent_config.get('include_optimal_solution', True)}

Provide comprehensive solution explanation with educational focus."""
    
    def _determine_solution_depth(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        problem = context_data.get('problem', {})
        user_code = context_data.get('user_code', {})
        
        if user_code and user_code.get('is_working'):
            return "Optimization and alternative approaches"
        elif problem.get('difficulty') == 'Hard':
            return "Deep explanation with multiple approaches"
        else:
            return "Complete solution with step-by-step breakdown"
    
    def _determine_explanation_style(self, context_data: Dict[str, Any]) -> str:
        user_history = context_data.get('user_history', [])
        
        if len(user_history) > 15:
            return "Advanced with focus on patterns"
        elif len(user_history) > 5:
            return "Intermediate with detailed reasoning"
        else:
            return "Beginner-friendly with examples"
    
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        return {
            "solution_code": self.extract_code_from_response(llm_response),
            "approaches": self._extract_approaches(llm_response),
            "key_insights": self._extract_insights(llm_response),
            "complexity_info": self._extract_complexity_info(llm_response),
            "patterns": self._extract_patterns(llm_response)
        }
    
    def _extract_approaches(self, response: str) -> list:
        approaches = []
        import re
        
        # Look for approach headers
        approach_pattern = r'(?:approach|solution|method)\s*\d*:?\s*([^\n]+)'
        matches = re.findall(approach_pattern, response, re.IGNORECASE)
        
        return [match.strip() for match in matches[:3]]
    
    def _extract_insights(self, response: str) -> list:
        return self.extract_list_items(response, ['insight', 'key', 'important', 'notice'])
    
    def _extract_complexity_info(self, response: str) -> Dict[str, str]:
        import re
        complexity = {}
        
        time_match = re.search(r'time.*?O\([^)]+\)', response, re.IGNORECASE)
        space_match = re.search(r'space.*?O\([^)]+\)', response, re.IGNORECASE)
        
        if time_match:
            complexity['time'] = time_match.group(0)
        if space_match:
            complexity['space'] = space_match.group(0)
        
        return complexity
    
    def _extract_patterns(self, response: str) -> list:
        patterns = ['two pointer', 'sliding window', 'dynamic programming', 'greedy', 'divide and conquer']
        return [p for p in patterns if p in response.lower()][:3]
