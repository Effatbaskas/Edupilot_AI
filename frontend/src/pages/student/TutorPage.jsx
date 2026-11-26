import { useEffect, useRef, useState } from 'react'
import { AlertCircle, ArrowDown, ArrowRight, BookOpen, Bot, Lightbulb, Loader2, MessageCircle, RotateCcw, Send, Sparkles, UserRound } from 'lucide-react'
import DemoNotice from '../../components/DemoNotice'
import { tutorService } from '../../services/tutorService'

const prompts = ['Explain photosynthesis simply', 'What is a cell?', 'Help me plan a study break']
const createSessionId = () => globalThis.crypto?.randomUUID?.() || 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
  const random = Math.random() * 16 | 0
  return (char === 'x' ? random : (random & 0x3 | 0x8)).toString(16)
})

export default function TutorPage() {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [showHints, setShowHints] = useState(true)
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('tutor_session_id') || createSessionId())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    localStorage.setItem('tutor_session_id', sessionId)
    let active = true
    tutorService.getChatHistory(sessionId).then((history) => {
      if (active && history.messages?.length) {
        setMessages(history.messages)
        setShowHints(false)
      }
    }).catch(() => {
      if (active) setError('Chat history could not be loaded. You can still start a new message.')
    })
    return () => { active = false }
  }, [sessionId])

  async function sendMessage(value = question) {
    const text = value.trim()
    if (!text || isLoading) return
    const userMessage = { id: createSessionId(), role: 'user', content: text, created_at: new Date().toISOString() }
    setMessages((current) => [...current, userMessage])
    setQuestion('')
    setShowHints(false)
    setError('')
    setIsLoading(true)
    try {
      const response = await tutorService.sendMessage(text, sessionId)
      setMessages((current) => [...current, {
        id: createSessionId(), role: 'assistant', content: response.answer,
        sources: response.sources || [], created_at: new Date().toISOString(), mode: response.mode,
      }])
      if (response.session_id && response.session_id !== sessionId) setSessionId(response.session_id)
    } catch (requestError) {
      setMessages((current) => current.filter((message) => message.id !== userMessage.id))
      setError(requestError.response?.data?.error || requestError.response?.data?.detail || 'Could not reach the tutor service. Please try again.')
      setQuestion(text)
    } finally {
      setIsLoading(false)
    }
  }

  return <div className="feature-page tutor-page">
    <div className="feature-intro"><div><span className="eyebrow">A FRIENDLY PLACE TO WONDER</span><h2>What are you curious about?</h2><p>Ask a question, share a tricky topic, or start with one of these ideas.</p></div><span className="feature-hero-icon tutor-hero-icon"><MessageCircle size={24} /></span></div>
    <DemoNotice>The backend returns deterministic mock tutoring, not Gemini. Messages are saved to your account when the API is available.</DemoNotice>
    {error && <div className="error-alert" role="alert"><AlertCircle size={17} />{error}</div>}
    <section className="tutor-workspace">
      <div className="tutor-topline"><div className="tutor-identity"><span className="tutor-avatar"><Sparkles size={18} /></span><div><strong>Study buddy <span className="local-tag">MOCK MODE</span></strong><small>Here to help you think it through</small></div></div><button className="icon-button" onClick={() => { setSessionId(createSessionId()); setMessages([]); setShowHints(true); setError('') }} aria-label="Start a new chat"><RotateCcw size={17} /></button></div>
      <div className="tutor-messages">{messages.length === 0 ? <div className="tutor-empty"><span className="tutor-empty-illustration"><Lightbulb size={34} /></span><h3>Every question is a good start.</h3><p>Ask the mock tutor for a short study prompt. It is not a live Gemini answer.</p>{showHints && <div className="prompt-chips">{prompts.map((prompt) => <button key={prompt} onClick={() => sendMessage(prompt)}>{prompt}<ArrowRight size={14} /></button>)}</div>}</div> : messages.map((message, index) => <div className={`chat-message ${message.role}`} key={`${message.role}-${message.id || index}`}><span className={`chat-avatar ${message.role}`}>{message.role === 'assistant' ? <Bot size={17} /> : <UserRound size={17} />}</span><div><small>{message.role === 'assistant' ? 'Mock tutor · not Gemini' : 'You'}</small><p>{message.content}</p></div></div>)}</div>
      <form className="chat-compose" onSubmit={(event) => { event.preventDefault(); sendMessage() }}><textarea ref={inputRef} rows={2} placeholder="Type a question or topic…" value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage() } }} aria-label="Your question" disabled={isLoading} /><div className="compose-bottom"><span><BookOpen size={14} /> Shift + Enter for a new line</span><button type="submit" className="button button-dark" disabled={!question.trim() || isLoading}>{isLoading ? <Loader2 className="spin-icon" size={15} /> : <Send size={15} />}{isLoading ? 'Thinking…' : 'Send'}</button></div></form>
    </section><div className="tutor-footnote"><ArrowDown size={15} /> Chat history is stored with your account.</div>
  </div>
}
