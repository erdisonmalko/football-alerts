import { useState } from 'react'
import styles from './JoinPrivateServerModal.module.css'

export default function JoinPrivateServerModal({
  isOpen,
  onClose,
  onSubmit, // (code) => Promise
  serverName
}) {
  const [code, setCode] = useState('')
  const [status, setStatus] = useState('idle') 
  // idle | typing | submitting | success | error

  const [error, setError] = useState(null)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!code.trim()) {
      setError('Invite code is required')
      setStatus('error')
      return
    }

    setStatus('submitting')
    setError(null)

    try {
      await onSubmit(code)

      setStatus('success')

      setTimeout(() => {
        handleClose()
      }, 1200)

    } catch (err) {
      setStatus('error')
      setError(
        err?.response?.data?.detail || 'Invalid or expired invite code'
      )
    }
  }

  const handleClose = () => {
    setCode('')
    setStatus('idle')
    setError(null)
    onClose()
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>

        <h3 className={styles.title}>Join Private Server</h3>

        <p className={styles.subtitle}>
          Enter invite code for <strong>{serverName}</strong>
        </p>

        <form onSubmit={handleSubmit}>

          <input
            className={`${styles.input} ${
              status === 'error' ? styles.inputError : ''
            }`}
            placeholder="Enter invite code..."
            value={code}
            onChange={(e) => {
              setCode(e.target.value)
              setStatus('typing')
              setError(null)
            }}
          />

          {error && (
            <p className={styles.error}>{error}</p>
          )}

          {status === 'success' && (
            <p className={styles.success}>Request sent ✓</p>
          )}

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.secondary}
              onClick={handleClose}
              disabled={status === 'submitting'}
            >
              Cancel
            </button>

            <button
              type="submit"
              className={styles.primary}
              disabled={status === 'submitting'}
            >
              {status === 'submitting' ? '...' : 'Submit'}
            </button>
          </div>

        </form>
      </div>
    </div>
  )
}