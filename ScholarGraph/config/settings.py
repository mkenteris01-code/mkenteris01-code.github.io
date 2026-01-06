"""
Centralized configuration management for ScholarGraph.
Loads all settings from .env file using Pydantic.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.
    All sensitive credentials are stored in .env and never hardcoded.
    """

    # Neo4j Database Configuration
    neo4j_uri: str = Field(default="bolt://127.0.0.1:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="pkg.graphrag", alias="NEO4J_DATABASE")

    # GPU Rig Configuration
    gpu_rig_qwen_url: str = Field(
        default="http://192.168.1.150:8000",
        alias="GPU_RIG_QWEN_URL"
    )
    gpu_rig_mistral_url: str = Field(
        default="http://192.168.1.150:8001",
        alias="GPU_RIG_MISTRAL_URL"
    )
    gpu_rig_embedding_url: str = Field(
        default="http://192.168.1.150:8005",
        alias="GPU_RIG_EMBEDDING_URL"
    )

    # Embedding Configuration
    embedding_model: str = Field(default="qwen", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, alias="EMBEDDING_DIMENSION")

    # Document Processing Configuration
    chunk_size_words: int = Field(default=3500, alias="CHUNK_SIZE_WORDS")
    chunk_overlap_words: int = Field(default=400, alias="CHUNK_OVERLAP_WORDS")

    # Optional: Gemini API Key
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    Creates it on first call, then returns cached instance.

    Returns:
        Settings: The application settings
    """
    global _settings
    if _settings is None:
        # Load settings from .env file in project root
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".env"

        if not env_path.exists():
            raise FileNotFoundError(
                f"Missing .env file at {env_path}. "
                f"Copy .env.example to .env and configure your credentials."
            )

        _settings = Settings(_env_file=str(env_path))

    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings from .env file.
    Useful for testing or when .env file changes.

    Returns:
        Settings: The reloaded settings
    """
    global _settings
    _settings = None
    return get_settings()


if __name__ == "__main__":
    # Test configuration loading
    settings = get_settings()
    print("Configuration loaded successfully!")
    print(f"Neo4j URI: {settings.neo4j_uri}")
    print(f"Neo4j Database: {settings.neo4j_database}")
    print(f"GPU Rig Qwen URL: {settings.gpu_rig_qwen_url}")
    print(f"Embedding Model: {settings.embedding_model}")
    print(f"Chunk Size: {settings.chunk_size_words} words")
