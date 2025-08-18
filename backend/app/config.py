"""
Configuration management for LeetCoach application.
Handles environment variables and application settings.
"""

from typing import List, Optional, Union
from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path
import json

# Load .env from project-specific locations only (avoid picking up unrelated parent .env)
_this_file = Path(__file__).resolve()
_project_root = _this_file.parents[2]
_backend_dir = _this_file.parents[1]
_app_dir = _this_file.parent
for _env_path in (
    _project_root / ".env",
    _backend_dir / ".env",
    _app_dir / ".env",
):
    if _env_path.exists():
        load_dotenv(_env_path.as_posix(), override=False)
        break


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    BEDROCK = "bedrock"


class LogLevel(str, Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # pydantic-settings v2 configuration
    model_config = SettingsConfigDict(case_sensitive=False)

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # AWS Bedrock Configuration
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    bedrock_model_id: str = Field(
        "anthropic.claude-3-sonnet-20240229-v1:0", 
        env="BEDROCK_MODEL_ID"
    )
    bedrock_embedding_model_id: str = Field(
        "amazon.titan-embed-text-v1",
        env="BEDROCK_EMBEDDING_MODEL_ID"
    )
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field("leetcoach-user-context", env="PINECONE_INDEX_NAME")
    
    # Application Configuration
    default_llm_provider: LLMProvider = Field(LLMProvider.BEDROCK, env="DEFAULT_LLM_PROVIDER")
    log_level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    
    # CORS Configuration
    # Read env into a string to avoid pydantic-settings auto-JSON parsing
    cors_origins_env: Optional[str] = Field(None, env="CORS_ORIGINS")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./leetcoach.db", env="DATABASE_URL")
    
    # Agent Configuration
    max_tokens: int = Field(2000, env="MAX_TOKENS")
    temperature: float = Field(0.7, env="TEMPERATURE")
    
    def validate_llm_config(self) -> bool:
        """Validate that the required LLM configuration is present."""
        if self.default_llm_provider == LLMProvider.OPENAI:
            return self.openai_api_key is not None
        elif self.default_llm_provider == LLMProvider.BEDROCK:
            return all([
                self.aws_access_key_id,
                self.aws_secret_access_key
            ])
        return False
    
    def validate_vector_db_config(self) -> bool:
        """Validate that the required vector database configuration is present."""
        return all([
            self.pinecone_api_key,
            self.pinecone_environment
        ])

    @staticmethod
    def _parse_cors_origins(v: Union[str, List[str], None]) -> List[str]:
        """
        Accept multiple formats for CORS_ORIGINS env var:
        - JSON array string, e.g. '["http://localhost:3000", "https://example.com"]'
        - Comma-separated string, e.g. 'http://localhost:3000, https://example.com'
        - Already a list
        """
        if v is None or v == "":
            return [
                "chrome-extension://*",
                "http://localhost:3000",
                "https://leetcode.com",
            ]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            # Try JSON array first
            if s.startswith("[") and s.endswith("]"):
                try:
                    loaded = json.loads(s)
                    if isinstance(loaded, list):
                        return [str(item).strip() for item in loaded]
                except json.JSONDecodeError:
                    pass
            # Fallback: comma/semicolon separated
            parts = [p.strip().strip('"\'') for p in s.replace(";", ",").split(",") if p.strip()]
            return parts if parts else [
                "chrome-extension://*",
                "http://localhost:3000",
                "https://leetcode.com",
            ]
        # Any other type: return defaults
        return [
            "chrome-extension://*",
            "http://localhost:3000",
            "https://leetcode.com",
        ]

    @property
    def cors_origins(self) -> List[str]:
        return self._parse_cors_origins(self.cors_origins_env)


# Global settings instance
settings = Settings()
