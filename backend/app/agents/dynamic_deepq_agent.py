"""
Dynamic Deep Question Agent for advanced technical exploration.
"""

from typing import Dict, Any
from ..models.request_models import AgentType
from .base_dynamic_agent import BaseDynamicAgent


class DynamicDeepQAgent(BaseDynamicAgent):
    """Dynamic agent for generating deep technical questions."""
    
    def __init__(self):
        super().__init__(AgentType.DEEPQ)
    
    def get_agent_system_prompt(self) -> str:
        return """You are the LeetCoach Deep Question Agent, an expert in advanced technical exploration.

YOUR MISSION: Generate profound questions that push the boundaries of understanding and explore advanced concepts.

DEEP QUESTION PHILOSOPHY:
- Explore system design implications
- Challenge fundamental assumptions
- Connect to real-world applications
- Probe advanced algorithmic concepts
- Test architectural thinking

QUESTION DOMAINS:
1. SYSTEM DESIGN: How would this scale in production?
2. ARCHITECTURE: What are the design trade-offs?
3. PERFORMANCE: How does this perform under stress?
4. RELIABILITY: What failure modes exist?
5. OPTIMIZATION: What advanced techniques apply?
6. THEORY: What are the theoretical foundations?

DEPTH LEVELS:
- CONCEPTUAL: Theoretical understanding
- PRACTICAL: Real-world application
- ARCHITECTURAL: System-level thinking
- RESEARCH: Cutting-edge considerations

Generate questions that separate senior engineers from junior ones."""

    def get_dynamic_user_prompt(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        depth_level = self._determine_depth_level(context_data, agent_config)
        focus_domain = self._identify_focus_domain(context_data, agent_config)
        technical_level = self._assess_technical_level(context_data)
        
        formatted_context = self.format_context_for_prompt(context_data)
        
        return f"""DEEP QUESTION GENERATION:

{formatted_context}

DEEP ANALYSIS CONFIGURATION:
- Depth Level: {depth_level}
- Focus Domain: {focus_domain}
- Technical Level: {technical_level}
- Difficulty: {agent_config.get('dynamic_parameters', {}).get('difficulty_level', 'medium')}

Generate deep, thought-provoking questions that explore advanced concepts and real-world implications."""
    
    def _determine_depth_level(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        difficulty = agent_config.get('dynamic_parameters', {}).get('difficulty_level', 'medium')
        problem_difficulty = context_data.get('problem', {}).get('difficulty', 'Medium')
        
        if difficulty == 'hard' or problem_difficulty == 'Hard':
            return "Architectural and Research level"
        elif difficulty == 'medium':
            return "Practical and Conceptual level"
        else:
            return "Conceptual level"
    
    def _identify_focus_domain(self, context_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        focus_area = agent_config.get('dynamic_parameters', {}).get('focus_area')
        if focus_area:
            return focus_area
        
        problem = context_data.get('problem', {})
        tags = problem.get('tags', [])
        
        if any(tag in ['graph', 'tree'] for tag in tags):
            return "System Design and Graph Theory"
        elif any(tag in ['dynamic-programming', 'recursion'] for tag in tags):
            return "Algorithmic Theory and Optimization"
        elif any(tag in ['array', 'string'] for tag in tags):
            return "Performance and Memory Architecture"
        else:
            return "General System Architecture"
    
    def _assess_technical_level(self, context_data: Dict[str, Any]) -> str:
        user_history = context_data.get('user_history', [])
        user_code = context_data.get('user_code', {})
        
        advanced_indicators = 0
        
        if len(user_history) > 20:
            advanced_indicators += 1
        
        if user_code:
            code = user_code.get('code', '')
            if any(term in code for term in ['class', 'import', 'try', 'except']):
                advanced_indicators += 1
            if len(code) > 300:
                advanced_indicators += 1
        
        if advanced_indicators >= 2:
            return "Senior/Principal Engineer"
        elif advanced_indicators >= 1:
            return "Mid-level Engineer"
        else:
            return "Junior Engineer"
    
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        return {
            "deep_questions": self._extract_questions(llm_response),
            "question_domains": self._categorize_domains(llm_response),
            "complexity_level": self._assess_complexity(llm_response),
            "real_world_connections": self._extract_connections(llm_response)
        }
    
    def _extract_questions(self, response: str) -> list:
        import re
        questions = []
        
        # Extract questions (similar to counter agent but looking for deeper patterns)
        patterns = [
            r'\d+\.\s*([^?]*\?)',  # Numbered questions
            r'[-*•]\s*([^?]*\?)',  # Bullet questions
            r'([A-Z][^.!?]*\?)'    # Standalone questions
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response)
            questions.extend(matches)
        
        # Filter for deep questions (longer, more complex)
        deep_questions = [q.strip() for q in questions if len(q.strip()) > 30]
        
        return deep_questions[:6]  # Limit to 6 deep questions
    
    def _categorize_domains(self, response: str) -> Dict[str, int]:
        domains = {
            'system_design': 0,
            'performance': 0,
            'architecture': 0,
            'scalability': 0,
            'theory': 0,
            'reliability': 0
        }
        
        response_lower = response.lower()
        
        domain_keywords = {
            'system_design': ['system', 'design', 'distributed', 'microservices'],
            'performance': ['performance', 'optimize', 'bottleneck', 'latency'],
            'architecture': ['architecture', 'pattern', 'structure', 'design'],
            'scalability': ['scale', 'scalability', 'load', 'concurrent'],
            'theory': ['complexity', 'algorithm', 'theoretical', 'mathematical'],
            'reliability': ['failure', 'reliability', 'fault', 'resilience']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                domains[domain] += 1
        
        return domains
    
    def _assess_complexity(self, response: str) -> str:
        advanced_terms = [
            'distributed systems', 'consensus', 'cap theorem', 'eventual consistency',
            'load balancing', 'sharding', 'replication', 'microservices',
            'containerization', 'orchestration', 'circuit breaker'
        ]
        
        advanced_count = sum(1 for term in advanced_terms if term in response.lower())
        
        if advanced_count >= 3:
            return "Very High"
        elif advanced_count >= 2:
            return "High"
        elif advanced_count >= 1:
            return "Medium"
        else:
            return "Low"
    
    def _extract_connections(self, response: str) -> list:
        connection_indicators = [
            'real world', 'production', 'industry', 'practice',
            'application', 'implementation', 'deployment'
        ]
        
        sentences = response.split('.')
        connections = []
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in connection_indicators):
                connections.append(sentence.strip())
        
        return connections[:3]
