import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, UserRound } from 'lucide-react'
import AuthFrame from '../../components/AuthFrame'
import { useAuth } from '../../hooks/useAuth'

function messageFromError(error) {
  const data = error.response?.data
  if (typeof data?.error === 'string') return data.error
  if (typeof data?.detail === 'string') return data.detail
  if (Array.isArray(data?.details)) return data.details.map((item) => item.msg).join('. ')
  return 'We could not create your account. Please try again.'
}

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await register({ full_name: fullName.trim(), email: email.trim(), password })
      navigate('/login', { replace: true, state: { email: email.trim(), registered: true } })
    } catch (requestError) {
      setError(messageFromError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return <AuthFrame mode="register"><div className="auth-heading"><span className="eyebrow">A FRESH START</span><h1>Create your account.</h1><p>Make a little room for what you want to learn.</p></div>{error && <div className="error-alert" role="alert">{error}</div>}<form className="auth-form" onSubmit={handleSubmit}><label htmlFor="fullName">Your name</label><div className="input-wrap"><UserRound size={17} /><input id="fullName" autoComplete="name" placeholder="Your name" value={fullName} onChange={(event) => setFullName(event.target.value)} maxLength={255} required /></div><label htmlFor="email">Email address</label><div className="input-wrap"><Mail size={17} /><input id="email" type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(event) => setEmail(event.target.value)} required /></div><label htmlFor="password">Create a password</label><div className="input-wrap"><LockKeyhole size={17} /><input id="password" type={showPassword ? 'text' : 'password'} autoComplete="new-password" placeholder="At least 8 characters" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} maxLength={72} required /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div><small className="field-hint">Use 8–72 characters. Your account will start with student access.</small><button className="button button-dark auth-submit" type="submit" disabled={busy}>{busy ? <><span className="button-spinner" /> Creating account…</> : <>Create account <ArrowRight size={16} /></>}</button></form><p className="auth-switch">Already have an account? <Link to="/login">Log in</Link></p></AuthFrame>
}
