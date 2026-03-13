import styles from './Pagination.module.css'

export default function Pagination({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null

  const pages = []
  const delta = 2  // pages around current

  // Always show first, last, current±delta, with ellipsis gaps
  const range = new Set([
    1,
    totalPages,
    ...Array.from({ length: delta * 2 + 1 }, (_, i) => page - delta + i)
      .filter(p => p >= 1 && p <= totalPages),
  ])
  const sorted = [...range].sort((a, b) => a - b)

  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) pages.push('...')
    pages.push(p)
  })

  return (
    <div className={styles.pagination}>
      <button
        className={styles.arrow}
        onClick={() => onChange(page - 1)}
        disabled={page === 1}
      >
        PREV
      </button>

      <div className={styles.pages}>
        {pages.map((p, i) =>
          p === '...' ? (
            <span key={`ellipsis-${i}`} className={styles.ellipsis}>...</span>
          ) : (
            <button
              key={p}
              className={`${styles.pageBtn} ${p === page ? styles.active : ''}`}
              onClick={() => onChange(p)}
            >
              {p}
            </button>
          )
        )}
      </div>

      <button
        className={styles.arrow}
        onClick={() => onChange(page + 1)}
        disabled={page === totalPages}
      >
        NEXT
      </button>
    </div>
  )
}