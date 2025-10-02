"""
AWS Bedrock client wrapper for LeetCoach application.
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from ..config import settings


class BedrockClient:
    """Async AWS Bedrock client wrapper with error handling and retry logic."""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """Initialize Bedrock client."""
        self.aws_access_key_id = aws_access_key_id or settings.aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key or settings.aws_secret_access_key
        self.region_name = region_name or settings.aws_region
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key]):
            raise ValueError("AWS credentials are required")
        
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
        
        self.model_id = settings.bedrock_model_id
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
    
    def _format_claude_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Format prompt for Claude model."""
        formatted_prompt = ""
        
        if system_prompt:
            formatted_prompt += f"System: {system_prompt}\n\n"
        
        formatted_prompt += f"Human: {prompt}\n\nAssistant:"
        return formatted_prompt
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion using AWS Bedrock.
        
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
            # Format prompt based on model type
            if "claude" in self.model_id.lower():
                formatted_prompt = self._format_claude_prompt(prompt, system_prompt)
                
                body = {
                    "prompt": formatted_prompt,
                    "max_tokens_to_sample": max_tokens or self.max_tokens,
                    "temperature": temperature or self.temperature,
                    "top_p": kwargs.get("top_p", 0.9),
                    "stop_sequences": kwargs.get("stop_sequences", ["\n\nHuman:"])
                }
            elif "llama" in self.model_id.lower():
                # Llama models use a specific format
                formatted_prompt = prompt
                if system_prompt:
                    formatted_prompt = f"{system_prompt}\n\n{prompt}"
                
                body = {
                    "prompt": formatted_prompt,
                    "max_gen_len": max_tokens or self.max_tokens,
                    "temperature": temperature or self.temperature,
                    "top_p": kwargs.get("top_p", 0.9)
                }
            else:
                # Generic format for other models (Titan, etc.)
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens or self.max_tokens,
                        "temperature": temperature or self.temperature,
                        "topP": kwargs.get("top_p", 0.9)
                    }
                }
            
            # Use asyncio to run the synchronous boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json"
                )
            )
            
            # Parse response based on model type
            response_body = json.loads(response['body'].read())
            
            if "claude" in self.model_id.lower():
                completion = response_body.get("completion", "")
                input_tokens = response_body.get("usage", {}).get("input_tokens", 0)
                output_tokens = response_body.get("usage", {}).get("output_tokens", 0)
            elif "llama" in self.model_id.lower():
                # Llama models response format
                completion = response_body.get("generation", "")
                input_tokens = response_body.get("prompt_token_count", 0)
                output_tokens = response_body.get("generation_token_count", 0)
            else:
                # Generic parsing for other models (Titan, etc.)
                completion = response_body.get("results", [{}])[0].get("outputText", "")
                input_tokens = response_body.get("inputTextTokenCount", 0)
                output_tokens = response_body.get("results", [{}])[0].get("tokenCount", 0)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "response": completion.strip(),
                "processing_time_ms": processing_time,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                "model": self.model_id,
                "finish_reason": "stop"
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            return {
                "success": False,
                "error": f"AWS Bedrock error: {error_code} - {error_message}",
                "error_type": "bedrock_error",
                "details": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
            
        except BotoCoreError as e:
            return {
                "success": False,
                "error": "AWS connection error",
                "error_type": "connection_error",
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
            if result.get("error_type") in ["bedrock_error"]:
                return result
            
            # Wait before retry with exponential backoff
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1
                await asyncio.sleep(wait_time)
        
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the AWS Bedrock service.
        
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
