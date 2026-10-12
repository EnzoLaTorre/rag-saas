import pytest

from app.core.config import settings
from app.services.providers import get_provider
from app.services.providers.cloud import CloudProvider
from app.services.providers.ollama import OllamaProvider
from app.services.providers.openai_compatible import OpenAICompatibleProvider


class _FakeEmbeddings:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs

        class _Item:
            embedding = [0.0]

        class _Res:
            data = [_Item()]

        return _Res()


class _FakeClient:
    def __init__(self):
        self.embeddings = _FakeEmbeddings()


def test_embeddings_envia_dimensions_si_se_configura():
    provider = OpenAICompatibleProvider(
        api_key="k",
        base_url=None,
        chat_model="c",
        embed_model="e",
        embedding_dim=768,
        send_dimensions=True,
    )
    provider.client = _FakeClient()
    provider.embed(["hola"])
    assert provider.client.embeddings.kwargs["dimensions"] == 768


def test_embeddings_no_envia_dimensions_por_defecto():
    provider = OpenAICompatibleProvider(
        api_key="k",
        base_url=None,
        chat_model="c",
        embed_model="e",
        embedding_dim=768,
    )
    provider.client = _FakeClient()
    provider.embed(["hola"])
    assert "dimensions" not in provider.client.embeddings.kwargs


def test_provider_ollama(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    get_provider.cache_clear()
    assert isinstance(get_provider(), OllamaProvider)
    get_provider.cache_clear()


def test_provider_cloud(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "cloud")
    monkeypatch.setattr(settings, "cloud_api_key", "test-key")
    get_provider.cache_clear()
    assert isinstance(get_provider(), CloudProvider)
    get_provider.cache_clear()


def test_provider_cloud_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "cloud")
    monkeypatch.setattr(settings, "cloud_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    get_provider.cache_clear()
    with pytest.raises(ValueError):
        get_provider()
    get_provider.cache_clear()


def test_provider_desconocido(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "wat")
    get_provider.cache_clear()
    with pytest.raises(ValueError):
        get_provider()
    get_provider.cache_clear()
