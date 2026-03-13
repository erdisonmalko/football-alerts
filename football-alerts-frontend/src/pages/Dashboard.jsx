import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getUpcomingMatches, addSubscription, removeSubscription, getSubscriptions } from '../api/endpoints'
import Nav from '../components/Nav'
import Pagination from '../components/Pagination'
import styles from './Dashboard.module.css'

const LEAGUES = [
  { code: null,  name: 'ALL' },
  { code: 'PL',  name: 'PL' },
  { code: 'PD',  name: 'LA LIGA' },
  { code: 'SA',  name: 'SERIE A' },
  { code: 'BL1', name: 'BUNDESLIGA' },
  { code: 'FL1', name: 'LIGUE 1' },
  { code: 'CL',  name: 'UCL' },
  { code: 'EL',  name: 'UEL' },
]

const PAGE_SIZE = 20

function formatKickoff(dateStr) {
  const d = new Date(dateStr)
  return {
    date: d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }),
    time: d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) + ' UTC',
  }
}

function timeUntil(dateStr) {
  const diff = new Date(dateStr) - new Date()
  if (diff < 0) return null
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  if (days >= 7) return `${days}d`
  if (days > 0)  return `${days}d ${hours}h`
  return `${hours}h`
}

export default function Dashboard() {
  const { user } = useAuth()
  const [matches, setMatches] = useState([])
  const [subscriptions, setSubscriptions] = useState([])
  const [league, setLeague] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)

  const fetchMatches = async (leagueCode, pageNum) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: pageNum, page_size: PAGE_SIZE })
      if (leagueCode) params.set('league_code', leagueCode)
      const data = await getUpcomingMatches(`?${params}`)
      setMatches(data.items)
      setTotalPages(data.total_pages)
      setTotal(data.total)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMatches(null, 1)
    getSubscriptions().then(setSubscriptions)
  }, [])

  const handleLeague = (code) => {
    setLeague(code)
    setPage(1)
    fetchMatches(code, 1)
  }

  const handlePage = (p) => {
    setPage(p)
    fetchMatches(league, p)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const getMatchSubId = (externalId) =>
    subscriptions.find(s => s.subscription_type === 'match' && s.external_id === String(externalId))?.id

  const handleToggle = async (match) => {
    const key = match.external_id
    setActing(key)
    try {
      if (match.is_subscribed) {
        const subId = getMatchSubId(match.external_id)
        if (subId) {
          await removeSubscription(subId)
          setSubscriptions(s => s.filter(x => x.id !== subId))
        }
      } else {
        const displayName = `${match.home_team_name} vs ${match.away_team_name}`
        const sub = await addSubscription('match', String(match.external_id), displayName)
        setSubscriptions(s => [...s, sub])
      }
      setMatches(ms => ms.map(m =>
        m.external_id === key ? { ...m, is_subscribed: !m.is_subscribed } : m
      ))
    } finally {
      setActing(null)
    }
  }

  const name = user?.full_name?.split(' ')[0] || 'Fan'

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>

        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>WELCOME BACK, {name.toUpperCase()}</p>
            <h1 className={styles.title}>UPCOMING MATCHES</h1>
          </div>
          <Link to="/subscriptions" className={styles.manageBtn}>
            MANAGE ALERTS
          </Link>
        </div>

        {/* League filter */}
        <div className={styles.filters}>
          {LEAGUES.map(lg => (
            <button
              key={lg.code ?? 'all'}
              className={`${styles.filterBtn} ${league === lg.code ? styles.filterActive : ''}`}
              onClick={() => handleLeague(lg.code)}
            >
              {lg.name}
            </button>
          ))}
        </div>

        {/* Results count */}
        {!loading && total > 0 && (
          <p className={styles.resultsCount}>
            {total} MATCHES — PAGE {page} OF {totalPages}
          </p>
        )}

        {loading ? (
          <div className={styles.loading}>
            <div className={styles.loadingBar} />
          </div>
        ) : matches.length === 0 ? (
          <div className={styles.empty}>
            <p className={styles.emptyTitle}>NO MATCHES FOUND</p>
            <p className={styles.emptySub}>Try a different league or run a match sync from admin.</p>
          </div>
        ) : (
          <>
            <div className={styles.matchList}>
              {matches.map(match => {
                const { date, time } = formatKickoff(match.kickoff_utc)
                const countdown = timeUntil(match.kickoff_utc)
                const subscribed = match.is_subscribed
                const busy = acting === match.external_id

                return (
                  <div key={match.external_id} className={`${styles.matchRow} ${subscribed ? styles.matchRowAlerted : ''}`}>
                    <div className={styles.matchLeague}>
                      <span className={styles.leagueCode}>{match.league_code}</span>
                      {match.matchday && <span className={styles.matchday}>MD{match.matchday}</span>}
                    </div>

                    <div className={styles.matchTeams}>
                      <span className={styles.teamName}>{match.home_team_name}</span>
                      <span className={styles.vs}>VS</span>
                      <span className={styles.teamName}>{match.away_team_name}</span>
                    </div>

                    <div className={styles.matchTime}>
                      <span className={styles.kickoffDate}>{date}</span>
                      <span className={styles.kickoffTime}>{time}</span>
                    </div>

                    <div className={styles.matchActions}>
                      {countdown && <span className={styles.countdown}>{countdown}</span>}
                      <button
                        className={`${styles.alertBtn} ${subscribed ? styles.alertBtnActive : ''}`}
                        onClick={() => handleToggle(match)}
                        disabled={busy}
                      >
                        {busy ? '...' : subscribed ? 'ALERTED' : '+ ALERT'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            <Pagination page={page} totalPages={totalPages} onChange={handlePage} />
          </>
        )}

      </main>
    </div>
  )
}