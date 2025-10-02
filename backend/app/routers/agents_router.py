"""
API routes for agent interactions.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from fastapi.responses import JSONResponse

from ..config import settings, LLMProvider
from ..orchestrator import DynamicAgentOrchestrator
from ..vectordb import PineconeClient
from ..models.request_models import (
    OptimizeRequest, ComplexityRequest, HintRequest,
    CounterQuestionRequest, DeepQuestionRequest, SolutionRequest,
    AgentType, HealthCheckResponse
)

router = APIRouter(prefix="/api", tags=["agents"])

# Global dynamic orchestrator instance (auto-select best available provider)
orchestrator = DynamicAgentOrchestrator()

# Global Pinecone client (optional, only if configured)
pinecone_client = None
try:
    if settings.validate_vector_db_config():
        pinecone_client = PineconeClient()
except Exception as e:
    print(f"Warning: Pinecone not available: {e}")


async def store_interaction_background(
    user_id: str,
    interaction_data: Dict[str, Any]
):
    """Store interaction in background task."""
    if pinecone_client:
        try:
            await pinecone_client.store_interaction_history(user_id, interaction_data)
        except Exception as e:
            print(f"Failed to store interaction: {e}")


@router.post("/ask")
async def dynamic_ask(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Dynamic endpoint that handles natural language requests and routes intelligently.
    
    Args:
        request: Dynamic request with user_request and context_data
        provider: Optional LLM provider override
        
    Returns:
        Dynamic agent response
    """
    try:
        # Validate request structure
        if "user_request" not in request or "context_data" not in request:
            raise HTTPException(
                status_code=400,
                detail="Request must contain 'user_request' and 'context_data' fields"
            )
        
        user_request = request["user_request"]
        context_data = request["context_data"]
        
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request dynamically
        response = await orchestrator.process_dynamic_request(
            user_request=user_request,
            context_data=context_data,
            provider=llm_provider
        )
        
        # Store interaction in background
        if pinecone_client:
            user_id = context_data.get("user_id", "anonymous")
            interaction_data = {
                'type': 'dynamic_ask',
                'user_request': user_request,
                'agent_used': response.metadata.get('orchestration_decision', {}).get('selected_agent', 'unknown'),
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_code(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Optimize code using the optimization agent.
    
    Args:
        request: Optimization request
        provider: Optional LLM provider override
        
    Returns:
        Optimization response
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request
        response = await orchestrator.optimize_code(request, llm_provider)
        
        # Store interaction in background
        if pinecone_client:
            interaction_data = {
                'type': 'optimize',
                'agent_used': AgentType.OPTIMIZE.value,
                'problem_title': request.problem.title,
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                request.user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complexity")
async def analyze_complexity(
    request: ComplexityRequest,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Analyze code complexity using the complexity agent.
    
    Args:
        request: Complexity analysis request
        provider: Optional LLM provider override
        
    Returns:
        Complexity analysis response
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request
        response = await orchestrator.analyze_complexity(request, llm_provider)
        
        # Store interaction in background
        if pinecone_client:
            interaction_data = {
                'type': 'complexity',
                'agent_used': AgentType.COMPLEXITY.value,
                'problem_title': request.problem.title,
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                request.user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hint")
async def get_hint(
    request: HintRequest,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Get hint using the hint agent.
    
    Args:
        request: Hint request
        provider: Optional LLM provider override
        
    Returns:
        Hint response
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request
        response = await orchestrator.get_hint(request, llm_provider)
        
        # Store interaction in background
        if pinecone_client:
            interaction_data = {
                'type': 'hint',
                'agent_used': AgentType.HINT.value,
                'problem_title': request.problem.title,
                'hint_level': request.hint_level,
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                request.user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/counter-questions")
async def get_counter_questions(
    request: CounterQuestionRequest,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Get counter questions using the counter question agent.
    
    Args:
        request: Counter question request
        provider: Optional LLM provider override
        
    Returns:
        Counter questions response
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request
        response = await orchestrator.get_counter_questions(request, llm_provider)
        
        # Store interaction in background
        if pinecone_client:
            interaction_data = {
                'type': 'counter_questions',
                'agent_used': AgentType.COUNTER.value,
                'problem_title': request.problem.title,
                'question_type': request.question_type,
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                request.user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deep-questions")
async def get_deep_questions(
    request: DeepQuestionRequest,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Get deep questions using the deep question agent.
    
    Args:
        request: Deep question request
        provider: Optional LLM provider override
        
    Returns:
        Deep questions response
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request
        response = await orchestrator.get_deep_questions(request, llm_provider)
        
        # Store interaction in background
        if pinecone_client:
            interaction_data = {
                'type': 'deep_questions',
                'agent_used': AgentType.DEEPQ.value,
                'problem_title': request.problem.title,
                'difficulty_level': request.difficulty_level,
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                request.user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/solution")
async def get_solution(
    request: SolutionRequest,
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Get solution explanation using the solution agent.
    
    Args:
        request: Solution request
        provider: Optional LLM provider override
        
    Returns:
        Solution response
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Process request
        response = await orchestrator.get_solution(request, llm_provider)
        
        # Store interaction in background
        if pinecone_client:
            interaction_data = {
                'type': 'solution',
                'agent_used': AgentType.SOLUTION.value,
                'problem_title': request.problem.title,
                'success': response.success,
                'confidence_score': response.confidence_score
            }
            background_tasks.add_task(
                store_interaction_background,
                request.user_id,
                interaction_data
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_process(
    requests: Dict[str, Dict[str, Any]],
    background_tasks: BackgroundTasks,
    provider: Optional[str] = None
):
    """
    Process multiple requests in batch.
    
    Args:
        requests: Dictionary mapping agent types to request data
        provider: Optional LLM provider override
        
    Returns:
        Dictionary mapping agent types to responses
    """
    try:
        # Validate provider
        llm_provider = None
        if provider:
            try:
                llm_provider = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider}. Must be one of: {[p.value for p in LLMProvider]}"
                )
        
        # Convert request data to proper request objects
        processed_requests = {}
        request_models = {
            'optimize': OptimizeRequest,
            'complexity': ComplexityRequest,
            'hint': HintRequest,
            'counter': CounterQuestionRequest,
            'deepq': DeepQuestionRequest,
            'solution': SolutionRequest
        }
        
        for agent_type_str, request_data in requests.items():
            if agent_type_str in request_models:
                agent_type = AgentType(agent_type_str)
                request_model = request_models[agent_type_str]
                processed_requests[agent_type] = request_model(**request_data)
        
        # Process batch
        responses = await orchestrator.batch_process(processed_requests, llm_provider)
        
        # Convert responses to serializable format
        serializable_responses = {}
        for agent_type, response in responses.items():
            serializable_responses[agent_type.value] = response.dict()
        
        return serializable_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user preferences from vector store."""
    if not pinecone_client:
        raise HTTPException(status_code=503, detail="Vector database not available")
    
    try:
        preferences = await pinecone_client.get_user_preferences(user_id)
        return preferences or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: Dict[str, Any]):
    """Update user preferences in vector store."""
    if not pinecone_client:
        raise HTTPException(status_code=503, detail="Vector database not available")
    
    try:
        context_id = await pinecone_client.update_user_preferences(user_id, preferences)
        return {"context_id": context_id, "status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/history")
async def get_user_history(
    user_id: str,
    interaction_type: Optional[str] = None,
    limit: int = 10
):
    """Get user interaction history from vector store."""
    if not pinecone_client:
        raise HTTPException(status_code=503, detail="Vector database not available")
    
    try:
        history = await pinecone_client.get_user_history(
            user_id, interaction_type, limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/history")
async def get_user_history_post(
    user_id: str,
    payload: Optional[Dict[str, Any]] = Body(default=None)
):
    """Post-compatible endpoint to retrieve user interaction history.

    Accepts optional JSON body with `interaction_type` and `limit`.
    """
    if not pinecone_client:
        raise HTTPException(status_code=503, detail="Vector database not available")

    try:
        interaction_type = (payload or {}).get("interaction_type")
        limit = int((payload or {}).get("limit", 10))
        history = await pinecone_client.get_user_history(
            user_id, interaction_type, limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Comprehensive health check (always 200, status in body)."""
    try:
        # Check orchestrator
        orchestrator_health = await orchestrator.health_check()
        
        # Check vector database
        vector_db_health = {"status": "not_configured"}
        if pinecone_client:
            try:
                vector_db_health = await pinecone_client.health_check()
            except Exception as ve:
                vector_db_health = {"status": "unhealthy", "error": str(ve)}
        
        # Overall status
        overall_status = "healthy"
        if (orchestrator_health.get("llm_client") != "healthy" or 
            vector_db_health.get("status") in ("unhealthy", "error")):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": str(orchestrator_health.get("timestamp", "")),
            "version": "1.0.0",
            "llm_provider": orchestrator_health.get("llm_provider", "unknown"),
            "vector_db_status": vector_db_health.get("status", "unknown"),
            "vector_db_error": vector_db_health.get("error")
        }
        
    except Exception as e:
        # Still return 200 with unhealthy status to keep the extension working
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "",
            "version": "1.0.0",
            "llm_provider": "unknown",
            "vector_db_status": "unknown"
        }


@router.get("/providers")
async def get_provider_info():
    """Get information about available LLM providers."""
    try:
        return orchestrator.get_provider_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/{provider_name}")
async def switch_provider(provider_name: str):
    """Switch the default LLM provider."""
    try:
        provider = LLMProvider(provider_name.lower())
        orchestrator.switch_provider(provider)
        return {"status": "switched", "provider": provider.value}
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {provider_name}. Must be one of: {[p.value for p in LLMProvider]}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
