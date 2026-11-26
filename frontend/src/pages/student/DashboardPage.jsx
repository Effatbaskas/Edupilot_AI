import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ArrowRight, BookOpen, BookOpenCheck, Check, Eye, FolderOpen, Loader2, MessageCircle, Search, Sparkles, Target, Trash2, UploadCloud, X } from 'lucide-react'
import api from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import { DemoPill } from '../../components/DemoNotice'
import { materialService } from '../../services/materialService'
import { performanceService } from '../../services/performanceService'

const week = [
  { day: 'M', value: 42 }, { day: 'T', value: 74 }, { day: 'W', value: 56 },
  { day: 'T', value: 91 }, { day: 'F', value: 64 }, { day: 'S', value: 36 }, { day: 'S', value: 52 },
]

export default function DashboardPage() {
  const { user } = useAuth()
  const [apiStatus, setApiStatus] = useState('checking')
  const [overview, setOverview] = useState(null)
  const [overviewError, setOverviewError] = useState('')
  const [materials, setMaterials] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [materialSearch, setMaterialSearch] = useState('')
  const [materialDetails, setMaterialDetails] = useState(null)
  const [materialAction, setMaterialAction] = useState('')
  const fileInput = useRef(null)
  const firstName = user?.full_name?.trim().split(/\s+/)[0] || 'Learner'

  useEffect(() => {
    let active = true
    api.get('/health', { timeout: 5000 }).then(() => active && setApiStatus('online')).catch(() => active && setApiStatus('offline'))
    performanceService.getOverview().then((data) => active && setOverview(data)).catch(() => active && setOverviewError('Saved learning statistics could not be loaded.'))
    materialService.getMaterials().then((data) => active && setMaterials(data.materials || [])).catch(() => active && setUploadError('Your saved materials could not be loaded.'))
    return () => { active = false }
  }, [])

  async function uploadMaterial(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadError('')
    try {
      await materialService.uploadMaterial(file)
      const data = await materialService.getMaterials(materialSearch)
      setMaterials(data.materials || [])
    } catch (error) {
      setUploadError(error.response?.data?.error || error.response?.data?.detail || 'Could not upload this PDF. Check that it is a readable PDF under the size limit.')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  async function searchMaterials(event) {
    event.preventDefault()
    setMaterialAction('search')
    setUploadError('')
    try {
      const data = await materialService.getMaterials(materialSearch.trim())
      setMaterials(data.materials || [])
      setMaterialDetails(null)
    } catch (error) {
      setUploadError(error.response?.data?.error || error.response?.data?.detail || 'Could not search your materials.')
    } finally {
      setMaterialAction('')
    }
  }

  async function viewMaterial(materialId) {
    setMaterialAction(materialId)
    setUploadError('')
    try {
      setMaterialDetails(await materialService.getMaterial(materialId))
    } catch (error) {
      setUploadError(error.response?.data?.error || error.response?.data?.detail || 'Could not load this material.')
    } finally {
      setMaterialAction('')
    }
  }

  async function deleteMaterial(materialId) {
    if (!window.confirm('Delete this uploaded PDF and its saved text?')) return
    setMaterialAction(materialId)
    setUploadError('')
    try {
      await materialService.deleteMaterial(materialId)
      setMaterials((current) => current.filter((item) => item.id !== materialId))
      if (materialDetails?.id === materialId) setMaterialDetails(null)
    } catch (error) {
      setUploadError(error.response?.data?.error || error.response?.data?.detail || 'Could not delete this material.')
    } finally {
      setMaterialAction('')
    }
  }

  return <div className="dashboard-page">
    <div className="welcome-row"><div><div className="eyebrow">{new Date().toLocaleDateString('en', { weekday: 'long', month: 'long', day: 'numeric' })}</div><h2>Hey, {firstName} <span className="wave">✦</span></h2><p>Every curious question is a good place to begin.</p></div><div className={`connection-status ${apiStatus}`}><span /> API {apiStatus === 'checking' ? 'checking' : apiStatus}</div></div>
    {user?.role !== 'student' && <div className="info-alert">You’re signed in with <strong>{user.role}</strong> access. Learning activities below are a student experience preview.</div>}
    {overviewError && <div className="error-alert" role="alert"><AlertCircle size={16} />{overviewError}</div>}
    <section className="hero-banner"><div className="banner-copy"><span className="banner-kicker"><Sparkles size={14} /> A SMALL STEP TODAY</span><h3>Make today a<br />good study day.</h3><p>Choose one topic, take your time, and see what you discover.</p><Link className="button button-dark" to="/tutor">Start with a question <ArrowRight size={16} /></Link></div><div className="banner-art" aria-hidden="true"><div className="banner-sun" /><div className="banner-arch"><div className="arch-book"><BookOpen size={43} /></div></div><span className="banner-star star-one">✦</span><span className="banner-star star-two">✧</span><span className="banner-leaf leaf-one">❋</span><span className="banner-leaf leaf-two">❋</span><span className="banner-note">You’ve got this!</span></div></section>
    <DemoPill />
    <div className="stats-grid"><article className="stat-card"><span className="stat-icon stat-lilac"><Target size={19} /></span><span className="stat-label">Average score</span><strong>{overview ? `${Math.round(overview.avg_score)}%` : '—'}</strong><span className="stat-foot">Saved quiz results</span></article><article className="stat-card"><span className="stat-icon stat-peach"><BookOpenCheck size={19} /></span><span className="stat-label">Quizzes completed</span><strong>{overview?.total_quizzes ?? '—'}</strong><span className="stat-foot">From your account</span></article><article className="stat-card"><span className="stat-icon stat-mint"><Sparkles size={19} /></span><span className="stat-label">Recorded attempts</span><strong>{overview?.total_attempts ?? '—'}</strong><span className="stat-foot">Scored by the backend</span></article><article className="stat-card"><span className="stat-icon stat-blue"><FolderOpen size={19} /></span><span className="stat-label">Study materials</span><strong>{materials.length}</strong><span className="stat-foot">PDFs saved to your account</span></article></div>
    <div className="dashboard-columns"><section className="panel weekly-panel"><div className="panel-heading"><div><h3>Your weekly rhythm</h3><p>A little time set aside can go a long way.</p></div><span className="soft-tag">Sample week</span></div><div className="weekly-chart"><div className="chart-scale"><span>3h</span><span>2h</span><span>1h</span><span>0</span></div><div className="chart-bars">{week.map((item, index) => <div className="chart-column" key={`${item.day}-${index}`}><div className={`bar-track ${index === 3 ? 'highlight' : ''}`}><div className="bar-fill" style={{ height: `${item.value}%` }} /></div><span>{item.day}</span></div>)}</div></div><div className="chart-footer"><span><i className="legend-dot" /> Study minutes (sample)</span><strong>4.5 hrs <small>this week</small></strong></div></section>
      <section className="panel focus-panel"><div className="panel-heading"><div><h3>Pick your next step</h3><p>Try whichever feels right today.</p></div><span className="sparkle-bubble"><Sparkles size={17} /></span></div><div className="focus-options"><Link to="/tutor" className="focus-option"><span className="focus-option-icon option-peach"><MessageCircle size={18} /></span><span><strong>Ask a question</strong><small>Explore an idea</small></span><ArrowRight size={16} /></Link><Link to="/quiz" className="focus-option"><span className="focus-option-icon option-lilac"><BookOpenCheck size={18} /></span><span><strong>Try a practice quiz</strong><small>Check what you know</small></span><ArrowRight size={16} /></Link><Link to="/roadmap" className="focus-option"><span className="focus-option-icon option-mint"><Target size={18} /></span><span><strong>See your study plan</strong><small>Find one small step</small></span><ArrowRight size={16} /></Link></div></section></div>
    <section className="panel materials-panel"><div className="panel-heading"><div><h3>Your study shelf</h3><p>Upload a text-readable PDF to use with mock tutor and quiz tools.</p></div><div><input ref={fileInput} type="file" accept="application/pdf,.pdf" hidden onChange={uploadMaterial} /><button type="button" className="button button-outline" onClick={() => fileInput.current?.click()} disabled={uploading}>{uploading ? <Loader2 className="spin-icon" size={16} /> : <UploadCloud size={16} />}{uploading ? 'Uploading…' : 'Add PDF'}</button></div></div>{uploadError && <div className="error-alert" role="alert"><AlertCircle size={16} />{uploadError}</div>}
      <form onSubmit={searchMaterials} className="quiz-meta"><label>Search your PDFs<input className="input-field" value={materialSearch} onChange={(event) => setMaterialSearch(event.target.value)} placeholder="Search by title" /></label><button className="button button-outline button-small" type="submit" disabled={materialAction === 'search'}><Search size={15} /> Search</button></form>
      {materialDetails && <div className="empty-materials"><span className="empty-icon"><BookOpen size={19} /></span><div><strong>{materialDetails.title}</strong><p>{materialDetails.filename} · {materialDetails.status} · {materialDetails.total_chunks} text sections · {Math.ceil(materialDetails.file_size / 1024)} KB</p></div><button type="button" className="button button-ghost button-small" onClick={() => setMaterialDetails(null)} aria-label="Close material details"><X size={15} /></button></div>}
      {materials.length ? materials.map((material) => <div className="empty-materials" key={material.id}><span className="empty-icon"><BookOpen size={19} /></span><div><strong>{material.title}</strong><p>{material.filename} · {material.status} · {material.total_chunks || 0} text sections</p></div><button type="button" className="button button-ghost button-small" onClick={() => viewMaterial(material.id)} disabled={materialAction === material.id} aria-label={`View ${material.title}`}>{materialAction === material.id ? <Loader2 className="spin-icon" size={15} /> : <Eye size={15} />}</button><button type="button" className="button button-ghost button-small" onClick={() => deleteMaterial(material.id)} disabled={materialAction === material.id} aria-label={`Delete ${material.title}`}><Trash2 size={15} /></button></div>) : <div className="empty-materials"><span className="empty-icon"><FolderOpen size={23} /></span><div><strong>{materialSearch ? 'No matching materials' : 'Your shelf is ready for a first resource'}</strong><p>Choose a readable PDF under the backend file-size limit.</p></div></div>}</section>
    <div className="dashboard-bottom"><div className="mini-tip"><span className="tip-icon"><Sparkles size={19} /></span><div><small>A GENTLE REMINDER</small><strong>Rest is part of learning, too.</strong><p>Try a short pause between study sessions.</p></div><span className="tip-check"><Check size={16} /></span></div><Link to="/progress" className="see-progress">See all progress <ArrowRight size={15} /></Link></div>
  </div>
}
