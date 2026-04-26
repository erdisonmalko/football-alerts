import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register, login, getMe } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'
import styles from './Auth.module.css'
import { parseApiError } from '../api/errorHandler'

export default function Register() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', fullName: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.email, form.password, form.fullName)
      const { access_token } = await login(form.email, form.password)
      const user = await getMe()
      signIn(access_token, user)
      navigate('/subscriptions')
    } catch (err) {
      setError(parseApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.badge}>FOOTBALL ALERTS</div>
        <h1 className={styles.title}>CREATE<br />ACCOUNT</h1>
        <p className={styles.sub}>Never miss a match again.</p>

        <form onSubmit={handle} className={styles.form}>
          <div className={styles.field}>
            <label>FULL NAME</label>
            <input
              type="text"
              value={form.fullName}
              onChange={e => setForm(f => ({ ...f, fullName: e.target.value }))}
              placeholder="Your name"
            />
          </div>
          <div className={styles.field}>
            <label>EMAIL</label>
            <input
              type="email"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder="you@example.com"
              required
            />
          </div>
          <div className={styles.field}>
            <label>PASSWORD</label>
            <input
              type="password"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder="Min 8 chars, at least one number"
              required
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.btn} disabled={loading}>
            {loading ? 'CREATING...' : 'CREATE ACCOUNT'}
          </button>
        </form>

        <p className={styles.switch}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
