from collections.abc import Iterator

from openai import OpenAI

from .base import AIProvider


class OpenAICompatibleProvider(AIProvider):
    """Proveedor basado en la API compatible con OpenAI.

    Sirve tanto para Ollama (`/v1`) como para servicios en la nube
    (Gemini, Groq, OpenRouter, OpenAI) cambiando `base_url` y modelos.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None,
        chat_model: str,
        embed_model: str,
        embedding_dim: int,
        send_dimensions: bool = False,
    ) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url or None)
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.embedding_dim = embedding_dim
        self.send_dimensions = send_dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        kwargs: dict = {"model": self.embed_model, "input": texts}
        if self.send_dimensions:
            kwargs["dimensions"] = self.embedding_dim
        res = self.client.embeddings.create(**kwargs)
        return [item.embedding for item in res.data]

    def chat_stream(self, messages: list[dict], model: str | None = None) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=model or self.chat_model,
            messages=messages,
            stream=True,
            temperature=0.2,
        )
        for part in stream:
            delta = part.choices[0].delta.content
            if delta:
                yield delta
