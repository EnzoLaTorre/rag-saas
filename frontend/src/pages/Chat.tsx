import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import {
  listDocuments,
  streamChat,
  type ChatSource,
  type DocumentInfo,
} from '../api'
import { clearToken } from '../auth'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
}

export default function Chat() {
  const [docs, setDocs] = useState<DocumentInfo[]>([])
  const [documentId, setDocumentId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listDocuments()
      .then((d) => {
        setDocs(d)
        setDocumentId(d.find((x) => x.status === 'ready')?.id ?? null)
      })
      .catch(() => setError('No se pudieron cargar los documentos'))
  }, [])

  function handleLogout() {
    clearToken()
    window.location.href = '/login'
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const q = question.trim()
    if (!q || streaming) return

    setQuestion('')
    setError('')
    setStreaming(true)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: q },
      { role: 'assistant', content: '' },
    ])

    let full = ''

    streamChat(q, documentId, {
      onSources: () => {
        // la lista final llega en onDone
      },
      onToken: (token) => {
        full += token
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = { role: 'assistant', content: full }
          return next
        })
      },
      onDone: (answer, s) => {
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = {
            role: 'assistant',
            content: answer,
            sources: s,
          }
          return next
        })
        setStreaming(false)
      },
      onError: (err) => {
        setError(`Error: ${String(err)}`)
        setStreaming(false)
      },
    })
  }

  return (
    <div className="chat-page">
      <header className="topbar">
        <h1>Chat con tus documentos</h1>
        <div>
          <Link to="/dashboard">Documentos</Link>
          <button onClick={handleLogout} className="link">
            Salir
          </button>
        </div>
      </header>

      <div className="chat-sources-filter">
        <label>
          Preguntar sobre:
          <select
            value={documentId ?? ''}
            onChange={(e) =>
              setDocumentId(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">Todos mis documentos</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.status})
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="messages">
        {messages.length === 0 && (
          <p className="hint">Escribe una pregunta... y citaremos las fuentes.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.content}
            {m.sources && m.sources.length > 0 && (
              <div className="sources">
                <strong>Fuentes:</strong>
                {m.sources.map((s, j) => (
                  <details key={`${s.chunk_id}-${j}`}>
                    <summary>
                      Doc #{s.document_id} · chunk {s.chunk_index}
                    </summary>
                    <p>{s.text}</p>
                  </details>
                ))}
              </div>
            )}
          </div>
        ))}
        {streaming && <p className="meta">Escribiendo…</p>}
      </div>

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Escribe tu pregunta…"
          disabled={streaming}
        />
        <button type="submit" disabled={streaming}>
          Enviar
        </button>
      </form>
    </div>
  )
}