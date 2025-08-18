"""
OpenAI client wrapper for LeetCoach application.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import openai
from openai import AsyncOpenAI

from ..config import settings


class OpenAIClient:
    """Async OpenAI client wrapper with error handling and retry logic."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion using OpenAI's chat completion API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters for the API call
        
        Returns:
            Dict containing the response and metadata
        """
        start_time = time.time()
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                **kwargs
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "processing_time_ms": processing_time,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except openai.RateLimitError as e:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "error_type": "rate_limit",
                "details": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
            
        except openai.APIError as e:
            return {
                "success": False,
                "error": "OpenAI API error",
                "error_type": "api_error",
                "details": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected error",
                "error_type": "unknown",
                "details": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    async def generate_completion_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion with retry logic for transient failures.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
        
        Returns:
            Dict containing the response and metadata
        """
        for attempt in range(max_retries + 1):
            result = await self.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            
            if result["success"]:
                return result
            
            # Don't retry on certain error types
            if result.get("error_type") in ["rate_limit", "invalid_request"]:
                return result
            
            # Wait before retry with exponential backoff
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1
                await asyncio.sleep(wait_time)
        
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the OpenAI service.
        
        Returns:
            Dict containing health status
        """
        try:
            result = await self.generate_completion(
                prompt="Hello, this is a health check. Please respond with 'OK'.",
                max_tokens=10,
                temperature=0
            )
            
            return {
                "status": "healthy" if result["success"] else "unhealthy",
                "details": result
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
