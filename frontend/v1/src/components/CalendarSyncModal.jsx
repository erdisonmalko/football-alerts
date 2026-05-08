import styles from './CalendarSyncModal.module.css'

export default function CalendarSyncModal({
  isOpen,
  isConnected,
  syncing,
  errorMessage,
  onClose,
  onConnect,
  onConfirm,
}) {
  if (!isOpen) return null

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>
            {isConnected ? 'Add to Google Calendar' : 'Connect Google Calendar'}
          </h3>
          {errorMessage && (
            <span className={styles.badge}>Reconnect required</span>
          )}
        </div>

        <p className={styles.text}>
          {isConnected
            ? 'Block time on your calendar for this match and get notified by Google before kickoff.'
            : 'Connect your Google Calendar to block time for matches and get reminders from Google.'}
        </p>
        {errorMessage && (
          <p className={styles.errorText}>{errorMessage}</p>
        )}

        <div className={styles.actions}>
          {isConnected ? (
            <>
              <button
                className={styles.primary}
                onClick={onConfirm}
                disabled={syncing}
              >
                {syncing ? 'ADDING...' : 'ADD TO CALENDAR'}
              </button>
              <button className={styles.secondary} onClick={onClose} disabled={syncing}>
                SKIP
              </button>
            </>
          ) : (
            <>
              <button className={styles.primary} onClick={onConnect}>
                CONNECT GOOGLE
              </button>
              <button className={styles.secondary} onClick={onClose}>
                MAYBE LATER
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}