"""
Base class for dynamic agents with context-aware prompting.
"""

import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from ..models.request_models import AgentType, AgentResponse
from ..providers import OpenAIClient, BedrockClient


class BaseDynamicAgent(ABC):
    """Base class for all dynamic agents with intelligent prompting."""
    
    def __init__(self, agent_type: AgentType):
        """Initialize the base dynamic agent."""
        self.agent_type = agent_type
    
    @abstractmethod
    def get_agent_system_prompt(self) -> str:
        """Get the detailed system prompt that defines the agent's behavior."""
        pass
    
    @abstractmethod
    def get_dynamic_user_prompt(
        self, 
        context_data: Dict[str, Any], 
        agent_config: Dict[str, Any]
    ) -> str:
        """Generate dynamic user prompt based on current context and configuration."""
        pass
    
    @abstractmethod
    def extract_response_data(self, llm_response: str) -> Dict[str, Any]:
        """Extract structured data from LLM response for this agent type."""
        pass
    
    def get_context_analysis_prompt(self, context_data: Dict[str, Any]) -> str:
        """Generate context analysis prompt for understanding current state."""
        return f"""Analyze the current coding session context for optimal assistance:

CURRENT CONTEXT:
{json.dumps(context_data, indent=2)}

ANALYZE:
1. Problem Understanding:
   - What is the user trying to solve?
   - What concepts are involved?
   - What's the difficulty level?

2. User's Current State:
   - Where are they in the problem-solving process?
   - What code have they written (if any)?
   - What might they be struggling with?

3. Optimal Assistance Strategy:
   - What type of help would be most beneficial?
   - How detailed should the response be?
   - What should be the focus area?

4. Learning Opportunity:
   - What can the user learn from this interaction?
   - How can we build their problem-solving skills?

Provide a structured analysis that will guide the response generation."""
    
    async def process_dynamic(
        self,
        context_data: Dict[str, Any],
        agent_config: Dict[str, Any],
        orchestration_decision: Dict[str, Any],
        llm_client: Union[OpenAIClient, BedrockClient]
    ) -> AgentResponse:
        """
        Process a request dynamically based on context and configuration.
        
        Args:
            context_data: Current context from LeetCode page and user state
            agent_config: Configuration from orchestrator
            orchestration_decision: Full orchestration decision
            llm_client: LLM client to use
            
        Returns:
            Agent response with structured data
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze context for this specific agent
            context_analysis = await self._analyze_context_for_agent(
                context_data, agent_config, llm_client
            )
            
            # Step 2: Generate dynamic prompts
            system_prompt = self.get_agent_system_prompt()
            user_prompt = self.get_dynamic_user_prompt(context_data, agent_config)
            
            # Step 3: Get LLM response
            llm_response = await llm_client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=agent_config.get('max_tokens', 2000),
                temperature=agent_config.get('temperature', 0.7),
                max_retries=2
            )
            
            if not llm_response["success"]:
                return AgentResponse(
                    agent_type=self.agent_type,
                    success=False,
                    response=f"LLM error: {llm_response.get('error', 'Unknown error')}",
                    confidence_score=0.0,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Step 4: Extract structured response data
            response_data = self.extract_response_data(llm_response["response"])
            
            # Step 5: Calculate confidence score
            confidence_score = self.calculate_confidence_score(
                llm_response["response"],
                context_data,
                agent_config,
                llm_response.get("usage", {})
            )
            
            # Step 6: Create agent response
            return AgentResponse(
                agent_type=self.agent_type,
                success=True,
                response=llm_response["response"],
                confidence_score=confidence_score,
                processing_time_ms=int((time.time() - start_time) * 1000),
                metadata={
                    "agent_config": agent_config,
                    "context_analysis": context_analysis,
                    "orchestration_decision": orchestration_decision,
                    "response_data": response_data,
                    "llm_usage": llm_response.get("usage", {}),
                    "dynamic_processing": True
                }
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                success=False,
                response=f"Dynamic processing error: {str(e)}",
                confidence_score=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                metadata={
                    "error_type": type(e).__name__,
                    "agent_config": agent_config,
                    "dynamic_processing": True
                }
            )
    
    async def _analyze_context_for_agent(
        self,
        context_data: Dict[str, Any],
        agent_config: Dict[str, Any],
        llm_client: Union[OpenAIClient, BedrockClient]
    ) -> Dict[str, Any]:
        """Analyze context specifically for this agent's needs."""
        try:
            context_prompt = self.get_context_analysis_prompt(context_data)
            
            llm_response = await llm_client.generate_completion_with_retry(
                prompt=context_prompt,
                system_prompt=f"You are a context analyzer for a {self.agent_type.value} agent.",
                max_tokens=600,
                temperature=0.3
            )
            
            if llm_response["success"]:
                try:
                    return json.loads(llm_response["response"])
                except json.JSONDecodeError:
                    return {
                        "analysis_text": llm_response["response"],
                        "structured": False
                    }
            else:
                return {"error": "Context analysis failed"}
                
        except Exception as e:
            return {"error": f"Context analysis error: {str(e)}"}
    
    def calculate_confidence_score(
        self,
        response: str,
        context_data: Dict[str, Any],
        agent_config: Dict[str, Any],
        usage_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence score based on response quality and context."""
        score = 0.0
        
        # Base score for successful response
        score += 0.3
        
        # Response length and detail bonus
        if len(response) > 200:
            score += 0.2
        elif len(response) > 100:
            score += 0.1
        
        # Context awareness bonus
        problem_title = context_data.get('problem', {}).get('title', '')
        if problem_title and problem_title.lower() in response.lower():
            score += 0.1
        
        # Code relevance bonus (if code exists)
        user_code = context_data.get('user_code', {})
        if user_code and user_code.get('code'):
            # Check if response addresses the specific code
            code_language = user_code.get('language', '')
            if code_language and code_language in response.lower():
                score += 0.1
        
        # Configuration adherence bonus
        specific_focus = agent_config.get('specific_focus', '')
        if specific_focus and any(word in response.lower() for word in specific_focus.lower().split()):
            score += 0.15
        
        # Technical depth bonus (agent-specific)
        technical_terms = self.get_technical_terms_for_scoring()
        terms_found = sum(1 for term in technical_terms if term.lower() in response.lower())
        score += min(terms_found * 0.05, 0.15)
        
        return min(score, 1.0)
    
    def get_technical_terms_for_scoring(self) -> list:
        """Get technical terms relevant to this agent for scoring."""
        # Base terms, can be overridden by specific agents
        return [
            'algorithm', 'complexity', 'optimization', 'data structure',
            'time', 'space', 'efficient', 'performance', 'solution'
        ]
    
    def format_context_for_prompt(self, context_data: Dict[str, Any]) -> str:
        """Format context data for inclusion in prompts."""
        formatted_parts = []
        
        # Problem information
        problem = context_data.get('problem', {})
        if problem:
            formatted_parts.append(f"""
PROBLEM DETAILS:
- Title: {problem.get('title', 'Unknown')}
- Difficulty: {problem.get('difficulty', 'Unknown')}
- Description: {problem.get('description', 'No description available')[:500]}...
- Tags: {', '.join(problem.get('tags', []))}
""")
        
        # User code information
        user_code = context_data.get('user_code', {})
        if user_code and user_code.get('code'):
            formatted_parts.append(f"""
USER'S CURRENT CODE ({user_code.get('language', 'unknown')}):
```{user_code.get('language', '')}
{user_code.get('code')}
```
Code Status: {'Working' if user_code.get('is_working') else 'Not working/incomplete'}
""")
        else:
            formatted_parts.append("USER'S CURRENT CODE: No code written yet")
        
        # Page context
        page_context = context_data.get('page_context', {})
        if page_context:
            formatted_parts.append(f"""
PAGE CONTEXT:
- Time on problem: {page_context.get('time_spent', 'unknown')}
- Attempts made: {page_context.get('attempts', 'unknown')}
- Current focus area: {page_context.get('focus_area', 'unknown')}
""")
        
        # User history
        user_history = context_data.get('user_history', [])
        if user_history:
            recent_history = user_history[-3:]  # Last 3 interactions
            formatted_parts.append(f"""
RECENT USER HISTORY:
{json.dumps(recent_history, indent=2)}
""")
        
        return '\n'.join(formatted_parts)
    
    def extract_code_from_response(self, response: str) -> str:
        """Extract code blocks from LLM response."""
        import re
        
        # Look for code blocks
        code_pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            # Return the longest code block
            return max(matches, key=len).strip()
        
        return ""
    
    def extract_list_items(self, response: str, keywords: list = None) -> list:
        """Extract list items from response based on patterns."""
        import re
        
        items = []
        
        # Pattern for numbered lists
        numbered_pattern = r'(?:^|\n)\s*\d+\.\s*([^\n]+)'
        numbered_matches = re.findall(numbered_pattern, response, re.MULTILINE)
        items.extend(numbered_matches)
        
        # Pattern for bullet points
        bullet_pattern = r'(?:^|\n)\s*[-*•]\s*([^\n]+)'
        bullet_matches = re.findall(bullet_pattern, response, re.MULTILINE)
        items.extend(bullet_matches)
        
        # Filter by keywords if provided
        if keywords:
            filtered_items = []
            for item in items:
                if any(keyword.lower() in item.lower() for keyword in keywords):
                    filtered_items.append(item.strip())
            return filtered_items[:10]  # Limit results
        
        return [item.strip() for item in items[:10]]
