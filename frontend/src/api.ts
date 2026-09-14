import axios from 'axios'
import { getToken } from './auth'

const http = axios.create({ baseURL: '/api' })

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface UserInfo {
  id: number
  tenant_id: number
  email: string
  full_name: string
  role: string
}

export interface DocumentInfo {
  id: number
  tenant_id: number
  name: string
  filename: string
  size: number
  status: string
  chunk_count: number
  error: string | null
  created_at: string
}

export interface ChatSource {
  chunk_id: string
  text: string
  document_id: number
  chunk_index: number
}

export async function register(data: {
  tenant_name: string
  email: string
  full_name: string
  password: string
}) {
  const res = await http.post('/auth/register', data)
  return res.data
}

export async function login(username: string, password: string) {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const res = await http.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export async function me(): Promise<UserInfo> {
  const res = await http.get('/auth/me')
  return res.data
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await http.get('/documents')
  return res.data
}

export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await http.post('/documents', form)
  return res.data
}

export async function deleteDocument(id: number) {
  const res = await http.delete(`/documents/${id}`)
  return res.data
}

export function streamChat(
  question: string,
  documentId: number | null,
  handlers: {
    onSources: (sources: ChatSource[]) => void
    onToken: (token: string) => void
    onDone: (answer: string, sources: ChatSource[]) => void
    onError: (err: unknown) => void
  },
) {
  fetch('/api/chat/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ question, document_id: documentId }),
  })
    .then(async (res) => {
      if (!res.ok || !res.body) throw new Error(await res.text())
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let full = ''
      let finished = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split('\n\n')
        buffer = events.pop() ?? ''

        for (const ev of events) {
          const line = ev.trim()
          if (!line.startsWith('data:')) continue
          let data: Record<string, unknown>
          try {
            data = JSON.parse(line.slice(5).trim())
          } catch {
            continue
          }
          if (data.type === 'sources') {
            handlers.onSources(data.sources as ChatSource[])
          } else if (data.type === 'token') {
            full += String(data.content)
            handlers.onToken(String(data.content))
          } else if (data.type === 'done') {
            finished = true
            handlers.onDone(String(data.answer), data.sources as ChatSource[])
          } else if (data.type === 'error') {
            finished = true
            handlers.onError(new Error(String(data.message)))
          }
        }
      }
      if (!finished) {
        handlers.onError(new Error('La conexión se cerró sin respuesta completa.'))
      }
    })
    .catch(handlers.onError)
}