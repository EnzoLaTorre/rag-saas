from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag"
    jwt_secret: str
    access_token_expire_minutes: int = 30

    ai_provider: str = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_embedding_dim: int = 768

    cloud_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    cloud_api_key: str = ""
    cloud_chat_model: str = "gemini-2.5-flash"
    cloud_embed_model: str = "gemini-embedding-001"
    cloud_embedding_dim: int = 768

    openai_api_key: str = ""

    # Orígenes permitidos para CORS, separados por comas (vacío = ninguno).
    cors_origins: str = ""
    # Límites de protección de la demo.
    max_upload_mb: int = 10
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    # Cola de ingesta opcional. Si está vacío se usa BackgroundTasks en proceso.
    redis_url: str = ""
    documents_dir: Path = Path("data/documents")

    model_config = {"env_file": ".env"}

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, url: str) -> str:
        """Adapta `postgres://`/`postgresql://` (Railway, Heroku...) al driver psycopg."""
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def embedding_dim(self) -> int:
        """Dimensión de los embeddings según el proveedor activo.

        Debe coincidir con la dimensión de la columna `pgvector` y con el
        modelo elegido; si no, la inserción/consulta falla.
        """
        if self.ai_provider == "ollama":
            return self.ollama_embedding_dim
        if self.ai_provider == "cloud":
            return self.cloud_embedding_dim
        raise ValueError(f"AI_PROVIDER desconocido: {self.ai_provider!r}")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
