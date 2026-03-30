import { useEffect, useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import FilterChips from '../components/FilterChips'
import TabContent from '../components/TabContent'
import ServersList from '../components/ServersList'
import ServerDetail from '../components/ServerDetail'
import ServerCreateModal from '../components/ServerCreateModal'
import styles from './Dashboard.module.css'
import { getMyMatches, getMyServers, createServer, getServer, getServerLeaderboard, getServerChallenges } from '../api/endpoints'

const REFRESH_INTERVAL = 15 * 60 * 1000
const PAGE_SIZES = { live: 5, upcoming: 20, finished: 10 }

export default function Dashboard() {
  const { user } = useAuth()
  
  // Matches state
  const [matches, setMatches] = useState({ live: [], upcoming: [], finished: [] })
  const [matchesLoading, setMatchesLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [leagueFilter, setLeagueFilter] = useState(new Set())
  
  // Server state
  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState(null)
  const [serverDetails, setServerDetails] = useState(null)
  const [leaderboard, setLeaderboard] = useState(null)
  const [challenges, setChallenges] = useState([])
  const [serversLoading, setServersLoading] = useState(false)
  
  // Tab state - Servers is default
  const [tab, setTab] = useState('servers')
  
  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creatingServer, setCreatingServer] = useState(false)

  const fetchMatches = useCallback(async () => {
    try {
      const data = await getMyMatches()
      setMatches(data)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch matches:', err)
    } finally {
      setMatchesLoading(false)
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

  const handleCreateServer = useCallback(async (name, isPublic) => {
    setCreatingServer(true)
    try {
      const newServer = await createServer(name, isPublic)
      setServers((prev) => [newServer, ...prev])
      setShowCreateModal(false)
    } catch (err) {
      console.error('Failed to create server:', err)
      throw err
    } finally {
      setCreatingServer(false)
    }
  }, [])

  // Fetch matches on mount
  useEffect(() => {
    fetchMatches()
    const interval = setInterval(fetchMatches, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchMatches])

  // Fetch servers when needed
  useEffect(() => {
    if (tab === 'servers') {
      fetchServers()
    }
  }, [tab, fetchServers])

  // Build dynamic league options from all matches
  const leagueOptions = useMemo(() => {
    const all = [...matches.live, ...matches.upcoming, ...matches.finished]
    const codes = [...new Set(all.map(m => m.league_code))].sort()
    return codes.map(code => ({ value: code, label: code }))
  }, [matches])

  const name = user?.full_name?.split(' ')[0] || 'Fan'
  const hasAnyMatches = matches.live.length + matches.upcoming.length + matches.finished.length > 0

  const TABS = [
    { key: 'servers', label: 'SERVERS', count: servers.length },
    { key: 'live', label: 'LIVE', count: matches.live.length, live: true },
    { key: 'upcoming', label: 'UPCOMING', count: matches.upcoming.length },
    { key: 'finished', label: "TODAY'S RESULTS", count: matches.finished.length },
  ]

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>WELCOME BACK, {name.toUpperCase()}</p>
            <h1 className={styles.title}>SERVERS & CHALLENGES</h1>
          </div>
          {tab === 'servers' && (
            <button
              className={styles.createServerBtn}
              onClick={() => setShowCreateModal(true)}
            >
              + CREATE SERVER
            </button>
          )}
        </div>

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

        {showCreateModal && (
          <ServerCreateModal
            onClose={() => setShowCreateModal(false)}
            onCreate={handleCreateServer}
            isLoading={creatingServer}
          />
        )}
      </main>
    </div>
  )
}