import { Link } from 'react-router-dom'
import { ArrowLeft, BookOpen, GraduationCap, Sparkles } from 'lucide-react'

export default function AuthFrame({ children, mode = 'login' }) {
  return (
    <main className="auth-page">
      <section className="auth-form-side">
        <Link to="/" className="brand-lockup auth-brand"><span className="brand-mark"><GraduationCap size={23} strokeWidth={2.5} /></span><span>EduPilot<span className="brand-ai">AI</span></span></Link>
        <div className="auth-form-wrap">
          <Link to="/" className="back-link"><ArrowLeft size={16} /> Back to home</Link>
          {children}
        </div>
        <p className="auth-legal">By continuing, you agree to use EduPilot kindly and responsibly.</p>
      </section>
      <aside className="auth-visual">
        <div className="auth-visual-glow" />
        <div className="auth-visual-top"><span className="tiny-orbit"><Sparkles size={15} /></span><span>Your next chapter starts here</span></div>
        <div className="auth-illustration" aria-hidden="true"><div className="illustration-ring ring-one" /><div className="illustration-ring ring-two" /><div className="book-stack"><div className="book book-back"><span /></div><div className="book book-mid"><span /></div><div className="book book-front"><BookOpen size={52} /></div><span className="book-spark spark-one">✦</span><span className="book-spark spark-two">✧</span></div><div className="float-note note-a">✦ &nbsp; Learn at your pace</div><div className="float-note note-b">✓ &nbsp; One step at a time</div></div>
        <div className="auth-visual-copy"><h2>{mode === 'register' ? 'Make space for your curiosity.' : 'A calmer way to keep learning.'}</h2><p>Build good study habits, explore new ideas, and celebrate how far you’ve come.</p><div className="auth-dots"><i /><i /><i /></div></div>
      </aside>
    </main>
  )
}
