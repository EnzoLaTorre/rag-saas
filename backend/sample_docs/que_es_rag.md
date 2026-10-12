# ¿Qué es RAG?

RAG (Retrieval-Augmented Generation) combina la búsqueda de información con un
modelo de lenguaje. En lugar de responder solo con lo que "recuerda", el sistema
recupera fragmentos relevantes de una base de conocimiento y los usa como
contexto para generar la respuesta.

## Fases del pipeline

1. **Ingesta**: los documentos (PDF, DOCX, TXT) se dividen en fragmentos (chunks).
2. **Embeddings**: cada fragmento se convierte en un vector numérico.
3. **Almacenamiento**: los vectores se guardan en una base vectorial (pgvector).
4. **Recuperación**: la pregunta se vectoriza y se buscan los fragmentos más cercanos.
5. **Generación**: el modelo responde usando únicamente esos fragmentos como contexto.

## Ventajas

- Reduce las alucinaciones al anclar la respuesta en fuentes verificables.
- Permite citar la procedencia de cada afirmación.
- Se puede actualizar el conocimiento sin reentrenar el modelo.
