from abc import ABC, abstractmethod
from collections.abc import Iterator


class AIProvider(ABC):
    """Interfaz común para proveedores de embeddings y chat.

    Implementaciones concretas viven en este paquete (ollama, cloud, ...).
    """

    embedding_dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Devuelve un vector por cada texto de entrada."""

    @abstractmethod
    def chat_stream(self, messages: list[dict], model: str | None = None) -> Iterator[str]:
        """Genera la respuesta del modelo token a token."""
