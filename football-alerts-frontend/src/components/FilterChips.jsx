import styles from './FilterChips.module.css'

/**
 * FilterChips — reusable multi-select filter component.
 *
 * Props:
 *   label      — string shown above the chips e.g. "FILTER BY LEAGUE"
 *   options    — [{ value, label }] array
 *   selected   — Set of selected values
 *   onChange   — (newSet) => void
 *   color      — 'accent' | 'neutral' (default: 'accent')
 */
export default function FilterChips({ label, options, selected, onChange, color = 'accent' }) {
  if (!options || options.length === 0) return null

  const toggle = (value) => {
    const next = new Set(selected)
    if (next.has(value)) {
      next.delete(value)
    } else {
      next.add(value)
    }
    onChange(next)
  }

  const clearAll = () => onChange(new Set())

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        {selected.size > 0 && (
          <button className={styles.clearBtn} onClick={clearAll}>
            CLEAR
          </button>
        )}
      </div>
      <div className={styles.chips}>
        {options.map(opt => {
          const active = selected.has(opt.value)
          return (
            <button
              key={opt.value}
              className={`${styles.chip} ${active ? styles.chipActive : ''} ${color === 'neutral' ? styles.chipNeutral : ''} ${active && color === 'neutral' ? styles.chipNeutralActive : ''}`}
              onClick={() => toggle(opt.value)}
            >
              {active && <span className={styles.chipCheck}>✓</span>}
              {opt.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}