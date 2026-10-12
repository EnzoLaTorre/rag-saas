# Guion del video demo (60–90 s)

## Antes de grabar

- [ ] Backend y frontend desplegados (ver [DEPLOY.md](./DEPLOY.md)) o corriendo en local.
- [ ] Tenant demo con documentos ya ingeridos (`python -m app.seed`).
- [ ] Ventana a 1280×720 o superior, zoom del navegador al 100 %.
- [ ] Modo incógnito (sin sesión) para mostrar el registro desde cero.

## Guion

| Tiempo | Acción | Qué destacar |
|--------|--------|--------------|
| 0:00–0:08 | Pantalla del **README** en GitHub | Título, badges, stack |
| 0:08–0:18 | **Registro** (empresa + email) | "Cada registro crea una organización aislada" |
| 0:18–0:32 | Subir un **PDF** en *Mis documentos* | Cambia de `Procesando…` a `Listo` (indexado en segundo plano) |
| 0:32–0:52 | En *Chat*, preguntar algo del documento | Respuesta **en streaming** token a token |
| 0:52–1:02 | Desplegar **Fuentes** de la respuesta | "Cita los fragmentos exactos y su documento" |
| 1:02–1:15 | Cambiar el selector a **Todos mis documentos** y preguntar | Búsqueda sobre toda la organización |
| 1:15–1:25 | Mostrar `/docs` (Swagger) | API documentada automáticamente |
| 1:25–1:30 | Cierre con el README | "FastAPI + pgvector + React + Ollama/nube" |

## Consejos

- Graba a 30 fps con OBS o la grabadora del sistema.
- Acelera x2 las esperas (indexado, primera respuesta).
- Exporta a GIF para el README (`docs/demo.gif`, < 8 MB) y sube también el MP4.

## Insertar en el README

```markdown
![demo](docs/demo.gif)
```
