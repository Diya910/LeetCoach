"""
Dynamic Optimize Agent with context-aware code optimization.
"""

import json
from typing import Dict, Any
from ..models.request_models import AgentType
from .base_dynamic_agent import BaseDynamicAgent


class DynamicOptimizeAgent(BaseDynamicAgent):
    """Dynamic agent that provides intelligent code optimization."""
    
    def __init__(self):
        """Initialize the dynamic optimize agent."""
        super().__init__(AgentType.OPTIMIZE)
    
    def get_agent_system_prompt(self) -> str:
        """Get the detailed system prompt for optimization."""
        return """You are the LeetCoach Optimization Agent, an expert in code improvement and performance optimization.

YOUR MISSION: Analyze user code and provide intelligent optimization suggestions that improve performance, readability, and maintainability.

OPTIMIZATION PHILOSOPHY:
- Always understand the current code first
- Identify specific bottlenecks and inefficiencies
- Provide concrete, actionable improvements
- Explain the reasoning behind each optimization
- Consider multiple optimization dimensions

OPTIMIZATION DIMENSIONS:
1. TIME COMPLEXITY: Reduce algorithmic complexity
2. SPACE COMPLEXITY: Minimize memory usage
3. READABILITY: Improve code clarity and structure
4. PERFORMANCE: Optimize for runtime efficiency
5. BEST PRACTICES: Apply language-specific optimizations

ANALYSIS FRAMEWORK:
1. CODE UNDERSTANDING: What does the current code do?
2. COMPLEXITY ANALYSIS: Current time/space complexity
3. BOTTLENECK IDENTIFICATION: Where are the inefficiencies?
4. OPTIMIZATION OPPORTUNITIES: What can be improved?
5. TRADE-OFF ANALYSIS: What are the costs/benefits?

RESPONSE STRUCTURE:
1. Current code analysis
2. Identified optimization opportunities
3. Optimized code solution
4. Explanation of improvements
5. Complexity comparison (before/after)
6. Trade-offs and considerations

ADAPTIVE BEHAVIOR:
- Working code: Focus on performance optimization
- Buggy code: Fix bugs first, then optimize
- Simple code: Suggest algorithmic improvements
- Complex code: Refactor for clarity and efficiency
- Beginner level: Explain basic optimizations
- Advanced level: Discuss advanced techniques"""

    def get_dynamic_user_prompt(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        """Generate dynamic optimization prompt based on context."""
        
        optimization_focus = self._determine_optimization_focus(context_data, agent_config)
        code_analysis = self._analyze_code_quality(context_data)
        optimization_level = self._determine_optimization_level(context_data)
        
        formatted_context = self.format_context_for_prompt(context_data)
        
        return f"""CODE OPTIMIZATION REQUEST:

{formatted_context}

OPTIMIZATION ANALYSIS:
- Primary Focus: {optimization_focus}
- Code Quality: {code_analysis}
- Optimization Level: {optimization_level}
- Target Areas: {agent_config.get('specific_focus', 'General optimization')}

OPTIMIZATION INSTRUCTIONS:
1. Analyze the current code for inefficiencies
2. Identify specific optimization opportunities
3. Provide optimized code with improvements
4. Explain each optimization made
5. Compare before/after complexity
6. Discuss any trade-offs

Focus on {optimization_focus} while maintaining code correctness and readability."""
    
    def _determine_optimization_focus(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        """Determine what to focus optimization on."""
        user_code = context_data.get('user_code', {})
        problem = context_data.get('problem', {})
        
        # Check agent config for focus areas
        focus_areas = agent_config.get('dynamic_parameters', {}).get('focus_areas', [])
        if focus_areas:
            return ', '.join(focus_areas)
        
        # Analyze code to determine focus
        if not user_code or not user_code.get('code'):
            return "general optimization principles"
        
        code = user_code.get('code', '')
        
        # Check for obvious inefficiencies
        if 'for' in code and code.count('for') > 2:
            return "time complexity reduction (multiple nested loops detected)"
        elif 'while' in code and 'for' in code:
            return "algorithmic efficiency (mixed loop patterns)"
        elif len(code.split('\n')) > 20:
            return "code structure and readability"
        elif problem.get('difficulty') == 'Hard':
            return "advanced algorithmic optimization"
        else:
            return "time and space complexity optimization"
    
    def _analyze_code_quality(self, context_data: Dict[str, Any]) -> str:
        """Analyze current code quality."""
        user_code = context_data.get('user_code', {})
        if not user_code or not user_code.get('code'):
            return "No code to analyze"
        
        code = user_code.get('code', '')
        issues = []
        
        # Check for common issues
        if code.count('for') >= 3:
            issues.append("multiple nested loops")
        if 'list(' in code or 'dict(' in code:
            issues.append("potential inefficient conversions")
        if code.count('append') > 5:
            issues.append("frequent list operations")
        if 'sort()' in code and 'for' in code:
            issues.append("sorting within loops")
        
        if issues:
            return f"Issues detected: {', '.join(issues)}"
        elif user_code.get('is_working'):
            return "Working code, ready for optimization"
        else:
            return "Code needs debugging before optimization"
    
    def _determine_optimization_level(self, context_data: Dict[str, Any]) -> str:
        """Determine level of optimization to apply."""
        problem = context_data.get('problem', {})
        user_history = context_data.get('user_history', [])
        
        difficulty = problem.get('difficulty', 'Medium')
        user_experience = len(user_history)
        
        if difficulty == 'Hard' or user_experience > 20:
            return "Advanced (algorithmic + implementation optimizations)"
        elif difficulty == 'Medium' or user_experience > 5:
            return "Intermediate (efficiency + readability improvements)"
        else:
            return "Basic (fundamental optimizations)"
    
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        """Extract structured data from optimization response."""
        return {
            "optimized_code": self.extract_code_from_response(llm_response),
            "improvements": self._extract_improvements(llm_response),
            "complexity_analysis": self._extract_complexity_comparison(llm_response),
            "trade_offs": self._extract_trade_offs(llm_response),
            "optimization_techniques": self._extract_techniques(llm_response)
        }
    
    def _extract_improvements(self, response: str) -> list:
        """Extract specific improvements made."""
        improvements = self.extract_list_items(response, ['improved', 'optimized', 'reduced', 'eliminated'])
        
        # Also look for common optimization patterns
        optimization_keywords = [
            'hash map', 'memoization', 'two pointer', 'sliding window',
            'binary search', 'early termination', 'space optimization'
        ]
        
        for keyword in optimization_keywords:
            if keyword in response.lower():
                improvements.append(f"Applied {keyword} technique")
        
        return improvements[:5]
    
    def _extract_complexity_comparison(self, response: str) -> Dict[str, str]:
        """Extract before/after complexity comparison."""
        import re
        
        complexity_info = {}
        
        # Look for complexity mentions
        time_pattern = r'time.*?O\([^)]+\).*?O\([^)]+\)'
        space_pattern = r'space.*?O\([^)]+\).*?O\([^)]+\)'
        
        time_match = re.search(time_pattern, response, re.IGNORECASE)
        space_match = re.search(space_pattern, response, re.IGNORECASE)
        
        if time_match:
            complexity_info['time_complexity'] = time_match.group(0)
        if space_match:
            complexity_info['space_complexity'] = space_match.group(0)
        
        return complexity_info
    
    def _extract_trade_offs(self, response: str) -> str:
        """Extract trade-offs discussion."""
        trade_off_indicators = ['trade-off', 'however', 'but', 'although', 'while']
        
        sentences = response.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in trade_off_indicators):
                return sentence.strip()
        
        return "No significant trade-offs identified"
    
    def _extract_techniques(self, response: str) -> list:
        """Extract optimization techniques used."""
        techniques = [
            'memoization', 'dynamic programming', 'hash map', 'two pointer',
            'sliding window', 'binary search', 'greedy', 'divide and conquer',
            'early termination', 'caching', 'preprocessing'
        ]
        
        found_techniques = []
        for technique in techniques:
            if technique in response.lower():
                found_techniques.append(technique)
        
        return found_techniques[:5]
    
    def get_technical_terms_for_scoring(self) -> list:
        """Get technical terms for optimization scoring."""
        return [
            'optimize', 'efficiency', 'complexity', 'performance', 'algorithm',
            'time', 'space', 'memory', 'runtime', 'bottleneck', 'improve',
            'reduce', 'eliminate', 'faster', 'better', 'optimal'
        ]
