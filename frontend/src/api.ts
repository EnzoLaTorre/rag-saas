import axios from 'axios'
import { clearToken, getToken } from './auth'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

const http = axios.create({ baseURL: API_BASE })

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      clearToken()
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

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

export interface ChatMessageInfo {
  id: number
  question: string
  answer: string
  sources_json: string
  created_at: string
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

export async function getHistory(): Promise<ChatMessageInfo[]> {
  const res = await http.get('/chat/history')
  return res.data
}

export type StreamEvent =
  | { type: 'sources'; sources: ChatSource[] }
  | { type: 'token'; content: string }
  | { type: 'done'; answer: string; sources: ChatSource[] }
  | { type: 'error'; message: string }

export function parseEvent(raw: string): StreamEvent | null {
  const line = raw.trim()
  if (!line.startsWith('data:')) return null
  try {
    return JSON.parse(line.slice(5).trim()) as StreamEvent
  } catch {
    return null
  }
}

export function splitSSEBuffer(buffer: string): { events: StreamEvent[]; rest: string } {
  const parts = buffer.split('\n\n')
  const rest = parts.pop() ?? ''
  const events = parts.map(parseEvent).filter((e): e is StreamEvent => e !== null)
  return { events, rest }
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
  fetch(`${API_BASE}/chat/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ question, document_id: documentId }),
  })
    .then(async (res) => {
      if (res.status === 401) {
        clearToken()
        window.location.assign('/login')
        return
      }
      if (!res.ok || !res.body) throw new Error(await res.text())
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finished = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const { events, rest } = splitSSEBuffer(buffer)
        buffer = rest

        for (const data of events) {
          if (data.type === 'sources') {
            handlers.onSources(data.sources)
          } else if (data.type === 'token') {
            handlers.onToken(data.content)
          } else if (data.type === 'done') {
            finished = true
            handlers.onDone(data.answer, data.sources)
          } else if (data.type === 'error') {
            finished = true
            handlers.onError(new Error(data.message))
          }
        }
      }
      if (!finished) {
        handlers.onError(new Error('La conexión se cerró sin respuesta completa.'))
      }
    })
    .catch(handlers.onError)
}