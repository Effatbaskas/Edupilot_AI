import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { BookOpenCheck, BarChart3, ChevronDown, HelpCircle, Compass, GraduationCap, LayoutDashboard, LogOut, Menu, MessageCircle, ShieldCheck, Sparkles, X } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { getInitials } from '../utils/formatters'

const links = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/tutor', label: 'AI study room', icon: MessageCircle },
  { to: '/quiz', label: 'Practice', icon: BookOpenCheck },
  { to: '/roadmap', label: 'Study plan', icon: Compass },
  { to: '/progress', label: 'My progress', icon: BarChart3 },
]

const pageTitles = {
  '/dashboard': ['Your learning space', 'A little progress each day adds up.'],
  '/tutor': ['AI study room', 'Ask a question and explore a concept.'],
  '/quiz': ['Practice corner', 'Try a short knowledge check.'],
  '/roadmap': ['Your study plan', 'A gentle plan to keep you moving.'],
  '/progress': ['Your progress', 'See the habits you are building.'],
  '/admin': ['Admin workspace', 'Manage EduPilot accounts securely.'],
}

export default function AppLayout({ children }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()
  const [title, subtitle] = pageTitles[location.pathname] || pageTitles['/dashboard']

  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`}>
        <NavLink to="/dashboard" className="brand-lockup" onClick={() => setMenuOpen(false)}>
          <span className="brand-mark"><GraduationCap size={23} strokeWidth={2.5} /></span>
          <span>EduPilot<span className="brand-ai">AI</span></span>
        </NavLink>
        <div className="sidebar-label">LEARN</div>
        <nav className="side-nav" aria-label="Main navigation">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`} onClick={() => setMenuOpen(false)}>
              <Icon size={19} /><span>{label}</span>{to === '/tutor' && <span className="nav-new">NEW</span>}
            </NavLink>
          ))}
          {user?.role === 'admin' && <NavLink to="/admin" className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`} onClick={() => setMenuOpen(false)}><ShieldCheck size={19} /><span>Admin tools</span></NavLink>}
        </nav>
        <div className="sidebar-bottom">
          <div className="help-card"><span className="help-icon"><HelpCircle size={17} /></span><div><strong>Keep going!</strong><p>Small steps make big things.</p></div><Sparkles size={17} className="help-sparkle" /></div>
          <button className="profile-row" onClick={logout} title="Sign out">
            <span className="avatar">{getInitials(user?.full_name)}</span>
            <span className="profile-copy"><strong>{user?.full_name || 'Learner'}</strong><small>{user?.role || 'student'}</small></span>
            <LogOut size={17} className="logout-icon" />
          </button>
        </div>
      </aside>
      {menuOpen && <button className="mobile-scrim" onClick={() => setMenuOpen(false)} aria-label="Close navigation" />}
      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu-button icon-button" onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Close menu' : 'Open menu'}>{menuOpen ? <X size={21} /> : <Menu size={21} />}</button>
          <div className="topbar-title"><h1>{title}</h1><p>{subtitle}</p></div>
          <div className="topbar-right"><span className="topbar-date">{new Intl.DateTimeFormat('en', { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date())}</span><span className="avatar avatar-small">{getInitials(user?.full_name)}</span><ChevronDown size={15} className="topbar-chevron" /></div>
        </header>
        <div className="page-content">{children || <Outlet />}</div>
      </main>
    </div>
  )
}
