"""
Pydantic models for request and response schemas.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProgrammingLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    TYPESCRIPT = "typescript"


class AgentType(str, Enum):
    """Available agent types."""
    OPTIMIZE = "optimize"
    COMPLEXITY = "complexity"
    HINT = "hint"
    COUNTER = "counter"
    DEEPQ = "deepq"
    SOLUTION = "solution"


class DifficultyLevel(str, Enum):
    """LeetCode problem difficulty levels."""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class UserPreferences(BaseModel):
    """User preferences for personalized responses."""
    preferred_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON
    explanation_style: str = Field("detailed", description="brief, detailed, or comprehensive")
    include_examples: bool = True
    include_edge_cases: bool = True


class LeetCodeProblem(BaseModel):
    """LeetCode problem information."""
    title: str
    description: str
    difficulty: DifficultyLevel
    tags: List[str] = []
    constraints: List[str] = []
    examples: List[Dict[str, Any]] = []


class UserCode(BaseModel):
    """User's code submission."""
    code: str
    language: ProgrammingLanguage
    is_working: bool = False
    runtime_ms: Optional[int] = None
    memory_mb: Optional[float] = None


class UserRequest(BaseModel):
    """Base user request model."""
    user_id: str
    session_id: Optional[str] = None
    problem: LeetCodeProblem
    user_code: Optional[UserCode] = None
    preferences: Optional[UserPreferences] = None
    additional_context: Optional[str] = None


class OptimizeRequest(UserRequest):
    """Request for code optimization."""
    target_language: Optional[ProgrammingLanguage] = None
    focus_areas: List[str] = Field(default=["time_complexity", "space_complexity", "readability"])


class ComplexityRequest(UserRequest):
    """Request for complexity analysis."""
    analyze_space: bool = True
    analyze_time: bool = True
    include_explanation: bool = True


class HintRequest(UserRequest):
    """Request for hints."""
    hint_level: int = Field(1, ge=1, le=5, description="Hint level from 1 (subtle) to 5 (detailed)")
    previous_hints: List[str] = []


class CounterQuestionRequest(UserRequest):
    """Request for counter questions."""
    question_type: str = Field("clarifying", description="clarifying, edge_case, or optimization")
    num_questions: int = Field(3, ge=1, le=10)


class DeepQuestionRequest(UserRequest):
    """Request for deep interview questions."""
    difficulty_level: str = Field("medium", description="easy, medium, or hard")
    focus_area: Optional[str] = None


class SolutionRequest(UserRequest):
    """Request for solution explanation."""
    include_multiple_approaches: bool = True
    include_optimal_solution: bool = True
    explain_trade_offs: bool = True


class AgentResponse(BaseModel):
    """Base response model from agents."""
    agent_type: AgentType
    success: bool
    response: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class OptimizeResponse(AgentResponse):
    """Response from optimization agent."""
    optimized_code: Optional[str] = None
    improvements: List[str] = []
    complexity_improvement: Optional[Dict[str, str]] = None


class ComplexityResponse(AgentResponse):
    """Response from complexity analysis agent."""
    time_complexity: str
    space_complexity: str
    explanation: str
    best_case: Optional[str] = None
    worst_case: Optional[str] = None
    average_case: Optional[str] = None


class HintResponse(AgentResponse):
    """Response from hint agent."""
    hint: str
    hint_level: int
    next_hint_available: bool


class CounterQuestionResponse(AgentResponse):
    """Response from counter question agent."""
    questions: List[str]
    question_type: str


class DeepQuestionResponse(AgentResponse):
    """Response from deep question agent."""
    questions: List[str]
    difficulty_level: str
    focus_area: str


class SolutionResponse(AgentResponse):
    """Response from solution agent."""
    solutions: List[Dict[str, Any]]
    optimal_solution: Optional[Dict[str, Any]] = None
    trade_offs: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    llm_provider: str
    vector_db_status: str
