# Despliegue de la demo pública

Arquitectura de referencia:

```
Vercel (React)  ──HTTPS──►  Railway (FastAPI)  ──►  Postgres + pgvector (Neon o Railway)
     VITE_API_URL                CORS_ORIGINS              DATABASE_URL
```

Decisiones:

- **Backend en Railway** (Docker) con PostgreSQL + pgvector.
- **Frontend en Vercel** (estático, Vite).
- **Proveedor de IA en la nube** para la demo (Gemini por defecto, tier gratuito),
  ya que Ollama no cabe en el hosting gratuito.

---

## 1. Base de datos (Postgres + pgvector)

Elige una opción:

**A. Neon (recomendado, free tier con pgvector)**

1. Crea un proyecto en https://neon.tech
2. Copia la cadena de conexión (`postgresql://usuario:pass@host/db?sslmode=require`).
3. El backend la normaliza a `postgresql+psycopg://` automáticamente.
4. `pgvector` ya está disponible; el backend ejecuta `CREATE EXTENSION IF NOT EXISTS vector`.

**B. Railway Postgres**

Añade el plugin PostgreSQL en Railway. Verifica que `pgvector` esté disponible;
si no lo está, usa Neon.

---

## 2. Backend en Railway

1. New Project → **Deploy from GitHub repo** → `rag-saas`.
2. En el servicio, **Settings → Root Directory**: `backend` (así usa `backend/Dockerfile`).
3. Variables de entorno (Settings → Variables):

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | cadena de Neon/Railway |
| `JWT_SECRET` | un secreto aleatorio de 32+ caracteres |
| `CORS_ORIGINS` | `https://TU-APP.vercel.app` (se completa en el paso 4) |
| `AI_PROVIDER` | `cloud` |
| `CLOUD_API_KEY` | tu clave de Gemini (o Groq/OpenAI) |
| `CLOUD_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `CLOUD_CHAT_MODEL` | `gemini-3.8-flash` |
| `CLOUD_EMBED_MODEL` | `gemini-embedding-001` |
| `MAX_UPLOAD_MB` | `10` |

4. Deploy. El contenedor aplica migraciones (`alembic upgrade head`) y arranca uvicorn.
5. Comprueba `https://TU-BACKEND.up.railway.app/health` → `{"status":"ok"}`.

Opcional, cargar datos demo (Railway → servicio → Shell):

```bash
python -m app.seed
```

---

## 3. Frontend en Vercel

1. Import Project → mismo repo → **Root Directory**: `frontend`.
2. Framework: Vite (autodetectado). Build `npm run build`, output `dist`.
3. Variable de entorno:

| Variable | Valor |
|----------|-------|
| `VITE_API_URL` | `https://TU-BACKEND.up.railway.app/api` |

4. Deploy. Copia la URL final (`https://TU-APP.vercel.app`).
5. Vuelve a Railway y fija `CORS_ORIGINS=https://TU-APP.vercel.app`. Redeploy backend.

---

## 4. Verificación

- Abre la app de Vercel, regístrate y sube un documento.
- Comprueba que pasa a `Listo` y que el chat responde con fuentes.
- Revisa en el navegador que las peticiones a `/api` van al backend de Railway
  (Network tab) sin errores de CORS.

---

## Protección de la demo

- `CORS_ORIGINS` restringe quién puede llamar a la API.
- `MAX_UPLOAD_MB` limita el tamaño de archivo.
- `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` limitan chat y subidas por usuario.
- Usa una clave de IA con cuota baja y monitoriza el consumo.

> Para el free tier de Render/Railway, el servicio puede "dormir" y tardar en
> responder la primera petición. Es normal en demos.

---

## Cola de ingesta (opcional)

Por defecto la indexación corre con `BackgroundTasks` dentro del propio backend,
suficiente para una demo. Para separarla en un worker dedicado:

1. Añade un plugin **Redis** en Railway y copia su `REDIS_URL`.
2. Crea un segundo servicio desde el mismo repo (Root Directory `backend`) y
   define su **Start Command** como `rq worker --url $REDIS_URL ingest`.
3. Añade `REDIS_URL` también a las variables del servicio backend.

En local, `docker compose up` ya levanta los servicios `redis` y `worker`.
