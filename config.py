"""Application configuration via environment variables with Pydantic validation."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"

    # OpenAI (embeddings)
    openai_api_key: str = ""

    # DeepSeek (RAG generation)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Langfuse (observability)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # SEC EDGAR
    sec_user_agent: str = "FinIntelMCP dev@example.com"

    # RAG settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # App
    app_name: str = "fin-intel-mcp"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
