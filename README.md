# RAG SaaS — Chat con tus documentos

Aplicación multi-tenant que indexa documentos (PDF, DOCX, TXT) y responde
preguntas con citas/fuentes usando RAG (Retrieval Augmented Generation).

## Arquitectura

- **backend/** — FastAPI + SQLModel (SQLite) + ChromaDB + OpenAI
- **frontend/** — React + Vite + TypeScript

Cada organización (tenant) tiene su propia colección de vectores en ChromaDB,
lo que aísla los datos entre clientes.

## Requisitos

- Python 3.12, Node 18+
- Clave de API de OpenAI con créditos

## Puesta en marcha

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows: source venv/Scripts/activate
pip install -r requirements.txt

copy .env.example .env         # y pon tu OPENAI_API_KEY real

uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

## Flujo de uso

1. Regístrate (crea tu organización y te convierte en admin).
2. Sube un documento en "Mis documentos".
3. Espera a que aparezca `Listo` (se indexa en segundo plano).
4. Pregunta en "Chat con tus documentos" y revisa los fragmentos citados.

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /api/auth/register | Alta de tenant + admin |
| POST | /api/auth/login | Login (form OAuth2) |
| GET  | /api/auth/me | Usuario actual |
| POST | /api/documents | Subir e indexar documento |
| GET  | /api/documents | Listar documentos del tenant |
| DELETE | /api/documents/{id} | Borrar documento |
| POST | /api/chat/query | Pregunta RAG (streaming SSE) |
| GET  | /api/chat/history | Historial del tenant |