import { useState } from 'react'
import styles from './ServerCreateModal.module.css'

export default function ServerCreateModal({ onClose, onCreate, isLoading }) {
  const [name, setName] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Server name is required')
      return
    }

    try {
      await onCreate(name.trim(), isPublic)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create server')
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>CREATE NEW SERVER</h2>
          <button className={styles.close} onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="serverName">Server Name</label>
            <input
              id="serverName"
              type="text"
              placeholder="e.g., Premier League Predictions"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
              autoFocus
            />
          </div>

          <div className={styles.formGroup}>
            <label>Server Type</label>
            <div className={styles.radioGroup}>
              <label className={styles.radioLabel}>
                <input
                  type="radio"
                  name="serverType"
                  value="public"
                  checked={isPublic}
                  onChange={() => setIsPublic(true)}
                  disabled={isLoading}
                />
                <span className={styles.radioText}>
                  <strong>PUBLIC</strong> - Anyone can join
                </span>
              </label>
              <label className={styles.radioLabel}>
                <input
                  type="radio"
                  name="serverType"
                  value="private"
                  checked={!isPublic}
                  onChange={() => setIsPublic(false)}
                  disabled={isLoading}
                />
                <span className={styles.radioText}>
                  <strong>PRIVATE</strong> - Users must request to join
                </span>
              </label>
            </div>
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.footer}>
            <button
              type="button"
              className={styles.cancelBtn}
              onClick={onClose}
              disabled={isLoading}
            >
              CANCEL
            </button>
            <button
              type="submit"
              className={styles.createBtn}
              disabled={isLoading || !name.trim()}
            >
              {isLoading ? 'CREATING...' : 'CREATE SERVER'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
