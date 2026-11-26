import { useCallback, useEffect, useState } from 'react'
import { AlertCircle, Check, Loader2, RefreshCw, ShieldCheck, Users } from 'lucide-react'
import { adminService } from '../../services/adminService'
import { getInitials } from '../../utils/formatters'

function requestMessage(error) {
  const data = error.response?.data
  if (typeof data?.error === 'string') return data.error
  if (typeof data?.detail === 'string') return data.detail
  return 'Could not reach the admin API. Check that the backend is running.'
}

export default function AdminPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState('')
  const [notice, setNotice] = useState('')

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setUsers(await adminService.getUsers())
    } catch (requestError) {
      setError(requestMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadUsers() }, [loadUsers])

  async function changeRole(user, role) {
    if (user.role === role) return
    setSaving(user.id)
    setNotice('')
    setError('')
    try {
      const updated = await adminService.updateUserRole(user.id, role)
      setUsers((current) => current.map((item) => item.id === user.id ? updated : item))
      setNotice(`Updated ${user.full_name} to ${role}.`)
    } catch (requestError) {
      setError(requestMessage(requestError))
      await loadUsers()
    } finally {
      setSaving('')
    }
  }

  return <div className="feature-page admin-page"><div className="feature-intro"><div><span className="eyebrow">SECURE ADMINISTRATION</span><h2>People in your learning community.</h2><p>Account list and roles are loaded from the EduPilot backend.</p></div><span className="feature-hero-icon admin-hero-icon"><ShieldCheck size={24} /></span></div><div className="admin-toolbar"><div className="admin-live-label"><span /> Live backend data</div><button className="button button-outline" onClick={loadUsers} disabled={loading}><RefreshCw size={15} className={loading ? 'spin-icon' : ''} /> Refresh</button></div>{error && <div className="error-alert" role="alert"><AlertCircle size={17} /> {error}</div>}{notice && <div className="success-alert" role="status"><Check size={16} /> {notice}</div>}<section className="panel admin-table-panel"><div className="panel-heading"><div><h3>Accounts</h3><p>{loading ? 'Loading from the server…' : `${users.length} account${users.length === 1 ? '' : 's'} returned`}</p></div><span className="admin-count"><Users size={17} /> {users.length}</span></div>{loading ? <div className="admin-loading"><Loader2 size={23} className="spin-icon" /> Loading user accounts…</div> : users.length === 0 && !error ? <div className="admin-empty"><Users size={25} /><strong>No accounts returned</strong><p>Once learners register, they will show up here.</p></div> : <div className="table-scroll"><table className="user-table"><thead><tr><th>PERSON</th><th>ROLE</th><th>STATUS</th><th>JOINED</th><th>CHANGE ROLE</th></tr></thead><tbody>{users.map((user) => <tr key={user.id}><td><div className="user-cell"><span className="avatar table-avatar">{getInitials(user.full_name)}</span><span><strong>{user.full_name}</strong><small>{user.email}</small></span></div></td><td><span className={`role-chip role-${user.role}`}>{user.role}</span></td><td><span className={`status-chip ${user.is_active ? 'status-active' : 'status-inactive'}`}><i />{user.is_active ? 'Active' : 'Inactive'}</span></td><td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td><td><select aria-label={`Change role for ${user.full_name}`} value={user.role} disabled={saving === user.id} onChange={(event) => changeRole(user, event.target.value)}><option value="student">Student</option><option value="teacher">Teacher</option><option value="admin">Admin</option></select>{saving === user.id && <Loader2 size={14} className="spin-icon role-saving" />}</td></tr>)}</tbody></table></div>}</section><p className="admin-security-note"><ShieldCheck size={15} /> This page uses authenticated admin-only endpoints. Role changes are saved by the backend.</p></div>
}
