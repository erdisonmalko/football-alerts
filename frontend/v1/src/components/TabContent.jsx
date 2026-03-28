import { useEffect, useState, useMemo } from 'react'
import Pagination from './Pagination'
import MatchRow from './MatchRow'
import styles from '../pages/Dashboard.module.css'

export default function TabContent({ matches, section, pageSize, leagueFilter }) {
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    if (leagueFilter.size === 0) return matches
    return matches.filter(m => leagueFilter.has(m.league_code))
  }, [matches, leagueFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize)

  // Reset to page 1 when filter changes
  useEffect(() => { setPage(1) }, [leagueFilter])

  if (filtered.length === 0) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyTitle}>NO MATCHES</p>
        <p className={styles.emptySub}>
          {section === 'live' && 'No matches in play right now.'}
          {section === 'upcoming' && 'No upcoming matches for your subscriptions.'}
          {section === 'finished' && "No results yet today."}
        </p>
      </div>
    )
  }

  return (
    <>
      <div className={styles.matchList}>
        {paged.map(m => <MatchRow key={m.external_id} match={m} section={section} />)}
      </div>
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </>
  )
}
