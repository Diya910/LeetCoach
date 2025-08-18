"""
Dynamic Counter Question Agent for interview preparation.
"""

from typing import Dict, Any
from ..models.request_models import AgentType
from .base_dynamic_agent import BaseDynamicAgent


class DynamicCounterAgent(BaseDynamicAgent):
    """Dynamic agent for generating interview-style counter questions."""
    
    def __init__(self):
        super().__init__(AgentType.COUNTER)
    
    def get_agent_system_prompt(self) -> str:
        return """You are the LeetCoach Counter Question Agent, an expert interviewer specializing in probing questions.

YOUR MISSION: Generate intelligent counter questions that test deeper understanding and reveal knowledge gaps.

QUESTION PHILOSOPHY:
- Probe assumptions and edge cases
- Test understanding of trade-offs
- Explore alternative scenarios
- Challenge the approach
- Assess problem-solving depth

QUESTION TYPES:
1. CLARIFYING: Requirements and constraints
2. EDGE_CASE: Boundary conditions and special cases
3. OPTIMIZATION: Performance and efficiency challenges
4. SCALING: How solution handles growth
5. ALTERNATIVES: Different approaches and trade-offs

ADAPTIVE QUESTIONING:
- Match question difficulty to user level
- Build on their current solution
- Focus on weak points in their approach
- Encourage deeper thinking
- Simulate real interview pressure"""

    def get_dynamic_user_prompt(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        question_type = agent_config.get('dynamic_parameters', {}).get('question_type', 'clarifying')
        difficulty_level = self._determine_question_difficulty(context_data)
        focus_area = self._identify_focus_area(context_data, agent_config)
        
        formatted_context = self.format_context_for_prompt(context_data)
        
        return f"""COUNTER QUESTION GENERATION:

{formatted_context}

QUESTION CONFIGURATION:
- Question Type: {question_type}
- Difficulty Level: {difficulty_level}
- Focus Area: {focus_area}
- Number of Questions: {agent_config.get('dynamic_parameters', {}).get('num_questions', 5)}

Generate insightful counter questions that an interviewer would ask to test deeper understanding."""
    
    def _determine_question_difficulty(self, context_data: Dict[str, Any]) -> str:
        problem = context_data.get('problem', {})
        user_code = context_data.get('user_code', {})
        
        if problem.get('difficulty') == 'Hard' or (user_code and len(user_code.get('code', '')) > 200):
            return "Advanced"
        elif problem.get('difficulty') == 'Medium':
            return "Intermediate"
        else:
            return "Basic"
    
    def _identify_focus_area(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        focus = agent_config.get('specific_focus', '')
        if focus:
            return focus
        
        user_code = context_data.get('user_code', {})
        if user_code and user_code.get('code'):
            code = user_code.get('code', '')
            if 'for' in code and code.count('for') > 1:
                return "Time complexity and optimization"
            elif any(word in code for word in ['list', 'dict', 'set']):
                return "Data structure choices and space usage"
        
        return "General approach and edge cases"
    
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        return {
            "questions": self._extract_questions(llm_response),
            "question_categories": self._categorize_questions(llm_response),
            "difficulty_assessment": self._assess_question_difficulty(llm_response)
        }
    
    def _extract_questions(self, response: str) -> list:
        import re
        questions = []
        
        # Look for numbered questions
        numbered = re.findall(r'\d+\.\s*([^?]*\?)', response)
        questions.extend(numbered)
        
        # Look for bullet point questions
        bullets = re.findall(r'[-*•]\s*([^?]*\?)', response)
        questions.extend(bullets)
        
        # Look for standalone questions
        standalone = re.findall(r'([A-Z][^.!?]*\?)', response)
        questions.extend(standalone)
        
        return [q.strip() for q in questions[:8]]  # Limit to 8 questions
    
    def _categorize_questions(self, response: str) -> Dict[str, int]:
        categories = {
            'clarifying': 0,
            'edge_case': 0,
            'optimization': 0,
            'scaling': 0,
            'alternative': 0
        }
        
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['what if', 'clarify', 'assume']):
            categories['clarifying'] += 1
        if any(word in response_lower for word in ['edge', 'boundary', 'empty', 'null']):
            categories['edge_case'] += 1
        if any(word in response_lower for word in ['optimize', 'faster', 'efficient']):
            categories['optimization'] += 1
        if any(word in response_lower for word in ['scale', 'large', 'million']):
            categories['scaling'] += 1
        if any(word in response_lower for word in ['alternative', 'different', 'another']):
            categories['alternative'] += 1
        
        return categories
    
    def _assess_question_difficulty(self, response: str) -> str:
        advanced_terms = ['distributed', 'concurrent', 'scalability', 'architecture']
        if any(term in response.lower() for term in advanced_terms):
            return "Advanced"
        elif 'optimize' in response.lower() or 'complexity' in response.lower():
            return "Intermediate"
        else:
            return "Basic"
