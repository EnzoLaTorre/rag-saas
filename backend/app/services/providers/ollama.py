from ...core.config import settings
from .openai_compatible import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    """Ollama local (gratis, offline) usando su API compatible con OpenAI."""

    def __init__(self) -> None:
        base = settings.ollama_base_url.rstrip("/")
        super().__init__(
            api_key="ollama",
            base_url=f"{base}/v1",
            chat_model=settings.ollama_chat_model,
            embed_model=settings.ollama_embed_model,
            embedding_dim=settings.ollama_embedding_dim,
        )
