import { describe, expect, it } from 'vitest'
import { parseEvent, splitSSEBuffer } from './api'

describe('parseEvent', () => {
  it('parsea un token', () => {
    expect(parseEvent('data: {"type":"token","content":"hola"}')).toEqual({
      type: 'token',
      content: 'hola',
    })
  })

  it('parsea sources con documentos', () => {
    const ev = parseEvent(
      'data: {"type":"sources","sources":[{"chunk_id":"1_0","text":"hola","document_id":1,"chunk_index":0}]}',
    )
    expect(ev?.type).toBe('sources')
  })

  it('ignora líneas que no son data:', () => {
    expect(parseEvent(': keep-alive')).toBeNull()
    expect(parseEvent('')).toBeNull()
  })

  it('devuelve null si el JSON es inválido', () => {
    expect(parseEvent('data: {roto')).toBeNull()
  })
})

describe('splitSSEBuffer', () => {
  it('separa eventos completos y conserva el resto', () => {
    const buffer =
      'data: {"type":"token","content":"a"}\n\n' +
      'data: {"type":"token","content":"b"}\n\n' +
      'data: {"typ'
    const { events, rest } = splitSSEBuffer(buffer)
    expect(events).toEqual([
      { type: 'token', content: 'a' },
      { type: 'token', content: 'b' },
    ])
    expect(rest).toBe('data: {"typ')
  })

  it('sin eventos completos devuelve todo como resto', () => {
    const { events, rest } = splitSSEBuffer('data: {"type":')
    expect(events).toEqual([])
    expect(rest).toBe('data: {"type":')
  })
})
