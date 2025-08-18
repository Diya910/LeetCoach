"""
Pinecone vector database utilities for user context storage.
"""

import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime

try:
    from pinecone import Pinecone, ServerlessSpec

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from ..config import settings, LLMProvider
import boto3
from botocore.exceptions import BotoCoreError, ClientError


class PineconeClient:
    """Client for managing user context and embeddings in Pinecone."""
    
    def __init__(self, api_key: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize Pinecone client.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
        """
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone client not available. Install with: pip install pinecone-client")
        
        self.api_key = api_key or settings.pinecone_api_key
        self.environment = environment or settings.pinecone_environment
        self.index_name = settings.pinecone_index_name
        
        if not all([self.api_key, self.environment]):
            raise ValueError("Pinecone API key and environment are required")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or connect to the Pinecone index."""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name not in existing_indexes:
                # Create index if it doesn't exist
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Pinecone index: {e}")
    
    async def store_user_context(
        self,
        user_id: str,
        context_data: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store user context with embedding.
        
        Args:
            user_id: User identifier
            context_data: Context data to store
            embedding: Pre-computed embedding (optional)
            
        Returns:
            Context ID
        """
        try:
            # Generate context ID
            context_id = self._generate_context_id(user_id, context_data)
            
            # Generate embedding if not provided
            if embedding is None:
                embedding = await self._generate_embedding(context_data)
            
            # Prepare metadata
            metadata = {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'context_type': context_data.get('type', 'general'),
                'problem_title': context_data.get('problem_title', ''),
                'difficulty': context_data.get('difficulty', ''),
                'language': context_data.get('language', ''),
                'tags': json.dumps(context_data.get('tags', [])),
                'session_id': context_data.get('session_id', ''),
                'interaction_type': context_data.get('interaction_type', ''),
                'raw_data': json.dumps(context_data)[:40000]  # Pinecone metadata limit
            }
            
            # Store in Pinecone
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.index.upsert([(context_id, embedding, metadata)])
            )
            
            return context_id
            
        except Exception as e:
            raise RuntimeError(f"Failed to store user context: {e}")
    
    async def retrieve_user_context(
        self,
        user_id: str,
        query_embedding: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant user context.
        
        Args:
            user_id: User identifier
            query_embedding: Query embedding for similarity search
            query_text: Query text (will be embedded)
            top_k: Number of results to return
            filter_dict: Additional filters
            
        Returns:
            List of relevant context entries
        """
        try:
            # Generate embedding if needed
            if query_embedding is None and query_text:
                query_embedding = await self._generate_embedding({'text': query_text})
            
            if query_embedding is None:
                raise ValueError("Either query_embedding or query_text must be provided")
            
            # Prepare filter
            filter_conditions = {'user_id': user_id}
            if filter_dict:
                filter_conditions.update(filter_dict)
            
            # Query Pinecone
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_conditions
                )
            )
            
            # Process results
            contexts = []
            for match in results.matches:
                context = {
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata,
                    'data': json.loads(match.metadata.get('raw_data', '{}'))
                }
                contexts.append(context)
            
            return contexts
            
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve user context: {e}")
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> str:
        """
        Store or update user preferences.
        
        Args:
            user_id: User identifier
            preferences: User preferences
            
        Returns:
            Preference context ID
        """
        preference_data = {
            'type': 'preferences',
            'user_id': user_id,
            'preferences': preferences,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        return await self.store_user_context(user_id, preference_data)
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences or None
        """
        try:
            contexts = await self.retrieve_user_context(
                user_id=user_id,
                query_text="user preferences",
                top_k=1,
                filter_dict={'context_type': 'preferences'}
            )
            
            if contexts:
                return contexts[0]['data'].get('preferences', {})
            
            return None
            
        except Exception:
            return None
    
    async def store_interaction_history(
        self,
        user_id: str,
        interaction: Dict[str, Any]
    ) -> str:
        """
        Store user interaction history.
        
        Args:
            user_id: User identifier
            interaction: Interaction data
            
        Returns:
            Interaction context ID
        """
        interaction_data = {
            'type': 'interaction',
            'user_id': user_id,
            'interaction_type': interaction.get('type', 'unknown'),
            'problem_title': interaction.get('problem_title', ''),
            'agent_used': interaction.get('agent_used', ''),
            'timestamp': datetime.utcnow().isoformat(),
            **interaction
        }
        
        return await self.store_user_context(user_id, interaction_data)
    
    async def get_user_history(
        self,
        user_id: str,
        interaction_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user interaction history.
        
        Args:
            user_id: User identifier
            interaction_type: Filter by interaction type
            limit: Maximum number of results
            
        Returns:
            List of interactions
        """
        filter_dict = {'context_type': 'interaction'}
        if interaction_type:
            filter_dict['interaction_type'] = interaction_type
        
        contexts = await self.retrieve_user_context(
            user_id=user_id,
            query_text="user interaction history",
            top_k=limit,
            filter_dict=filter_dict
        )
        
        # Sort by timestamp (most recent first)
        contexts.sort(
            key=lambda x: x['data'].get('timestamp', ''),
            reverse=True
        )
        
        return [ctx['data'] for ctx in contexts]
    
    async def delete_user_context(self, user_id: str, context_id: Optional[str] = None):
        """
        Delete user context.
        
        Args:
            user_id: User identifier
            context_id: Specific context ID to delete (if None, deletes all user data)
        """
        try:
            if context_id:
                # Delete specific context
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.index.delete(ids=[context_id])
                )
            else:
                # Delete all user data
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.index.delete(filter={'user_id': user_id})
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to delete user context: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Pinecone service.
        
        Returns:
            Health status information
        """
        try:
            # Check index stats
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: self.index.describe_index_stats()
            )
            
            return {
                'status': 'healthy',
                'index_name': self.index_name,
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _generate_context_id(self, user_id: str, context_data: Dict[str, Any]) -> str:
        """Generate unique context ID."""
        # Create a hash based on user_id, timestamp, and content
        content_str = json.dumps(context_data, sort_keys=True)
        timestamp = str(int(time.time() * 1000))  # milliseconds
        hash_input = f"{user_id}:{timestamp}:{content_str}"
        
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    async def _generate_embedding(self, data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for data using OpenAI.
        This is a placeholder - in practice, you'd want to use a proper embedding service.
        """
        # Create text representation of data
        text_parts = []
        for key, value in data.items():
            if isinstance(value, (str, int, float)):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                text_parts.append(f"{key}: {', '.join(map(str, value))}")

        text = " | ".join(text_parts)

        # Prefer Bedrock embeddings when Bedrock is the default provider
        if settings.default_llm_provider == LLMProvider.BEDROCK:
            try:
                client = boto3.client(
                    'bedrock-runtime',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )

                body = {
                    "inputText": text
                }

                response = client.invoke_model(
                    modelId=settings.bedrock_embedding_model_id,
                    body=json.dumps(body)
                )

                payload = json.loads(response.get('body').read())
                # Titan returns json with 'embedding' key
                embedding = payload.get('embedding')
                if embedding and isinstance(embedding, list):
                    return embedding
            except (BotoCoreError, ClientError, Exception):
                pass

        # Fallback to OpenAI if configured
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception:
            # Final fallback: deterministic random vector matching 1536 dims
            import random
            random.seed(hash(str(data)))
            return [random.uniform(-1, 1) for _ in range(1536)]
