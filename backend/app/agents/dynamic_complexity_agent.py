"""
Dynamic Complexity Agent with detailed algorithmic analysis.
"""

from typing import Dict, Any
from ..models.request_models import AgentType
from .base_dynamic_agent import BaseDynamicAgent


class DynamicComplexityAgent(BaseDynamicAgent):
    """Dynamic agent for intelligent complexity analysis."""
    
    def __init__(self):
        super().__init__(AgentType.COMPLEXITY)
    
    def get_agent_system_prompt(self) -> str:
        return """You are the LeetCoach Complexity Agent, an expert in algorithmic complexity analysis.

YOUR MISSION: Provide detailed, educational complexity analysis that helps users understand performance characteristics.

ANALYSIS APPROACH:
- Examine code step by step
- Identify all operations and their costs
- Explain reasoning behind complexity calculations
- Discuss best/average/worst cases when relevant
- Compare with alternative approaches

RESPONSE STRUCTURE:
1. Code walkthrough and operation identification
2. Time complexity analysis with explanation
3. Space complexity analysis with explanation
4. Complexity breakdown by code sections
5. Comparison with optimal solutions
6. Performance implications and recommendations

EDUCATIONAL FOCUS:
- Teach complexity analysis thinking
- Explain why certain operations have specific costs
- Help build intuition for performance analysis
- Connect complexity to real-world impact"""

    def get_dynamic_user_prompt(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        analysis_depth = self._determine_analysis_depth(context_data)
        focus_areas = self._identify_complexity_focus(context_data, agent_config)
        
        formatted_context = self.format_context_for_prompt(context_data)
        
        return f"""COMPLEXITY ANALYSIS REQUEST:

{formatted_context}

ANALYSIS CONFIGURATION:
- Analysis Depth: {analysis_depth}
- Focus Areas: {focus_areas}
- Educational Level: {self._assess_user_level(context_data)}

Provide detailed complexity analysis with step-by-step reasoning."""
    
    def _determine_analysis_depth(self, context_data: Dict[str, Any]) -> str:
        user_code = context_data.get('user_code', {})
        problem = context_data.get('problem', {})
        
        if not user_code or len(user_code.get('code', '')) < 50:
            return "Basic analysis with educational focus"
        elif problem.get('difficulty') == 'Hard':
            return "Deep analysis with multiple scenarios"
        else:
            return "Comprehensive analysis with optimization suggestions"
    
    def _identify_complexity_focus(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        focus = agent_config.get('specific_focus', '')
        if focus:
            return focus
        
        user_code = context_data.get('user_code', {})
        code = user_code.get('code', '') if user_code else ''
        
        if 'for' in code and code.count('for') > 1:
            return "Time complexity (nested loops detected)"
        elif any(word in code for word in ['list', 'dict', 'set']):
            return "Space complexity (data structures usage)"
        else:
            return "Both time and space complexity"
    
    def _assess_user_level(self, context_data: Dict[str, Any]) -> str:
        user_history = context_data.get('user_history', [])
        complexity_requests = [h for h in user_history if h.get('type') == 'complexity']
        
        if len(complexity_requests) > 3:
            return "Advanced"
        elif len(complexity_requests) > 1:
            return "Intermediate"
        else:
            return "Beginner"
    
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        return {
            "time_complexity": self._extract_time_complexity(llm_response),
            "space_complexity": self._extract_space_complexity(llm_response),
            "complexity_breakdown": self._extract_breakdown(llm_response),
            "optimization_suggestions": self.extract_list_items(llm_response, ['optimize', 'improve', 'better'])
        }
    
    def _extract_time_complexity(self, response: str) -> str:
        import re
        time_pattern = r'time complexity.*?O\([^)]+\)'
        match = re.search(time_pattern, response, re.IGNORECASE)
        return match.group(0) if match else "Not specified"
    
    def _extract_space_complexity(self, response: str) -> str:
        import re
        space_pattern = r'space complexity.*?O\([^)]+\)'
        match = re.search(space_pattern, response, re.IGNORECASE)
        return match.group(0) if match else "Not specified"
    
    def _extract_breakdown(self, response: str) -> Dict[str, str]:
        breakdown = {}
        if 'loop' in response.lower():
            breakdown['loops'] = "Loop complexity analysis provided"
        if 'recursive' in response.lower():
            breakdown['recursion'] = "Recursion complexity analysis provided"
        return breakdown
