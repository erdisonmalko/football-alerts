import styles from './ConfirmationDialog.module.css'

export default function ConfirmationDialog({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  isLoading = false,
  confirmVariant = 'primary',
  children,
}) {
  if (!isOpen) return null

  const confirmClass = confirmVariant === 'danger'
    ? styles.confirmButtonDanger
    : styles.confirmButton

  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>
          <button
            type="button"
            className={styles.close}
            onClick={onCancel}
            aria-label="Close confirmation dialog"
          >
            ×
          </button>
        </div>

        {description && <p className={styles.description}>{description}</p>}
        {children}

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={confirmClass}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? '...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
