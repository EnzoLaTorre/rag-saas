import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
  type DocumentInfo,
} from '../api'
import { clearToken } from '../auth'

const STATUS_LABEL: Record<string, string> = {
  processing: 'Procesando…',
  ready: 'Listo',
  failed: 'Falló',
}

export default function Dashboard() {
  const [docs, setDocs] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    try {
      setDocs(await listDocuments())
    } catch {
      setError('No se pudieron cargar los documentos')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    reload()
    const id = setInterval(reload, 3000)
    return () => clearInterval(id)
  }, [reload])

  async function handleUpload(file: File | null) {
    if (!file) return
    setUploading(true)
    setError('')
    try {
      await uploadDocument(file)
      await reload()
    } catch {
      setError('No se pudo subir el archivo')
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteDocument(id)
      await reload()
    } catch {
      setError('No se pudo borrar')
    }
  }

  function handleLogout() {
    clearToken()
    window.location.href = '/login'
  }

  return (
    <div className="page">
      <header className="topbar">
        <h1>Mis documentos</h1>
        <div>
          <Link to="/chat">Chat</Link>
          <button onClick={handleLogout} className="link">
            Salir
          </button>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      <label className="upload">
        {uploading ? 'Subiendo…' : 'Subir documento (PDF, DOCX, TXT)'}
        <input
          type="file"
          hidden
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => {
            handleUpload(e.target.files?.[0] ?? null)
            e.target.value = ''
          }}
        />
      </label>

      {loading ? (
        <p>Cargando…</p>
      ) : docs.length === 0 ? (
        <p className="hint">Aún no hay documentos. Sube el primero.</p>
      ) : (
        <ul className="doc-list">
          {docs.map((doc) => (
            <li key={doc.id} className="doc-item">
              <div>
                <strong>{doc.name}</strong>
                <span className="meta">
                  {STATUS_LABEL[doc.status] ?? doc.status} ·{' '}
                  {(doc.size / 1024).toFixed(0)} KB
                  {doc.chunk_count > 0 && ` · ${doc.chunk_count} chunks`}
                </span>
                {doc.status === 'failed' && doc.error && (
                  <span className="meta error">{doc.error}</span>
                )}
              </div>
              <button className="danger" onClick={() => handleDelete(doc.id)}>
                Borrar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}