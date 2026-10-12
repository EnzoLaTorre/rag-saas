from functools import lru_cache

from ...core.config import settings
from .base import AIProvider


@lru_cache
def get_provider() -> AIProvider:
    """Devuelve el proveedor de IA configurado en `AI_PROVIDER`."""
    name = settings.ai_provider.lower()
    if name == "ollama":
        from .ollama import OllamaProvider

        return OllamaProvider()
    if name == "cloud":
        from .cloud import CloudProvider

        return CloudProvider()
    raise ValueError(f"AI_PROVIDER desconocido: {settings.ai_provider!r} (usa 'ollama' o 'cloud')")


__all__ = ["AIProvider", "get_provider"]
