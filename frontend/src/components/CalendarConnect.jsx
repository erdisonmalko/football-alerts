import styles from './CalendarConnectModal.module.css'

export default function CalendarConnectModal({ isOpen, onClose, onConnect }) {
  if (!isOpen) return null

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <h3 className={styles.title}>Connect Google Calendar</h3>

        <p className={styles.text}>
          Automatically add match reminders to your calendar and block time before kickoff.
        </p>

        <div className={styles.actions}>
          <button className={styles.primary} onClick={onConnect}>
            Connect Google
          </button>

          <button className={styles.secondary} onClick={onClose}>
            Maybe later
          </button>
        </div>
      </div>
    </div>
  )
}