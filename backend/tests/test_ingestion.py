import pytest

from app.services.ingestion import CHUNK_SIZE, chunk_text, extract_text


def test_extract_txt():
    assert extract_text("nota.txt", b"hola mundo") == "hola mundo"


def test_extract_markdown():
    assert extract_text("doc.md", "acentué".encode()) == "acentué"


def test_extract_formato_no_soportado():
    with pytest.raises(ValueError):
        extract_text("archivo.bin", b"x")


def test_chunk_text_vacio():
    assert chunk_text("   ") == []


def test_chunk_text_con_solape():
    chunks = chunk_text("a" * 2500)
    assert len(chunks) == 3
    assert all(len(c) <= CHUNK_SIZE for c in chunks)


def test_chunk_text_normaliza_espacios():
    chunks = chunk_text("uno   dos\n\ntres")
    assert chunks == ["uno dos tres"]
