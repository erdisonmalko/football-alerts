import styles from './FeedbackBanner.module.css'

export default function FeedbackBanner({ type = 'success', message, onClose }) {
  if (!message) return null

  return (
    <div className={`${styles.banner} ${type === 'error' ? styles.error : styles.success}`} role="status">
      <p className={styles.message}>{message}</p>
      <button
        type="button"
        className={styles.closeButton}
        onClick={onClose}
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  )
}
