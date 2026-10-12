from ...core.config import settings
from .openai_compatible import OpenAICompatibleProvider


class CloudProvider(OpenAICompatibleProvider):
    """Proveedor en la nube con API compatible con OpenAI.

    Por defecto apunta a Google Gemini (tier gratuito, con chat y embeddings).
    Cambia `CLOUD_BASE_URL`/modelos por cualquier endpoint compatible.
    """

    def __init__(self) -> None:
        api_key = settings.cloud_api_key or settings.openai_api_key
        if not api_key:
            raise ValueError(
                "AI_PROVIDER='cloud' requiere CLOUD_API_KEY (o OPENAI_API_KEY) configurada."
            )
        super().__init__(
            api_key=api_key,
            base_url=settings.cloud_base_url,
            chat_model=settings.cloud_chat_model,
            embed_model=settings.cloud_embed_model,
            embedding_dim=settings.cloud_embedding_dim,
            send_dimensions=True,
        )
