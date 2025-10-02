"""
Google Gemini client for LeetCoach application.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..config import settings


class GeminiClient:
    """Google Gemini client for generating completions."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key is required but not configured")
        
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def generate_completion_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate completion with retry logic.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            max_retries: Maximum number of retries
            retry_delay: Delay between retries
            
        Returns:
            Dictionary with success status and response
        """
        for attempt in range(max_retries + 1):
            try:
                # Combine system and user prompts
                full_prompt = self._format_prompt(system_prompt, prompt)
                
                # Generate content
                response = await self._generate_content(
                    full_prompt, max_tokens, temperature
                )
                
                return {
                    "success": True,
                    "response": response,
                    "usage": {
                        "prompt_tokens": len(full_prompt.split()),
                        "completion_tokens": len(response.split()),
                        "total_tokens": len(full_prompt.split()) + len(response.split())
                    },
                    "provider": "gemini",
                    "model": settings.gemini_model
                }
                
            except Exception as e:
                if attempt < max_retries:
                    print(f"Gemini API error (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    return {
                        "success": False,
                        "error": f"Gemini API error after {max_retries + 1} attempts: {str(e)}",
                        "provider": "gemini"
                    }
    
    def _format_prompt(self, system_prompt: Optional[str], user_prompt: str) -> str:
        """Format system and user prompts for Gemini."""
        if system_prompt:
            return f"System: {system_prompt}\n\nUser: {user_prompt}"
        return user_prompt
    
    async def _generate_content(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Generate content using Gemini API."""
        # Configure generation parameters
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.8,
            "top_k": 40
        }
        
        # Generate content
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=self.safety_settings
        )
        
        # Check for safety blocks
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            raise Exception(f"Content blocked: {response.prompt_feedback.block_reason}")
        
        if response.candidates and response.candidates[0].finish_reason == "SAFETY":
            raise Exception("Content blocked due to safety concerns")
        
        # Extract text from response
        if response.text:
            return response.text
        else:
            raise Exception("No content generated")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Gemini API."""
        try:
            # Simple test request
            test_response = await self.generate_completion_with_retry(
                prompt="Hello, this is a test.",
                max_tokens=10,
                temperature=0.1
            )
            
            return {
                "status": "healthy" if test_response["success"] else "unhealthy",
                "provider": "gemini",
                "model": settings.gemini_model,
                "error": test_response.get("error")
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "error": str(e)
            }
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts using Gemini."""
        try:
            # For now, return dummy embeddings since Gemini doesn't have a direct embedding API
            # In a real implementation, you might use a different service for embeddings
            return [[0.0] * 768 for _ in texts]  # Dummy 768-dimensional embeddings
            
        except Exception as e:
            raise Exception(f"Failed to get embeddings: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": "gemini",
            "model": settings.gemini_model,
            "max_tokens": 8192,  # Gemini 1.5 Pro context limit
            "supports_streaming": False,
            "supports_embeddings": False,
            "safety_settings": True
        }
