import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import Nav from '../components/Nav'
import styles from './Dashboard.module.css'
import { getMyMatches } from '../api/endpoints'

const REFRESH_INTERVAL = 15 * 60 * 1000 // 15 minutes

function formatKickoff(dateStr) {
  const d = new Date(dateStr)
  return {
    date: d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }),
    time: d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) + ' UTC',
  }
}

function timeUntil(dateStr) {
  const diff = new Date(dateStr) - new Date()
  if (diff <= 0) return null
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  const mins = Math.floor((diff % 3600000) / 60000)
  if (days >= 7) return `${days}d`
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h`
  return `${mins}m`
}

function MatchRow({ match, section }) {
  const { date, time } = formatKickoff(match.kickoff_utc)
  const isLive = section === 'live'
  const isFinished = section === 'finished'

  return (
    <div className={`${styles.matchRow} ${isLive ? styles.matchRowLive : ''} ${isFinished ? styles.matchRowFinished : ''}`}>
      <div className={styles.matchLeague}>
        <span className={styles.leagueCode}>{match.league_code}</span>
        {match.matchday && <span className={styles.matchday}>MD{match.matchday}</span>}
      </div>

      <div className={styles.matchTeams}>
        <span className={styles.teamName}>{match.home_team_name}</span>

        {(isLive || isFinished) && match.home_score !== null ? (
          <span className={styles.score}>
            {match.home_score} — {match.away_score}
          </span>
        ) : (
          <span className={styles.vs}>VS</span>
        )}

        <span className={styles.teamName}>{match.away_team_name}</span>
      </div>

      <div className={styles.matchMeta}>
        {isLive ? (
          <span className={styles.liveBadge}>● LIVE</span>
        ) : isFinished ? (
          <span className={styles.finishedBadge}>FINISHED</span>
        ) : (
          <>
            <span className={styles.kickoffDate}>{date}</span>
            <span className={styles.kickoffTime}>{time}</span>
          </>
        )}
        {!isLive && !isFinished && timeUntil(match.kickoff_utc) && (
          <span className={styles.countdown}>{timeUntil(match.kickoff_utc)}</span>
        )}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [matches, setMatches] = useState({ live: [], upcoming: [], finished: [] })
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchMatches = useCallback(async () => {
    try {
      const data = await getMyMatches()
      setMatches(data)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch matches:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMatches()
    const interval = setInterval(fetchMatches, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchMatches])

  const name = user?.full_name?.split(' ')[0] || 'Fan'
  const hasAny = matches.live.length + matches.upcoming.length + matches.finished.length > 0

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>

        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>WELCOME BACK, {name.toUpperCase()}</p>
            <h1 className={styles.title}>MY MATCHES</h1>
          </div>
          <div className={styles.headerRight}>
            {lastUpdated && (
              <span className={styles.lastUpdated}>
                Updated {lastUpdated.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
            <Link to="/subscriptions" className={styles.manageBtn}>
              MANAGE ALERTS
            </Link>
          </div>
        </div>

        {loading ? (
          <div className={styles.loading}>
            <div className={styles.loadingBar} />
          </div>
        ) : !hasAny ? (
          <div className={styles.empty}>
            <p className={styles.emptyTitle}>NO MATCHES YET</p>
            <p className={styles.emptySub}>
              Subscribe to leagues or teams to see your matches here.
            </p>
            <Link to="/subscriptions" className={styles.manageBtn}>
              SET UP ALERTS
            </Link>
          </div>
        ) : (
          <>
            {matches.live.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.liveIndicator}>●</span> LIVE NOW
                </h2>
                <div className={styles.matchList}>
                  {matches.live.map(m => (
                    <MatchRow key={m.external_id} match={m} section="live" />
                  ))}
                </div>
              </section>
            )}

            {matches.upcoming.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>UPCOMING</h2>
                <div className={styles.matchList}>
                  {matches.upcoming.map(m => (
                    <MatchRow key={m.external_id} match={m} section="upcoming" />
                  ))}
                </div>
              </section>
            )}

            {matches.finished.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>TODAY'S RESULTS</h2>
                <div className={styles.matchList}>
                  {matches.finished.map(m => (
                    <MatchRow key={m.external_id} match={m} section="finished" />
                  ))}
                </div>
              </section>
            )}
          </>
        )}

      </main>
    </div>
  )
}