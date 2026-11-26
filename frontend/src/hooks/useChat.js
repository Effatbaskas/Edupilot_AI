import { useState, useCallback, useRef } from 'react'
import { tutorService } from '../services/tutorService'

const createId = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`

export const useChat = (initialSessionId = null) => {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(initialSessionId || createId())
  const abortRef = useRef(null)

  const sendMessage = useCallback(async (question, language = 'auto') => {
    if (!question.trim() || isLoading) return

    const userMessage = {
      id: createId(),
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      const data = await tutorService.sendMessage(question, sessionId, language)
      const assistantMessage = {
        id: createId(),
        role: 'assistant',
        content: data.answer || data.content || data.message,
        sources: data.sources || [],
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      if (data.session_id) {
        setSessionId(data.session_id)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get response. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, sessionId])

  const loadHistory = useCallback(async (sid) => {
    setIsLoading(true)
    try {
      const history = await tutorService.getChatHistory(sid || sessionId)
      setMessages(Array.isArray(history) ? history : history.messages || [])
    } catch {
      setMessages([])
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  const startNewSession = useCallback(() => {
    const newId = createId()
    setSessionId(newId)
    setMessages([])
    setError(null)
    return newId
  }, [])

  return {
    messages,
    isLoading,
    error,
    sessionId,
    sendMessage,
    loadHistory,
    startNewSession,
    setMessages,
  }
}
