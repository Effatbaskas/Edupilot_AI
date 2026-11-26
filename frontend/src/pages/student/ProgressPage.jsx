import { useEffect, useState } from 'react'
import { Activity, AlertCircle, Award, BarChart3, BookOpenCheck, CheckCircle2, Target, TrendingUp } from 'lucide-react'
import DemoNotice from '../../components/DemoNotice'
import { performanceService } from '../../services/performanceService'

export default function ProgressPage() {
  const [overview, setOverview] = useState(null)
  const [topics, setTopics] = useState([])
  const [misconceptions, setMisconceptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([performanceService.getOverview(), performanceService.getTopics(), performanceService.getMisconceptions()])
      .then(([summary, topicRows, reports]) => {
        setOverview(summary)
        setTopics(topicRows || [])
        setMisconceptions(reports || [])
      })
      .catch((requestError) => setError(requestError.response?.data?.error || requestError.response?.data?.detail || 'Could not load your saved progress.'))
      .finally(() => setLoading(false))
  }, [])

  const trendLabel = { improving: 'Improving', declining: 'Needs attention', stable: 'Steady' }
  const toneFor = (score) => score >= 80 ? 'mint' : score >= 60 ? 'lavender' : 'peach'

  return <div className="feature-page">
    <div className="feature-intro"><div><span className="eyebrow">NOTICE HOW FAR YOU’VE COME</span><h2>Progress is more than a score.</h2><p>Scores and topic patterns come from your saved quiz attempts.</p></div><span className="feature-hero-icon progress-hero-icon"><BarChart3 size={24} /></span></div>
    <DemoNotice>These figures use quizzes saved by the backend. Study time and streaks are not tracked by this MVP.</DemoNotice>
    {error && <div className="error-alert" role="alert"><AlertCircle size={17} />{error}</div>}
    {loading ? <section className="panel admin-loading"><span className="spinner" /> Loading saved progress…</section> : <>
      <div className="progress-stats"><article className="progress-stat panel"><span className="stat-icon stat-lilac"><Award size={18} /></span><small>AVERAGE SCORE</small><strong>{Number(overview?.avg_score || 0).toFixed(0)}%</strong><span>From completed quiz attempts</span></article><article className="progress-stat panel"><span className="stat-icon stat-blue"><BookOpenCheck size={18} /></span><small>QUIZZES COMPLETED</small><strong>{overview?.total_quizzes || 0}</strong><span>Saved to your account</span></article><article className="progress-stat panel"><span className="stat-icon stat-mint"><Activity size={18} /></span><small>TOTAL ATTEMPTS</small><strong>{overview?.total_attempts || 0}</strong><span>Scored by the backend</span></article><article className="progress-stat panel"><span className="stat-icon stat-peach"><TrendingUp size={18} /></span><small>RECENT TREND</small><strong>{trendLabel[overview?.recent_trend] || 'Steady'}</strong><span>Compared with earlier attempts</span></article></div>
      <div className="progress-grid"><section className="panel topic-panel"><div className="panel-heading"><div><h3>Topic performance</h3><p>Based on your completed practice quizzes</p></div><Target size={17} className="muted-icon" /></div>{topics.length ? <div className="topic-bars">{topics.map((topic) => <div className="topic-progress" key={topic.topic}><div className="topic-progress-heading"><strong>{topic.topic}</strong><span>{Number(topic.score_pct || 0).toFixed(0)}%</span></div><div className="topic-track"><i className={toneFor(topic.score_pct)} style={{ width: `${Math.max(0, Math.min(100, topic.score_pct))}%` }} /></div><small>{topic.correct_count} correct of {topic.total_count} answers</small></div>)}</div> : <div className="admin-empty"><Target size={23} /><strong>No quiz results yet</strong><p>Complete a practice quiz to see saved topic scores.</p></div>}</section>
        <section className="panel topic-panel"><div className="panel-heading"><div><h3>Topics to revisit</h3><p>Rule-based notes from lower-scoring topics</p></div><Target size={17} className="muted-icon" /></div>{misconceptions.length ? <div className="topic-bars">{misconceptions.map((item) => <div className="topic-progress" key={item.topic}><div className="topic-progress-heading"><strong>{item.topic}</strong><span>{Number(item.score_percentage || 0).toFixed(0)}%</span></div><p>{item.evidence}</p><small>{item.suggestion}</small></div>)}</div> : <div className="admin-empty"><CheckCircle2 size={23} /><strong>No weak topics flagged</strong><p>More quiz attempts will help this summary become useful.</p></div>}</section>
      </div>
    </>}
  </div>
}
