import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from 'lucide-react'
import AuthFrame from '../../components/AuthFrame'
import { useAuth } from '../../hooks/useAuth'

function messageFromError(error) {
  const data = error.response?.data
  if (typeof data?.error === 'string') return data.error
  if (typeof data?.detail === 'string') return data.detail
  return 'We could not sign you in. Check your connection and try again.'
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState(location.state?.email || '')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email.trim(), password)
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (requestError) {
      setError(messageFromError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return <AuthFrame><div className="auth-heading"><span className="eyebrow">WELCOME BACK</span><h1>Good to see you.</h1><p>Log in to pick up where you left off.</p></div>{location.state?.registered && <div className="success-alert">Your account is ready. Sign in to continue.</div>}{error && <div className="error-alert" role="alert">{error}</div>}<form className="auth-form" onSubmit={handleSubmit}><label htmlFor="email">Email address</label><div className="input-wrap"><Mail size={17} /><input id="email" type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(event) => setEmail(event.target.value)} required /></div><label htmlFor="password">Password</label><div className="input-wrap"><LockKeyhole size={17} /><input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} required /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div><button className="button button-dark auth-submit" type="submit" disabled={busy}>{busy ? <><span className="button-spinner" /> Signing in…</> : <>Log in <ArrowRight size={16} /></>}</button></form><p className="auth-switch">New to EduPilot? <Link to="/register">Create an account</Link></p></AuthFrame>
}
