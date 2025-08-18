"""
Dynamic Multi-Agent Orchestrator for LeetCoach application.
Uses detailed prompts to intelligently route and configure agents based on context.
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, Union, List
from enum import Enum

from .config import settings, LLMProvider
from .providers import OpenAIClient, BedrockClient
from .models.request_models import (
    AgentType, UserRequest, AgentResponse
)


class ContextAnalyzer:
    """Analyzes user context and determines optimal agent routing."""
    
    @staticmethod
    def get_orchestrator_prompt() -> str:
        """Get the master orchestrator prompt that controls everything."""
        return """You are the LeetCoach Orchestrator, an intelligent system that analyzes user requests and coding contexts to provide optimal assistance.

Your role is to:
1. Analyze the user's current situation, problem, and code state
2. Determine their intent and what type of help they need
3. Select the most appropriate specialized agent
4. Configure that agent with precise parameters
5. Provide dynamic, contextual responses

AVAILABLE AGENTS:
- HINT: Provides progressive hints based on where user is stuck
- OPTIMIZE: Improves existing code for better performance/readability  
- COMPLEXITY: Analyzes algorithmic complexity with detailed explanations
- SOLUTION: Provides comprehensive solution explanations and approaches
- COUNTER: Generates interview-style counter questions and edge cases
- DEEPQ: Creates advanced technical questions for deeper understanding

ANALYSIS FRAMEWORK:
1. USER INTENT: What does the user actually want?
   - Stuck and needs guidance → HINT
   - Has code but wants improvement → OPTIMIZE  
   - Wants to understand performance → COMPLEXITY
   - Needs complete solution explanation → SOLUTION
   - Preparing for interviews → COUNTER/DEEPQ

2. CURRENT CONTEXT: Where is the user in their problem-solving journey?
   - No code written → HINT or SOLUTION
   - Partial code → HINT or OPTIMIZE
   - Complete code → OPTIMIZE or COMPLEXITY
   - Understanding phase → SOLUTION or DEEPQ

3. PROBLEM DIFFICULTY: How complex is the problem?
   - Easy: Focus on understanding and basic optimization
   - Medium: Balance between hints and comprehensive analysis  
   - Hard: Provide detailed guidance and multiple approaches

4. USER HISTORY: What's their pattern? (if available)
   - Beginner: More detailed explanations, basic hints
   - Intermediate: Balanced approach with some challenge
   - Advanced: Focus on optimization, edge cases, deep questions

RESPONSE FORMAT:
{
    "selected_agent": "AGENT_NAME",
    "reasoning": "Why this agent was selected based on context analysis",
    "agent_config": {
        "specific_focus": "What should the agent focus on",
        "difficulty_level": "How complex should the response be",
        "context_awareness": "Key context points the agent should consider",
        "dynamic_parameters": {
            // Agent-specific parameters based on analysis
        }
    },
    "user_guidance": "Brief explanation to user about what will happen"
}

CONTEXT TO ANALYZE:
- User Request: {user_request}
- Problem Details: {problem_info}
- Current Code State: {code_state}
- User History: {user_history}
- Page Context: {page_context}

Analyze this context deeply and select the optimal agent with precise configuration."""

    @staticmethod
    def get_context_extraction_prompt() -> str:
        """Prompt for extracting and understanding current context."""
        return """You are a Context Extraction specialist. Analyze the current LeetCode session state and extract meaningful context.

EXTRACT THE FOLLOWING:
1. PROBLEM STATE:
   - Problem title and difficulty
   - User's understanding level (based on time spent, attempts)
   - Key problem concepts and patterns

2. CODE STATE:
   - Current code status (empty, partial, complete, buggy)
   - Code quality indicators
   - Potential issues or stuck points
   - Language and style patterns

3. USER BEHAVIOR:
   - How long they've been on this problem
   - Previous attempts or iterations
   - Interaction patterns with the page
   - Signs of confusion or progress

4. LEARNING CONTEXT:
   - What concepts might be challenging
   - Where they might need guidance
   - Optimal learning approach for this user

5. INTENT SIGNALS:
   - Explicit request analysis
   - Implicit needs based on behavior
   - Urgency or pressure indicators

CONTEXT DATA:
{context_data}

Provide a structured analysis that will help the orchestrator make intelligent decisions."""


class LLMProviderFactory:
    """Factory for creating LLM provider clients."""
    
    @staticmethod
    def create_client(provider: LLMProvider) -> Union[OpenAIClient, BedrockClient]:
        """Create an LLM client based on the provider type."""
        if provider == LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is required but not configured")
            return OpenAIClient()
        
        elif provider == LLMProvider.BEDROCK:
            if not all([settings.aws_access_key_id, settings.aws_secret_access_key]):
                raise ValueError("AWS credentials are required but not configured")
            return BedrockClient()
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


class DynamicAgentOrchestrator:
    """
    Dynamic orchestrator that uses detailed prompts to intelligently
    route requests and configure agents based on real-time context analysis.
    """
    
    def __init__(self, default_provider: Optional[LLMProvider] = None):
        """Initialize the dynamic orchestrator."""
        self.default_provider = default_provider or settings.default_llm_provider
        self.llm_client = None
        self.context_analyzer = ContextAnalyzer()
        self._initialize_llm_client()
        
        # Import agents dynamically to avoid circular imports
        from .agents import (
            DynamicHintAgent, DynamicOptimizeAgent, DynamicComplexityAgent,
            DynamicCounterAgent, DynamicDeepQAgent, DynamicSolutionAgent
        )
        
        # Initialize dynamic agents
        self.agents = {
            AgentType.HINT: DynamicHintAgent(),
            AgentType.OPTIMIZE: DynamicOptimizeAgent(),
            AgentType.COMPLEXITY: DynamicComplexityAgent(),
            AgentType.SOLUTION: DynamicSolutionAgent(),
            AgentType.COUNTER: DynamicCounterAgent(),
            AgentType.DEEPQ: DynamicDeepQAgent()
        }
    
    def _initialize_llm_client(self):
        """Initialize the LLM client with the default provider."""
        try:
            self.llm_client = LLMProviderFactory.create_client(self.default_provider)
        except ValueError as e:
            raise RuntimeError(f"Failed to initialize LLM client: {e}")
    
    async def process_dynamic_request(
        self,
        user_request: str,
        context_data: Dict[str, Any],
        provider: Optional[LLMProvider] = None
    ) -> AgentResponse:
        """
        Process a request dynamically by analyzing context and routing intelligently.
        
        Args:
            user_request: The user's natural language request
            context_data: Current context from the LeetCode page and user state
            provider: Optional LLM provider override
            
        Returns:
            Dynamic agent response
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract and analyze context
            context_analysis = await self._analyze_context(context_data)
            
            # Step 2: Use orchestrator to determine optimal agent and configuration
            orchestration_decision = await self._make_orchestration_decision(
                user_request, context_analysis, context_data
            )
            
            # Step 3: Route to selected agent with dynamic configuration
            response = await self._route_to_dynamic_agent(
                orchestration_decision, context_data, provider
            )
            
            # Step 4: Add orchestration metadata
            response.processing_time_ms = int((time.time() - start_time) * 1000)
            if not response.metadata:
                response.metadata = {}
            response.metadata.update({
                "orchestration_decision": orchestration_decision,
                "context_analysis": context_analysis,
                "dynamic_routing": True
            })
            
            return response
            
        except Exception as e:
            return AgentResponse(
                agent_type=AgentType.HINT,  # Default fallback
                success=False,
                response=f"Orchestration error: {str(e)}",
                confidence_score=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                metadata={"error_type": type(e).__name__, "dynamic_routing": True}
            )
    
    async def _analyze_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current context to understand user state."""
        try:
            context_prompt = self.context_analyzer.get_context_extraction_prompt().format(
                context_data=json.dumps(context_data, indent=2)
            )
            
            llm_response = await self.llm_client.generate_completion_with_retry(
                prompt=context_prompt,
                system_prompt="You are an expert context analyzer for coding assistance.",
                max_tokens=800,
                temperature=0.3
            )
            
            if llm_response["success"]:
                # Try to parse structured response, fallback to text analysis
                try:
                    return json.loads(llm_response["response"])
                except json.JSONDecodeError:
                    return {
                        "analysis_text": llm_response["response"],
                        "structured": False
                    }
            else:
                return {"error": "Context analysis failed", "raw_context": context_data}
                
        except Exception as e:
            return {"error": f"Context analysis error: {str(e)}", "raw_context": context_data}
    
    async def _make_orchestration_decision(
        self, 
        user_request: str, 
        context_analysis: Dict[str, Any],
        raw_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use the orchestrator prompt to make intelligent routing decisions."""
        try:
            # Prepare context information for the orchestrator
            problem_info = raw_context.get('problem', {})
            code_state = raw_context.get('user_code', {})
            user_history = raw_context.get('user_history', [])
            page_context = raw_context.get('page_context', {})
            
            orchestrator_prompt = self.context_analyzer.get_orchestrator_prompt().format(
                user_request=user_request,
                problem_info=json.dumps(problem_info, indent=2),
                code_state=json.dumps(code_state, indent=2) if code_state else "No code written yet",
                user_history=json.dumps(user_history[-5:], indent=2) if user_history else "No history available",
                page_context=json.dumps(page_context, indent=2)
            )
            
            llm_response = await self.llm_client.generate_completion_with_retry(
                prompt=orchestrator_prompt,
                system_prompt="You are the master orchestrator for an AI coding assistant. Make precise, intelligent routing decisions.",
                max_tokens=1000,
                temperature=0.2
            )
            
            if llm_response["success"]:
                try:
                    decision = json.loads(llm_response["response"])
                    
                    # Validate the decision structure
                    required_keys = ["selected_agent", "reasoning", "agent_config"]
                    if all(key in decision for key in required_keys):
                        return decision
                    else:
                        raise ValueError("Invalid decision structure")
                        
                except json.JSONDecodeError:
                    # Fallback: parse text response for agent selection
                    response_text = llm_response["response"].lower()
                    
                    # Simple agent detection based on keywords
                    if any(word in response_text for word in ["hint", "stuck", "guidance"]):
                        selected_agent = "HINT"
                    elif any(word in response_text for word in ["optimize", "improve", "better"]):
                        selected_agent = "OPTIMIZE"
                    elif any(word in response_text for word in ["complexity", "performance", "time", "space"]):
                        selected_agent = "COMPLEXITY"
                    elif any(word in response_text for word in ["solution", "explain", "how"]):
                        selected_agent = "SOLUTION"
                    elif any(word in response_text for word in ["question", "interview", "counter"]):
                        selected_agent = "COUNTER"
                    elif any(word in response_text for word in ["deep", "advanced", "technical"]):
                        selected_agent = "DEEPQ"
                    else:
                        selected_agent = "HINT"  # Default fallback
                    
                    return {
                        "selected_agent": selected_agent,
                        "reasoning": llm_response["response"],
                        "agent_config": {
                            "specific_focus": "General assistance",
                            "difficulty_level": "medium",
                            "context_awareness": "Basic context",
                            "dynamic_parameters": {}
                        },
                        "fallback_parsing": True
                    }
            
            # Ultimate fallback
            return self._get_fallback_decision(user_request, context_analysis)
            
        except Exception as e:
            return self._get_fallback_decision(user_request, context_analysis, str(e))
    
    def _get_fallback_decision(
        self, 
        user_request: str, 
        context_analysis: Dict[str, Any], 
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provide a fallback decision when orchestration fails."""
        # Simple keyword-based fallback
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ["hint", "help", "stuck", "guide"]):
            agent = "HINT"
        elif any(word in request_lower for word in ["optimize", "improve", "better", "faster"]):
            agent = "OPTIMIZE"
        elif any(word in request_lower for word in ["complexity", "time", "space", "performance"]):
            agent = "COMPLEXITY"
        elif any(word in request_lower for word in ["solution", "solve", "answer", "explain"]):
            agent = "SOLUTION"
        elif any(word in request_lower for word in ["question", "interview", "ask"]):
            agent = "COUNTER"
        else:
            agent = "HINT"  # Default
        
        return {
            "selected_agent": agent,
            "reasoning": f"Fallback selection based on keywords in request: '{user_request}'",
            "agent_config": {
                "specific_focus": "User request analysis",
                "difficulty_level": "medium",
                "context_awareness": "Limited context",
                "dynamic_parameters": {}
            },
            "fallback_used": True,
            "error": error
        }
    
    async def _route_to_dynamic_agent(
        self,
        orchestration_decision: Dict[str, Any],
        context_data: Dict[str, Any],
        provider: Optional[LLMProvider] = None
    ) -> AgentResponse:
        """Route the request to the selected agent with dynamic configuration."""
        try:
            selected_agent_name = orchestration_decision["selected_agent"]
            agent_config = orchestration_decision.get("agent_config", {})
            
            # Map agent names to types
            agent_type_map = {
                "HINT": AgentType.HINT,
                "OPTIMIZE": AgentType.OPTIMIZE,
                "COMPLEXITY": AgentType.COMPLEXITY,
                "SOLUTION": AgentType.SOLUTION,
                "COUNTER": AgentType.COUNTER,
                "DEEPQ": AgentType.DEEPQ
            }
            
            agent_type = agent_type_map.get(selected_agent_name, AgentType.HINT)
            
            if agent_type not in self.agents:
                raise ValueError(f"Agent {agent_type} not available")
            
            # Use specified provider or default
            llm_provider = provider or self.default_provider
            if provider and provider != self.default_provider:
                llm_client = LLMProviderFactory.create_client(provider)
            else:
                llm_client = self.llm_client
            
            # Get the agent and process with dynamic configuration
            agent = self.agents[agent_type]
            
            # Process the request with dynamic configuration
            response = await agent.process_dynamic(
                context_data=context_data,
                agent_config=agent_config,
                orchestration_decision=orchestration_decision,
                llm_client=llm_client
            )
            
            return response
            
        except Exception as e:
            return AgentResponse(
                agent_type=AgentType.HINT,
                success=False,
                response=f"Agent routing error: {str(e)}",
                confidence_score=0.0,
                metadata={"routing_error": str(e)}
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the orchestrator and its components."""
        health_status = {
            "orchestrator": "healthy",
            "llm_provider": self.default_provider.value,
            "agents": {},
            "timestamp": time.time(),
            "dynamic_routing": True
        }
        
        # Check LLM client health
        try:
            llm_health = await self.llm_client.health_check()
            health_status["llm_client"] = llm_health["status"]
        except Exception as e:
            health_status["llm_client"] = "unhealthy"
            health_status["llm_error"] = str(e)
        
        # Check agent availability
        for agent_type, agent in self.agents.items():
            try:
                health_status["agents"][agent_type.value] = "available"
            except Exception as e:
                health_status["agents"][agent_type.value] = f"error: {str(e)}"
        
        return health_status
    
    def switch_provider(self, provider: LLMProvider):
        """Switch the default LLM provider."""
        self.default_provider = provider
        self._initialize_llm_client()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider."""
        return {
            "current_provider": self.default_provider.value,
            "available_providers": [provider.value for provider in LLMProvider],
            "model": getattr(settings, f"{self.default_provider.value}_model", "unknown"),
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "dynamic_routing": True
        }