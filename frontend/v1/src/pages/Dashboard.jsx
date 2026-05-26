import { useEffect, useState, useCallback, useMemo } from 'react'
import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import FilterChips from '../components/FilterChips'
import TabContent from '../components/TabContent'
import styles from './Dashboard.module.css'
import { getMyMatchesPaged } from '../api/endpoints'

const REFRESH_INTERVAL = 15 * 60 * 1000
const PAGE_SIZES = { live: 5, upcoming: 20, finished: 10 }

const TABS = [
  { key: 'live', label: 'LIVE', live: true },
  { key: 'upcoming', label: 'UPCOMING' },
  { key: 'finished', label: "TODAY'S RESULTS" },
]

export default function Dashboard() {
  const { user } = useAuth()
  const [matches, setMatches] = useState([])
  const [counts, setCounts] = useState({ live: 0, upcoming: 0, finished: 0 })
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [tab, setTab] = useState('live')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [leagueFilter, setLeagueFilter] = useState(new Set())

  const fetchMatches = useCallback(async (section = 'live', pageNumber = 1) => {
    setLoading(true)
    try {
      const data = await getMyMatchesPaged({ section, page: pageNumber, pageSize: PAGE_SIZES[section] })
      setMatches(data.items)
      setCounts({
        live: data.live_count,
        upcoming: data.upcoming_count,
        finished: data.finished_count,
      })
      setTotalPages(data.total_pages)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch matches:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMatches(tab, page)
    const interval = setInterval(() => fetchMatches(tab, page), REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchMatches, tab, page])

  const leagueOptions = useMemo(() => {
    const codes = [...new Set(matches.map(m => m.league_code))].sort()
    return codes.map(code => ({ value: code, label: code }))
  }, [matches])

  const name = user?.full_name?.split(' ')[0] || 'Fan'

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>WELCOME BACK, {name.toUpperCase()}</p>
            <h1 className={styles.title}>MY MATCHES</h1>
          </div>
          {lastUpdated && (
            <span className={styles.lastUpdated}>
              Updated {lastUpdated.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>

        {loading ? (
          <div className={styles.loading}><div className={styles.loadingBar} /></div>
        ) : (
          <>
            <div className={styles.tabs}>
              {TABS.map(t => {
                const count = counts[t.key] ?? 0
                return (
                  <button
                    key={t.key}
                    className={`${styles.tab} ${tab === t.key ? styles.tabActive : ''}`}
                    onClick={() => { setTab(t.key); setPage(1) }}
                  >
                    {t.live && count > 0 && <span className={styles.liveIndicator}>●</span>}
                    {t.label}
                    {count > 0 && (
                      <span className={`${styles.tabBadge} ${tab === t.key ? styles.tabBadgeActive : ''}`}>
                        {count}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            <FilterChips
              label="FILTER BY LEAGUE"
              options={leagueOptions}
              selected={leagueFilter}
              onChange={setLeagueFilter}
            />

            <TabContent
              matches={matches}
              section={tab}
              pageSize={PAGE_SIZES[tab]}
              leagueFilter={leagueFilter}
              currentPage={page}
              totalPages={totalPages}
              onPageChange={(next) => setPage(next)}
              serverPaging
            />
          </>
        )}
      </main>
    </div>
  )
}