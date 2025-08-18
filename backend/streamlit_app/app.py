"""
Streamlit app for LeetCoach administration and debugging.
"""

import streamlit as st
import asyncio
import json
from typing import Dict, Any
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.orchestrator import AgentOrchestrator
from app.models.request_models import *

# Page configuration
st.set_page_config(
    page_title="LeetCoach Admin",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'last_response' not in st.session_state:
    st.session_state.last_response = None

def initialize_orchestrator():
    """Initialize the orchestrator."""
    try:
        st.session_state.orchestrator = AgentOrchestrator()
        return True
    except Exception as e:
        st.error(f"Failed to initialize orchestrator: {e}")
        return False

def main():
    """Main Streamlit app."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 LeetCoach Administration</h1>
        <p>Debug, test, and monitor your AI coding assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # System Status
        st.subheader("System Status")
        
        if st.button("Initialize System"):
            with st.spinner("Initializing..."):
                if initialize_orchestrator():
                    st.success("System initialized successfully!")
                else:
                    st.error("Failed to initialize system")
        
        if st.session_state.orchestrator:
            st.success("✅ System Ready")
            
            # Health Check
            if st.button("Health Check"):
                with st.spinner("Checking health..."):
                    try:
                        health = asyncio.run(st.session_state.orchestrator.health_check())
                        st.json(health)
                    except Exception as e:
                        st.error(f"Health check failed: {e}")
        else:
            st.warning("⚠️ System Not Initialized")
        
        st.divider()
        
        # Settings
        st.subheader("Settings")
        st.text(f"LLM Provider: {settings.default_llm_provider.value}")
        st.text(f"Log Level: {settings.log_level.value}")
        st.text(f"API Port: {settings.api_port}")
        
        # Provider Switch
        if st.session_state.orchestrator:
            new_provider = st.selectbox(
                "Switch Provider",
                ["openai", "bedrock"],
                index=0 if settings.default_llm_provider.value == "openai" else 1
            )
            
            if st.button("Switch"):
                try:
                    st.session_state.orchestrator.switch_provider(LLMProvider(new_provider))
                    st.success(f"Switched to {new_provider}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to switch provider: {e}")
    
    # Main content area
    if not st.session_state.orchestrator:
        st.warning("Please initialize the system using the sidebar.")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🧪 Agent Testing", "📊 Analytics", "🔍 Debug", "📚 Documentation"])
    
    with tab1:
        agent_testing_tab()
    
    with tab2:
        analytics_tab()
    
    with tab3:
        debug_tab()
    
    with tab4:
        documentation_tab()

def agent_testing_tab():
    """Agent testing interface."""
    st.header("Agent Testing")
    st.write("Test individual agents with sample problems.")
    
    # Agent selection
    agent_type = st.selectbox(
        "Select Agent",
        ["optimize", "complexity", "hint", "counter", "deepq", "solution"]
    )
    
    # Sample problem
    st.subheader("Problem Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        problem_title = st.text_input("Problem Title", "Two Sum")
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        language = st.selectbox("Language", ["python", "javascript", "java", "cpp"])
    
    with col2:
        problem_description = st.text_area(
            "Problem Description",
            "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
            height=100
        )
    
    # User code
    if agent_type in ["optimize", "complexity"]:
        st.subheader("User Code")
        user_code = st.text_area(
            "Code",
            "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]",
            height=150
        )
    else:
        user_code = None
    
    # Agent-specific parameters
    st.subheader("Agent Parameters")
    
    params = {}
    if agent_type == "hint":
        params["hint_level"] = st.slider("Hint Level", 1, 5, 3)
    elif agent_type == "optimize":
        params["focus_areas"] = st.multiselect(
            "Focus Areas",
            ["time_complexity", "space_complexity", "readability"],
            default=["time_complexity", "space_complexity"]
        )
    elif agent_type == "counter":
        params["question_type"] = st.selectbox(
            "Question Type",
            ["clarifying", "edge_case", "optimization"]
        )
        params["num_questions"] = st.slider("Number of Questions", 1, 10, 5)
    elif agent_type == "deepq":
        params["difficulty_level"] = st.selectbox(
            "Difficulty Level",
            ["easy", "medium", "hard"]
        )
    elif agent_type == "solution":
        params["include_multiple_approaches"] = st.checkbox("Multiple Approaches", True)
        params["include_optimal_solution"] = st.checkbox("Optimal Solution", True)
        params["explain_trade_offs"] = st.checkbox("Trade-offs", True)
    
    # Test button
    if st.button("Test Agent", type="primary"):
        with st.spinner("Testing agent..."):
            try:
                # Create request
                problem = LeetCodeProblem(
                    title=problem_title,
                    description=problem_description,
                    difficulty=DifficultyLevel(difficulty),
                    tags=[],
                    constraints=[],
                    examples=[]
                )
                
                user_code_obj = None
                if user_code:
                    user_code_obj = UserCode(
                        code=user_code,
                        language=ProgrammingLanguage(language)
                    )
                
                # Create specific request based on agent type
                if agent_type == "optimize":
                    request = OptimizeRequest(
                        user_id="test_user",
                        problem=problem,
                        user_code=user_code_obj,
                        focus_areas=params.get("focus_areas", [])
                    )
                elif agent_type == "complexity":
                    request = ComplexityRequest(
                        user_id="test_user",
                        problem=problem,
                        user_code=user_code_obj
                    )
                elif agent_type == "hint":
                    request = HintRequest(
                        user_id="test_user",
                        problem=problem,
                        hint_level=params.get("hint_level", 3)
                    )
                elif agent_type == "counter":
                    request = CounterQuestionRequest(
                        user_id="test_user",
                        problem=problem,
                        question_type=params.get("question_type", "clarifying"),
                        num_questions=params.get("num_questions", 5)
                    )
                elif agent_type == "deepq":
                    request = DeepQuestionRequest(
                        user_id="test_user",
                        problem=problem,
                        difficulty_level=params.get("difficulty_level", "medium")
                    )
                elif agent_type == "solution":
                    request = SolutionRequest(
                        user_id="test_user",
                        problem=problem,
                        include_multiple_approaches=params.get("include_multiple_approaches", True),
                        include_optimal_solution=params.get("include_optimal_solution", True),
                        explain_trade_offs=params.get("explain_trade_offs", True)
                    )
                
                # Process request
                response = asyncio.run(
                    st.session_state.orchestrator.route_request(
                        AgentType(agent_type), request
                    )
                )
                
                st.session_state.last_response = response
                
                # Display response
                if response.success:
                    st.success(f"Agent responded successfully! (Confidence: {response.confidence_score:.2f})")
                    st.subheader("Response")
                    st.write(response.response)
                    
                    if hasattr(response, 'metadata') and response.metadata:
                        st.subheader("Metadata")
                        st.json(response.metadata)
                else:
                    st.error("Agent failed to respond")
                    st.write(response.response)
                
            except Exception as e:
                st.error(f"Error testing agent: {e}")

def analytics_tab():
    """Analytics and monitoring."""
    st.header("Analytics & Monitoring")
    st.write("Monitor system performance and usage statistics.")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Active Agents</h3>
            <h2>6</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>API Calls</h3>
            <h2>0</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Avg Response Time</h3>
            <h2>--ms</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>Success Rate</h3>
            <h2>--%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("📊 Analytics features will be implemented as the system collects usage data.")

def debug_tab():
    """Debug interface."""
    st.header("Debug Tools")
    st.write("Debug and troubleshoot system issues.")
    
    # Configuration display
    st.subheader("Current Configuration")
    config_dict = {
        "default_llm_provider": settings.default_llm_provider.value,
        "log_level": settings.log_level.value,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "openai_model": settings.openai_model,
        "bedrock_model_id": settings.bedrock_model_id,
        "pinecone_index_name": settings.pinecone_index_name,
    }
    st.json(config_dict)
    
    # Last response
    if st.session_state.last_response:
        st.subheader("Last Agent Response")
        st.json(st.session_state.last_response.dict())
    
    # Raw API test
    st.subheader("Raw API Test")
    if st.button("Test LLM Connection"):
        with st.spinner("Testing connection..."):
            try:
                if st.session_state.orchestrator:
                    # Test with a simple prompt
                    from app.models.request_models import HintRequest, LeetCodeProblem, DifficultyLevel
                    
                    test_problem = LeetCodeProblem(
                        title="Test",
                        description="Test problem",
                        difficulty=DifficultyLevel.EASY,
                        tags=[],
                        constraints=[],
                        examples=[]
                    )
                    
                    test_request = HintRequest(
                        user_id="test",
                        problem=test_problem,
                        hint_level=1
                    )
                    
                    response = asyncio.run(
                        st.session_state.orchestrator.get_hint(test_request)
                    )
                    
                    if response.success:
                        st.success("✅ LLM connection successful!")
                        st.write(f"Response: {response.response[:200]}...")
                    else:
                        st.error(f"❌ LLM connection failed: {response.response}")
                else:
                    st.error("Orchestrator not initialized")
            except Exception as e:
                st.error(f"Connection test failed: {e}")

def documentation_tab():
    """Documentation and help."""
    st.header("Documentation")
    
    st.markdown("""
    ## LeetCoach System Architecture
    
    LeetCoach is a modular AI-powered coding assistant with three main layers:
    
    ### 1. Frontend Layer (Chrome Extension)
    - **Content Script**: Injected into LeetCode pages to scrape problem data
    - **Background Script**: Handles API communication and extension lifecycle
    - **Popup UI**: User preferences and quick actions
    
    ### 2. Backend Layer (FastAPI)
    - **Orchestrator**: Routes requests to specialized agents
    - **Agents**: Six specialized agents for different tasks:
      - `OptimizeAgent`: Code optimization suggestions
      - `ComplexityAgent`: Time/space complexity analysis
      - `HintAgent`: Progressive hints for problem solving
      - `CounterAgent`: Interview-style counter questions
      - `DeepQAgent`: Advanced technical questions
      - `SolutionAgent`: Comprehensive solution explanations
    
    ### 3. Data Layer
    - **Vector Database (Pinecone)**: Stores user context and interaction history
    - **LLM Providers**: OpenAI GPT-4 and AWS Bedrock Claude
    
    ## API Endpoints
    
    - `POST /api/optimize` - Code optimization
    - `POST /api/complexity` - Complexity analysis
    - `POST /api/hint` - Get hints
    - `POST /api/counter-questions` - Counter questions
    - `POST /api/deep-questions` - Deep questions
    - `POST /api/solution` - Solution explanations
    - `POST /api/batch` - Batch processing
    - `GET /api/health` - Health check
    
    ## Getting Started
    
    1. **Backend Setup**:
       ```bash
       cd backend/app
       pip install -r requirements.txt
       cp .env.example .env  # Configure your API keys
       python main.py
       ```
    
    2. **Chrome Extension**:
       - Open Chrome Extensions (chrome://extensions/)
       - Enable Developer Mode
       - Load unpacked extension from `chrome_extension/` folder
    
    3. **Usage**:
       - Navigate to any LeetCode problem
       - The extension will automatically activate
       - Use the panel to get hints, optimize code, and more!
    
    ## Configuration
    
    Set up your `.env` file with the following variables:
    
    ```
    OPENAI_API_KEY=your_openai_key
    AWS_ACCESS_KEY_ID=your_aws_key
    AWS_SECRET_ACCESS_KEY=your_aws_secret
    PINECONE_API_KEY=your_pinecone_key
    PINECONE_ENVIRONMENT=your_pinecone_env
    ```
    """)

if __name__ == "__main__":
    main()
