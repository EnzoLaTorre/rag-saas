<div align="center">

# RAG SaaS — Chatea con tus documentos

**Plataforma multi-tenant de RAG (Retrieval-Augmented Generation): sube tus documentos y haz preguntas en lenguaje natural, con respuestas que citan las fuentes.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

[![CI](https://github.com/EnzoLaTorre/rag-saas/actions/workflows/ci.yml/badge.svg)](https://github.com/EnzoLaTorre/rag-saas/actions/workflows/ci.yml)

<!-- DEMO: descomentar cuando esté desplegada (Fase 4)
**[▶ Demo en vivo](https://tu-demo.vercel.app)**
-->

</div>

---

## ¿Qué hace?

- **Multi-tenant real**: cada organización (tenant) tiene su propia colección de vectores. Los datos quedan aislados entre clientes.
- **Ingesta de documentos**: PDF, DOCX, TXT y Markdown, con chunking y embeddings.
- **Chat con streaming** (SSE): la respuesta aparece token a token.
- **Respuestas con fuentes**: cada respuesta incluye los fragmentos citados y su documento de origen.
- **Proveedor de IA intercambiable**: Ollama (local, gratis) o cualquier API compatible con OpenAI (Gemini, Groq, OpenRouter…). Ver [Elegir proveedor de IA](#elegir-proveedor-de-ia).

## Demo

> _GIF/video pendiente de grabar (guion en [`docs/DEMO.md`](./docs/DEMO.md))._
> Sube un PDF, espera a que quede `Listo` y pregunta: verás la respuesta en
> streaming con sus fuentes citadas.

<!-- ![demo](docs/demo.gif) -->

El despliegue de la demo pública (Railway + Vercel + Postgres/pgvector) está
documentado paso a paso en [`docs/DEPLOY.md`](./docs/DEPLOY.md).

## Arquitectura

```mermaid
flowchart LR
    U[Navegador] -->|React + Vite| F[Frontend]
    F -->|/api| B[FastAPI]
    B -->|JWT| A[AUTH]
    B --> DB[(PostgreSQL + pgvector)]
    B --> P{AIProvider}
    P --> O[Ollama local]
    P --> C[Nube: Gemini / Groq / OpenAI]

    subgraph Ingesta
        DOC[Upload PDF/DOCX/TXT] --> CH[Chunking] --> EMB[Embeddings] --> DB
    end
    subgraph Consulta
        Q[Pregunta] --> R[Retrieval top-k] --> LLM[Chat streaming] --> CIT[Cita fuentes]
    end
```

El aislamiento por tenant se aplica filtrando siempre por `tenant_id` en cada
consulta vectorial, de modo que una búsqueda nunca cruza datos entre organizaciones.

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | FastAPI · SQLModel · Pydantic Settings · Alembic |
| Base de datos | PostgreSQL + pgvector (búsqueda vectorial) |
| IA | Ollama · API compatible con OpenAI · embeddings `nomic-embed-text` |
| Frontend | React 19 · Vite · TypeScript · React Router |
| Infra | Docker · Docker Compose |
| Auth | JWT (HS256) · bcrypt |

## Puesta en marcha

### Opción A — Docker Compose (recomendado)

Levanta Postgres+pgvector, el backend y el frontend con un comando:

```bash
# En la raíz del repo. Define tu clave si usas el proveedor "cloud":
export CLOUD_API_KEY=tu-clave     # Windows PowerShell: $env:CLOUD_API_KEY="tu-clave"
docker compose up --build
```

- App: http://localhost:8080 · API: http://localhost:8000/docs

Carga documentos de ejemplo (tenant `demo@example.com` / `demo1234`):

```bash
docker compose exec backend python -m app.seed
```

> Por defecto Compose usa `AI_PROVIDER=cloud` (Gemini). Para usar el Ollama de tu
> host, pon `AI_PROVIDER=ollama` y el backend lo alcanzará vía `host.docker.internal`.

### Opción B — Local (manual)

**0. Requisitos**: Python **3.12**, Node **18+**, PostgreSQL con `pgvector` (o `docker compose up db`) y [Ollama](https://ollama.com/).

**1. Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

copy .env.example .env           # macOS/Linux: cp .env.example .env
docker compose -f ../docker-compose.yml up -d db   # Postgres+pgvector

alembic upgrade head             # crea el esquema

ollama pull nomic-embed-text     # embeddings (modo ollama)
ollama pull llama3.2             # chat
uvicorn app.main:app --reload

python -m app.seed               # (opcional) datos de demo
```

- API: http://127.0.0.1:8000 · Swagger: http://127.0.0.1:8000/docs

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173 (el proxy de Vite redirige `/api` al backend)

### Úsala

1. Regístrate (crea tu organización y quedas como `admin`).
2. Sube un documento en **Mis documentos**.
3. Espera a que aparezca `Listo` (se indexa en segundo plano).
4. Pregunta en **Chat** y revisa los fragmentos citados.

## Elegir proveedor de IA

El proveedor se selecciona con la variable `AI_PROVIDER`:

| `AI_PROVIDER` | Proveedor | Cuándo usarlo |
|---------------|-----------|---------------|
| `ollama` (por defecto) | Ollama local | Desarrollo, sin costo, sin claves |
| `cloud` | API compatible con OpenAI | Demo pública / producción |

Para el modo `cloud`, configura una clave y el endpoint (por defecto Google Gemini, con tier gratuito):

```env
AI_PROVIDER=cloud
CLOUD_API_KEY=tu-clave
CLOUD_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
CLOUD_CHAT_MODEL=gemini-3.8-flash
CLOUD_EMBED_MODEL=gemini-embedding-001
```

> ⚠️ **Reindexado al cambiar de proveedor**: la dimensión de los embeddings cambia
> entre modelos (p. ej. 768 en `nomic-embed-text` vs 1536 en `text-embedding-3-small`).
> Si cambias de proveedor, vuelve a subir/reindexar los documentos.

## Variables de entorno

Ver [`backend/.env.example`](./backend/.env.example). Las principales:

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `AI_PROVIDER` | `ollama` o `cloud` | `ollama` |
| `DATABASE_URL` | Conexión a PostgreSQL | `postgresql+psycopg://rag:rag@localhost:5432/rag` |
| `JWT_SECRET` | Secreto para firmar JWT (≥ 32 caracteres) | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Caducidad del token | `30` |
| `OLLAMA_BASE_URL` / `_CHAT_MODEL` / `_EMBED_MODEL` | Config de Ollama | `localhost:11434`, `llama3.2`, `nomic-embed-text` |
| `*_EMBEDDING_DIM` | Dimensión de embeddings (debe coincidir con la columna pgvector) | `768` |
| `CLOUD_*` | Config del proveedor en la nube | Gemini |

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/register` | Alta de tenant + admin |
| POST | `/api/auth/login` | Login (form OAuth2) |
| GET  | `/api/auth/me` | Usuario actual |
| POST | `/api/documents` | Subir e indexar documento |
| GET  | `/api/documents` | Listar documentos del tenant |
| DELETE | `/api/documents/{id}` | Borrar documento |
| POST | `/api/chat/query` | Pregunta RAG (streaming SSE) |
| GET  | `/api/chat/history` | Historial del tenant |

## Estructura

```
backend/
  alembic/           # migraciones (env.py + versions/)
  sample_docs/       # documentos de ejemplo para el seed
  app/
    api/             # routers: auth, documents, chat
    core/            # config, seguridad (JWT/bcrypt), dependencias
    services/        # ingestion, rag, vectorstore
      providers/     # AIProvider: ollama, cloud (OpenAI-compatible)
    models.py        # SQLModel: Tenant, User, Document, Chunk, ChatMessage
    seed.py          # crea tenant + usuario demo e ingiere sample_docs
  tests/             # pytest: providers, ingestion, rag, API
  Dockerfile
frontend/
  src/
    pages/           # Login, Register, Dashboard, Chat
    api.ts           # cliente HTTP + parser SSE (parseEvent, splitSSEBuffer)
    api.test.ts      # vitest del parser SSE
    auth.ts          # gestión de token
  Dockerfile · nginx.conf
docker-compose.yml
.github/workflows/ci.yml
```

## Base de datos y migraciones

El esquema se gestiona con **Alembic** sobre PostgreSQL + pgvector:

```bash
cd backend
alembic upgrade head                 # aplicar migraciones
alembic revision --autogenerate -m "cambio"   # nueva migración
alembic downgrade -1                 # revertir la última
```

Los embeddings se guardan en la tabla `chunk` (columna `vector(N)`) con un índice
**HNSW** (`vector_cosine_ops`) para búsqueda por similitud de coseno.

## Calidad

```bash
# Backend (lint + tests)
cd backend
pip install -r requirements-dev.txt
ruff check app alembic tests && ruff format --check app alembic tests

TEST_DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/rag pytest
# (los tests de integración se saltan si no hay Postgres disponible)

# Frontend (lint + tests + build)
cd frontend
npm run lint
npm test
npm run build
```

La integración continua (`.github/workflows/ci.yml`) corre lint, migraciones,
tests de backend contra Postgres+pgvector y tests/build del frontend en cada push y PR.

## Despliegue

Guía completa en [`docs/DEPLOY.md`](./docs/DEPLOY.md) (Railway + Vercel + Neon).

Resumen:

- **Backend**: Railway con `backend/Dockerfile` y `backend/railway.json`
  (`alembic upgrade head` + uvicorn). El `DATABASE_URL` de Railway/Neon se
  normaliza a `postgresql+psycopg://` automáticamente.
- **Frontend**: Vercel con `frontend/vercel.json`; apunta al backend vía `VITE_API_URL`.
- **CORS**: define `CORS_ORIGINS` con el dominio del frontend desplegado.
- **Protección**: `MAX_UPLOAD_MB`, `RATE_LIMIT_REQUESTS` y `RATE_LIMIT_WINDOW_SECONDS`
  limitan subidas y consultas por usuario.

## Decisiones técnicas

- **Aislamiento por `tenant_id`** en cada consulta + índice pgvector HNSW: una
  búsqueda nunca cruza datos entre organizaciones.
- **Proveedor de IA como interfaz** (`AIProvider`): permite desarrollo 100% local
  y gratis con Ollama, y desplegar en la nube sin tocar la lógica de negocio.
- **Postgres + pgvector en lugar de un vector store aparte**: una sola base de datos
  para datos relacionales y vectores; menos infraestructura y transacciones consistentes.
- **Streaming SSE** en lugar de WebSockets: unidireccional, simple y compatible con proxies.
- **Chunking por caracteres** con solape: rápido y suficiente para un MVP; se puede
  migrar a chunking por tokens cuando se incorpore conteo de tokens.
- **Ingesta desacoplada opcional**: por defecto `BackgroundTasks`; si se define
  `REDIS_URL`, la indexación se encola en un worker RQ (`rq worker ingest`), de modo
  que el procesamiento pesado no compite con el servidor web.

## Roadmap

- [x] **Fase 1** — Abstracción del proveedor de IA (Ollama + nube)
- [x] **Fase 2** — Postgres + pgvector, Docker Compose, migraciones (Alembic), seed de demo
- [x] **Fase 3** — Tests (pytest + vitest) y CI con badges
- [ ] **Fase 4** — Demo pública desplegada (Railway + Vercel) y video
      _(configs y guía listas; falta ejecutar el deploy)_
- [x] **Fase 5** — Historial en la UI, Markdown en las respuestas, auto-logout en 401
      y cola de ingesta opcional con RQ (`REDIS_URL`)

## Licencia

MIT — ver [LICENSE](./LICENSE).
