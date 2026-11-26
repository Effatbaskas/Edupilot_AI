import { useEffect, useState } from 'react'
import { AlertCircle, ArrowLeft, ArrowRight, BookOpenCheck, CheckCircle2, Clock3, Loader2, RotateCcw, Sparkles, Target } from 'lucide-react'
import DemoNotice from '../../components/DemoNotice'
import { materialService } from '../../services/materialService'
import { quizService } from '../../services/quizService'

export default function QuizPage() {
  const [topic, setTopic] = useState('Biology')
  const [difficulty, setDifficulty] = useState('medium')
  const [numQuestions, setNumQuestions] = useState(5)
  const [quizType, setQuizType] = useState('mcq')
  const [materials, setMaterials] = useState([])
  const [savedQuizzes, setSavedQuizzes] = useState([])
  const [history, setHistory] = useState([])
  const [materialId, setMaterialId] = useState('')
  const [quiz, setQuiz] = useState(null)
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    materialService.getMaterials().then((data) => setMaterials(data.materials || [])).catch((requestError) => setError(requestError.response?.data?.error || requestError.response?.data?.detail || 'Could not load study materials.'))
    refreshSavedQuizzes().catch((requestError) => setError(requestError.response?.data?.error || requestError.response?.data?.detail || 'Could not load saved quizzes.'))
  }, [])

  async function refreshSavedQuizzes() {
    const [quizzes, attempts] = await Promise.all([quizService.getQuizzes(), quizService.getHistory()])
    setSavedQuizzes(quizzes)
    setHistory(attempts)
  }

  const question = quiz?.questions?.[current]
  const requestMessage = (requestError) => requestError.response?.data?.error || requestError.response?.data?.detail || 'The quiz service could not complete that request.'

  async function startQuiz(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await quizService.generateQuiz({
        topic: topic.trim(), difficulty, num_questions: Number(numQuestions), quiz_type: quizType,
        ...(materialId ? { material_id: materialId } : {}),
      })
      setQuiz(data)
      setCurrent(0)
      setAnswers({})
      setResult(null)
    } catch (requestError) {
      setError(requestMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  async function submitQuiz() {
    setLoading(true)
    setError('')
    try {
      setResult(await quizService.submitQuiz(quiz.id, answers))
      await refreshSavedQuizzes()
    } catch (requestError) {
      setError(requestMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  function reset() { setQuiz(null); setCurrent(0); setAnswers({}); setResult(null); setError('') }

  return <div className="feature-page">
    <div className="feature-intro"><div><span className="eyebrow">PRACTICE MAKES PROGRESS</span><h2>Try a quick knowledge check.</h2><p>A few gentle questions can help ideas stick.</p></div><span className="feature-hero-icon quiz-hero-icon"><BookOpenCheck size={24} /></span></div>
    <DemoNotice>Quizzes are generated and scored by the backend in deterministic mock mode. Results are saved to your account; they are not Gemini-generated.</DemoNotice>
    {error && <div className="error-alert" role="alert"><AlertCircle size={17} />{error}</div>}
    {!quiz && <form className="quiz-start panel" onSubmit={startQuiz}>
      <span className="quiz-start-icon"><Target size={27} /></span><span className="soft-tag">MOCK MODE · SAVED TO YOUR ACCOUNT</span><h3>Build a practice quiz</h3>
      <p>Choose a topic and the backend will create a short practice set. If you select a PDF, questions use its extracted text.</p>
      <label>Topic<input className="input-field" value={topic} onChange={(event) => setTopic(event.target.value)} minLength={2} maxLength={255} required /></label>
      <label>Study material (optional)<select className="input-field" value={materialId} onChange={(event) => setMaterialId(event.target.value)}><option value="">No material · topic-based practice</option>{materials.map((material) => <option key={material.id} value={material.id}>{material.title}</option>)}</select></label>
      <div className="quiz-meta"><label>Difficulty<select className="input-field" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label><label>Question type<select className="input-field" value={quizType} onChange={(event) => setQuizType(event.target.value)}><option value="mcq">Multiple choice</option><option value="short_answer">Short answer</option><option value="mixed">Mixed</option></select></label><label>Questions<input className="input-field" type="number" min="1" max="20" value={numQuestions} onChange={(event) => setNumQuestions(event.target.value)} /></label></div>
      <button className="button button-dark" type="submit" disabled={loading || topic.trim().length < 2}>{loading ? <Loader2 className="spin-icon" size={16} /> : <Sparkles size={16} />}{loading ? 'Creating…' : 'Create practice quiz'} <ArrowRight size={16} /></button>
    </form>}
    {quiz && !result && question && <section className="quiz-card panel">
      <div className="quiz-progress-head"><span>Question {current + 1} <small>of {quiz.questions.length}</small></span><span>{Math.round(((current + 1) / quiz.questions.length) * 100)}% complete</span></div>
      <div className="quiz-progress"><span style={{ width: `${((current + 1) / quiz.questions.length) * 100}%` }} /></div>
      <span className="quiz-topic">{question.topic || quiz.topic} · {quiz.difficulty} · MOCK</span><h3>{question.question_text}</h3>
      {question.options?.length ? <div className="quiz-options">{question.options.map((option, index) => <button type="button" key={`${question.id}-${index}`} className={`quiz-option ${answers[question.id] === option ? 'selected' : ''}`} onClick={() => setAnswers((currentAnswers) => ({ ...currentAnswers, [question.id]: option }))}><span className="option-letter">{String.fromCharCode(65 + index)}</span><span>{option}</span>{answers[question.id] === option && <CheckCircle2 size={17} />}</button>)}</div> : <label>Your answer<textarea className="input-field" rows={3} value={answers[question.id] || ''} onChange={(event) => setAnswers((currentAnswers) => ({ ...currentAnswers, [question.id]: event.target.value }))} /></label>}
      <div className="quiz-controls"><button type="button" className="button button-ghost" disabled={current === 0 || loading} onClick={() => setCurrent(current - 1)}><ArrowLeft size={15} /> Previous</button>{current < quiz.questions.length - 1 ? <button type="button" className="button button-dark" disabled={!answers[question.id]?.trim?.() && !answers[question.id] || loading} onClick={() => setCurrent(current + 1)}>Next question <ArrowRight size={15} /></button> : <button type="button" className="button button-dark" disabled={loading} onClick={submitQuiz}>{loading ? 'Scoring…' : 'Submit answers'} <CheckCircle2 size={15} /></button>}</div>
    </section>}
    {result && <section className="quiz-result panel"><span className="result-icon"><CheckCircle2 size={35} /></span><span className="eyebrow">PRACTICE COMPLETE · MOCK SCORING</span><h3>You answered {result.correct_count} of {result.total_questions} correctly.</h3><p>Your score: {result.score}% · saved to your account.</p><div className="result-review">{result.results.map((item) => <div className="review-row" key={item.question_id}><span className={item.is_correct ? 'review-correct' : 'review-missed'}>{item.is_correct ? <CheckCircle2 size={16} /> : <ArrowRight size={16} />}</span><div><strong>{item.topic}</strong><p>{item.question_text}</p><p>Your answer: {item.your_answer || 'No answer'} · Correct answer: {item.correct_answer}</p><p>{item.explanation}</p></div></div>)}</div><button className="button button-dark" onClick={reset}><RotateCcw size={15} /> Create another quiz</button></section>}
    {!quiz && <section className="panel topic-panel"><div className="panel-heading"><div><h3>Your saved practice</h3><p>Quizzes and scores stored in your account</p></div><Clock3 size={17} /></div>{savedQuizzes.length ? <div className="topic-bars">{savedQuizzes.map((saved) => { const attempt = history.find((item) => item.quiz_id === saved.id); return <div className="topic-progress" key={saved.id}><div className="topic-progress-heading"><strong>{saved.title}</strong><span>{attempt ? `${attempt.score}%` : 'Not submitted'}</span></div><small>{saved.topic} · {saved.difficulty} · {attempt ? `${attempt.correct_count}/${attempt.total_questions} correct` : 'Saved quiz'}</small></div> })}</div> : <div className="admin-empty"><BookOpenCheck size={23} /><strong>No saved quizzes yet</strong><p>Quizzes you create will appear here.</p></div>}</section>}
  </div>
}
