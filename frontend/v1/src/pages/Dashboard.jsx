import { useEffect, useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import FilterChips from '../components/FilterChips'
import TabContent from '../components/TabContent'
import ServersList from '../components/ServersList'
import ServerDetail from '../components/ServerDetail'
import styles from './Dashboard.module.css'
import { getMyMatches, getMyServers, getServer, getServerLeaderboard, getServerChallenges } from '../api/endpoints'

const REFRESH_INTERVAL = 15 * 60 * 1000
const PAGE_SIZES = { live: 5, upcoming: 20, finished: 10 }


export default function Dashboard() {
  const { user } = useAuth()
  const [matches, setMatches] = useState({ live: [], upcoming: [], finished: [] })
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [tab, setTab] = useState('live')
  const [leagueFilter, setLeagueFilter] = useState(new Set())
  
  // Server state
  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState(null)
  const [serverDetails, setServerDetails] = useState(null)
  const [leaderboard, setLeaderboard] = useState(null)
  const [challenges, setChallenges] = useState([])
  const [serversLoading, setServersLoading] = useState(false)

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

  const fetchServers = useCallback(async () => {
    setServersLoading(true)
    try {
      const data = await getMyServers()
      setServers(data)
    } catch (err) {
      console.error('Failed to fetch servers:', err)
    } finally {
      setServersLoading(false)
    }
  }, [])

  const fetchServerDetails = useCallback(async (serverId) => {
    try {
      const [details, leader, chal] = await Promise.all([
        getServer(serverId),
        getServerLeaderboard(serverId),
        getServerChallenges(serverId),
      ])
      setServerDetails(details)
      setLeaderboard(leader)
      setChallenges(chal || [])
      setSelectedServer(serverId)
    } catch (err) {
      console.error('Failed to fetch server details:', err)
    }
  }, [])

  useEffect(() => {
    fetchMatches()
    const interval = setInterval(fetchMatches, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchMatches])

  // Fetch servers when tab changes to servers
  useEffect(() => {
    if (tab === 'servers') {
      fetchServers()
    }
  }, [tab, fetchServers])

  // Build dynamic league options from all matches combined
  const leagueOptions = useMemo(() => {
    const all = [...matches.live, ...matches.upcoming, ...matches.finished]
    const codes = [...new Set(all.map(m => m.league_code))].sort()
    return codes.map(code => ({ value: code, label: code }))
  }, [matches])

  const name = user?.full_name?.split(' ')[0] || 'Fan'
  const hasAny = matches.live.length + matches.upcoming.length + matches.finished.length > 0

  const TABS = [
    { key: 'live', label: 'LIVE', count: matches.live.length, live: true },
    { key: 'upcoming', label: 'UPCOMING', count: matches.upcoming.length },
    { key: 'finished', label: "TODAY'S RESULTS", count: matches.finished.length },
    { key: 'servers', label: 'SERVERS', count: servers.length },
  ]

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
            <Link to="/subscriptions" className={styles.manageBtn}>MANAGE ALERTS</Link>
          </div>
        </div>

        {loading ? (
          <div className={styles.loading}><div className={styles.loadingBar} /></div>
        ) : !hasAny && tab !== 'servers' ? (
          <div className={styles.empty}>
            <p className={styles.emptyTitle}>NO MATCHES YET</p>
            <p className={styles.emptySub}>Subscribe to leagues or teams to see your matches here.</p>
            <Link to="/subscriptions" className={styles.manageBtn}>SET UP ALERTS</Link>
          </div>
        ) : (
          <>
            <div className={styles.tabs}>
              {TABS.map(t => (
                <button
                  key={t.key}
                  className={`${styles.tab} ${tab === t.key ? styles.tabActive : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  {t.live && t.count > 0 && <span className={styles.liveIndicator}>●</span>}
                  {t.label}
                  {t.count > 0 && (
                    <span className={`${styles.tabBadge} ${tab === t.key ? styles.tabBadgeActive : ''}`}>
                      {t.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {tab === 'servers' ? (
              selectedServer && serverDetails ? (
                <ServerDetail
                  serverDetails={serverDetails}
                  leaderboard={leaderboard}
                  challenges={challenges}
                  onBack={() => setSelectedServer(null)}
                />
              ) : (
                <ServersList
                  servers={servers}
                  loading={serversLoading}
                  onSelectServer={fetchServerDetails}
                />
              )
            ) : (
              <>
                <FilterChips
                  label="FILTER BY LEAGUE"
                  options={leagueOptions}
                  selected={leagueFilter}
                  onChange={setLeagueFilter}
                />

                <TabContent
                  matches={matches[tab]}
                  section={tab}
                  pageSize={PAGE_SIZES[tab]}
                  leagueFilter={leagueFilter}
                />
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}