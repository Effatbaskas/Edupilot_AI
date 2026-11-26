import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import AppLayout from './components/AppLayout'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import DashboardPage from './pages/student/DashboardPage'
import TutorPage from './pages/student/TutorPage'
import QuizPage from './pages/student/QuizPage'
import RoadmapPage from './pages/student/RoadmapPage'
import ProgressPage from './pages/student/ProgressPage'
import AdminPage from './pages/admin/AdminPage'

function RouteLoader() {
  return <div className="page-loader"><span className="spinner" /> Checking your account…</div>
}

function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <RouteLoader />
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <AppLayout><Outlet /></AppLayout>
}

function RequireRole({ role, children }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <RouteLoader />
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  const { isAuthenticated, isLoading } = useAuth()

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={isLoading ? <RouteLoader /> : isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/register" element={isLoading ? <RouteLoader /> : isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/tutor" element={<TutorPage />} />
        <Route path="/quiz" element={<QuizPage />} />
        <Route path="/roadmap" element={<RoadmapPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/admin" element={<RequireRole role="admin"><AdminPage /></RequireRole>} />
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/'} replace />} />
    </Routes>
  )
}
