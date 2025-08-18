"""
Dynamic Hint Agent with context-aware prompting.
"""

import json
from typing import Dict, Any
from ..models.request_models import AgentType
from .base_dynamic_agent import BaseDynamicAgent


class DynamicHintAgent(BaseDynamicAgent):
    """Dynamic agent that provides intelligent, context-aware hints."""
    
    def __init__(self):
        """Initialize the dynamic hint agent."""
        super().__init__(AgentType.HINT)
    
    def get_agent_system_prompt(self) -> str:
        """Get the detailed system prompt that defines the hint agent's behavior."""
        return """You are the LeetCoach Hint Agent, an intelligent coding mentor.

YOUR MISSION: Guide users to discover solutions through strategic hints.

HINT PHILOSOPHY:
- Never give away the solution directly
- Build understanding through progressive revelation
- Adapt to user's current level and context
- Focus on teaching problem-solving patterns

HINT LEVELS:
1. NUDGE: Subtle direction
2. PATTERN: Point toward technique
3. APPROACH: Suggest algorithm  
4. STRUCTURE: Provide pseudocode guidance
5. DETAILED: Implementation guidance (only when very stuck)

CONTEXT AWARENESS:
- Analyze exactly where user is stuck
- Reference their specific code
- Adapt to their experience level
- Build upon existing progress

RESPONSE STRUCTURE:
1. Acknowledge their situation
2. Provide level-appropriate hint
3. Explain why this helps
4. Suggest next steps
5. Encourage them

ADAPTIVE BEHAVIOR:
- Beginner: More explanation, encouragement
- Intermediate: Focus on patterns, efficiency
- Advanced: Subtle hints, optimization
- Long stuck time: More direct guidance
- Making progress: Lighter touch"""

    def get_dynamic_user_prompt(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        """Generate dynamic user prompt based on context."""
        hint_level = self._determine_hint_level(context_data, agent_config)
        stuck_point = self._analyze_stuck_point(context_data)
        user_level = self._assess_user_level(context_data)
        
        formatted_context = self.format_context_for_prompt(context_data)
        
        return f"""HINT REQUEST:

{formatted_context}

ANALYSIS:
- Optimal Hint Level: {hint_level}/5
- User Level: {user_level}
- Stuck Point: {stuck_point}
- Focus: {agent_config.get('specific_focus', 'General guidance')}

Provide a Level {hint_level} hint that helps them discover the solution without giving it away."""
    
    def _determine_hint_level(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> int:
        """Determine optimal hint level based on context."""
        level = 3  # Default
        
        user_code = context_data.get('user_code', {})
        if not user_code or not user_code.get('code'):
            level = 2  # Start with patterns if no code
        elif user_code.get('is_working') == False:
            level = 4  # More help if not working
        
        # Time factor
        time_spent = context_data.get('page_context', {}).get('time_spent_minutes', 0)
        if time_spent > 30:
            level += 1
        
        # Difficulty factor
        difficulty = context_data.get('problem', {}).get('difficulty', 'Medium')
        if difficulty == 'Hard':
            level += 1
        elif difficulty == 'Easy':
            level -= 1
        
        return max(1, min(5, level))
    
    def _analyze_stuck_point(self, context_data: Dict[str, Any]) -> str:
        """Analyze where user is stuck."""
        user_code = context_data.get('user_code', {})
        if not user_code or not user_code.get('code'):
            return "Getting started"
        
        code = user_code.get('code', '')
        if 'def ' in code and len(code.split('\n')) < 3:
            return "Function structure but no implementation"
        elif 'for ' in code and 'if ' not in code:
            return "Loop without logic"
        elif len(code) > 200 and not user_code.get('is_working'):
            return "Complex code not working"
        else:
            return "General implementation"
    
    def _assess_user_level(self, context_data: Dict[str, Any]) -> str:
        """Assess user experience level."""
        user_code = context_data.get('user_code', {})
        code = user_code.get('code', '') if user_code else ''
        
        quality_score = 0
        if 'def ' in code: quality_score += 1
        if any(word in code for word in ['try:', 'enumerate', 'zip']): quality_score += 1
        if '#' in code: quality_score += 1  # Comments
        
        if quality_score >= 2:
            return "Intermediate"
        elif quality_score >= 1:
            return "Beginner-Intermediate"
        else:
            return "Beginner"
    
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        """Extract structured data from hint response."""
        return {
            "hint_text": llm_response,
            "hint_level": self._extract_hint_level(llm_response),
            "key_concepts": self._extract_concepts(llm_response),
            "next_steps": self.extract_list_items(llm_response, ['next', 'try', 'consider'])
        }
    
    def _extract_hint_level(self, response: str) -> int:
        """Extract hint level from response."""
        import re
        level_match = re.search(r'level\s*(\d)', response.lower())
        return int(level_match.group(1)) if level_match else 3
    
    def _extract_concepts(self, response: str) -> list:
        """Extract key concepts from response."""
        concepts = ['hash map', 'two pointer', 'sliding window', 'binary search', 'recursion']
        return [c for c in concepts if c in response.lower()][:3]
