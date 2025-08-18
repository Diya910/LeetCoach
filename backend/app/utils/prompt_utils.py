"""
Prompt templates and utilities for LeetCoach agents.
"""

from typing import Dict, Any, Optional, List
from ..models.request_models import ProgrammingLanguage, LeetCodeProblem, UserCode


class PromptTemplates:
    """Collection of prompt templates for different agents."""
    
    @staticmethod
    def get_optimize_prompt(
        problem: LeetCodeProblem,
        user_code: UserCode,
        target_language: Optional[ProgrammingLanguage] = None,
        focus_areas: List[str] = None
    ) -> Dict[str, str]:
        """Generate optimization prompt."""
        focus_areas = focus_areas or ["time_complexity", "space_complexity", "readability"]
        
        system_prompt = """You are an expert code optimization assistant. Your task is to analyze the given code and provide optimized solutions focusing on the specified areas. Always explain your optimizations clearly and provide the reasoning behind each improvement."""
        
        user_prompt = f"""
Problem: {problem.title}
Difficulty: {problem.difficulty}

Problem Description:
{problem.description}

Current Code ({user_code.language}):
```{user_code.language}
{user_code.code}
```

Focus Areas: {', '.join(focus_areas)}
{"Target Language: " + target_language if target_language else ""}

Please provide:
1. An optimized version of the code
2. Explanation of improvements made
3. Time and space complexity analysis (before and after)
4. Any trade-offs involved in the optimization

Format your response clearly with code blocks and explanations.
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    @staticmethod
    def get_complexity_prompt(
        problem: LeetCodeProblem,
        user_code: UserCode,
        analyze_space: bool = True,
        analyze_time: bool = True
    ) -> Dict[str, str]:
        """Generate complexity analysis prompt."""
        
        system_prompt = """You are an expert in algorithmic complexity analysis. Provide detailed and accurate time and space complexity analysis for the given code. Use Big O notation and explain your reasoning step by step."""
        
        analysis_types = []
        if analyze_time:
            analysis_types.append("time complexity")
        if analyze_space:
            analysis_types.append("space complexity")
        
        user_prompt = f"""
Problem: {problem.title}
Difficulty: {problem.difficulty}

Problem Description:
{problem.description}

Code to Analyze ({user_code.language}):
```{user_code.language}
{user_code.code}
```

Please analyze the {' and '.join(analysis_types)} of this solution and provide:

1. **Time Complexity**: Big O notation with detailed explanation
2. **Space Complexity**: Big O notation with detailed explanation
3. **Best, Average, and Worst Case scenarios** (if applicable)
4. **Step-by-step breakdown** of how you arrived at the complexity
5. **Comparison with alternative approaches** (if relevant)

Be specific about:
- Which operations contribute to the complexity
- How input size affects performance
- Any auxiliary space usage
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    @staticmethod
    def get_hint_prompt(
        problem: LeetCodeProblem,
        user_code: Optional[UserCode] = None,
        hint_level: int = 1,
        previous_hints: List[str] = None
    ) -> Dict[str, str]:
        """Generate hint prompt."""
        previous_hints = previous_hints or []
        
        system_prompt = f"""You are a helpful coding mentor providing hints for LeetCode problems. Provide hints at level {hint_level} out of 5, where:
- Level 1: Very subtle guidance, ask leading questions
- Level 2: Point toward the right approach without giving away the solution
- Level 3: Provide more specific direction and key insights
- Level 4: Give detailed algorithmic approach
- Level 5: Provide step-by-step solution outline

Tailor your hint to be helpful but not too revealing for the current level."""
        
        code_section = ""
        if user_code:
            code_section = f"""
Current Code Attempt ({user_code.language}):
```{user_code.language}
{user_code.code}
```
"""
        
        previous_hints_section = ""
        if previous_hints:
            previous_hints_section = f"""
Previous Hints Given:
{chr(10).join(f"- {hint}" for hint in previous_hints)}
"""
        
        user_prompt = f"""
Problem: {problem.title}
Difficulty: {problem.difficulty}

Problem Description:
{problem.description}

{code_section}
{previous_hints_section}

Hint Level Requested: {hint_level}/5

Please provide a hint that:
1. Is appropriate for level {hint_level}
2. Builds upon previous hints (if any)
3. Guides toward the solution without giving it away
4. Encourages learning and understanding
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    @staticmethod
    def get_counter_question_prompt(
        problem: LeetCodeProblem,
        user_code: Optional[UserCode] = None,
        question_type: str = "clarifying",
        num_questions: int = 3
    ) -> Dict[str, str]:
        """Generate counter question prompt."""
        
        system_prompt = """You are an experienced technical interviewer. Generate insightful counter-questions that an interviewer might ask to test deeper understanding of the problem and solution. Focus on edge cases, assumptions, and alternative approaches."""
        
        code_section = ""
        if user_code:
            code_section = f"""
Candidate's Solution ({user_code.language}):
```{user_code.language}
{user_code.code}
```
"""
        
        user_prompt = f"""
Problem: {problem.title}
Difficulty: {problem.difficulty}

Problem Description:
{problem.description}

{code_section}

Question Type: {question_type}
Number of Questions: {num_questions}

Generate {num_questions} {question_type} questions that an interviewer might ask, such as:
- Clarifying questions about requirements
- Edge case scenarios
- Alternative approaches
- Optimization possibilities
- Real-world application considerations

Make the questions challenging but fair, designed to assess deeper understanding.
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    @staticmethod
    def get_deep_question_prompt(
        problem: LeetCodeProblem,
        user_code: Optional[UserCode] = None,
        difficulty_level: str = "medium",
        focus_area: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate deep interview question prompt."""
        
        system_prompt = f"""You are a senior technical interviewer at a top tech company. Generate deep, thought-provoking questions at {difficulty_level} difficulty level that test advanced understanding of algorithms, data structures, and problem-solving approaches. These questions should challenge even experienced developers."""
        
        code_section = ""
        if user_code:
            code_section = f"""
Current Solution ({user_code.language}):
```{user_code.language}
{user_code.code}
```
"""
        
        focus_section = f"Focus Area: {focus_area}" if focus_area else ""
        
        user_prompt = f"""
Problem: {problem.title}
Difficulty: {problem.difficulty}

Problem Description:
{problem.description}

{code_section}
{focus_section}

Generate deep interview questions that might be asked as follow-ups, such as:
- How would you modify this solution for different constraints?
- What if the input size was extremely large?
- How would you implement this in a distributed system?
- What are the memory access patterns and cache implications?
- How would you test this solution comprehensively?
- What are the failure modes and how would you handle them?

Questions should be at {difficulty_level} difficulty level and test advanced concepts.
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    @staticmethod
    def get_solution_prompt(
        problem: LeetCodeProblem,
        include_multiple_approaches: bool = True,
        include_optimal_solution: bool = True,
        explain_trade_offs: bool = True
    ) -> Dict[str, str]:
        """Generate solution explanation prompt."""
        
        system_prompt = """You are an expert algorithm instructor. Provide comprehensive solution explanations that help students understand not just the 'how' but also the 'why' behind different approaches. Focus on building intuition and understanding."""
        
        user_prompt = f"""
Problem: {problem.title}
Difficulty: {problem.difficulty}

Problem Description:
{problem.description}

Constraints:
{chr(10).join(f"- {constraint}" for constraint in problem.constraints)}

Please provide a comprehensive solution explanation including:

{"1. **Multiple Approaches**: Present 2-3 different solution approaches with code examples" if include_multiple_approaches else ""}
{"2. **Optimal Solution**: Highlight the most efficient approach and explain why it's optimal" if include_optimal_solution else ""}
{"3. **Trade-offs Analysis**: Compare time/space complexity and discuss when to use each approach" if explain_trade_offs else ""}
4. **Step-by-step Explanation**: Break down the solution logic
5. **Code Implementation**: Provide clean, well-commented code
6. **Complexity Analysis**: Time and space complexity for each approach
7. **Edge Cases**: Important edge cases to consider

Make the explanation educational and help build problem-solving intuition.
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
