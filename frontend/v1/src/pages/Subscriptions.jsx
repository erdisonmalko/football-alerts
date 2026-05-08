import { useEffect, useState, useMemo, useCallback } from 'react'
import {
  getSubscriptions, addSubscription, removeSubscription,
  getLeagues, getTeamsByLeague, getUpcomingMatches,
  getGoogleStatus, connectGoogle,
  addMatchToCalendar,removeMatchFromCalendar,
} from '../api/endpoints'
import Nav from '../components/Nav'
import CalendarSyncModal from '../components/CalendarSyncModal'
import Pagination from '../components/Pagination'
import FilterChips from '../components/FilterChips'
import styles from './Subscriptions.module.css'

const MATCH_PAGE_SIZE = 15

function formatKickoff(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
    + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

function usePaged(items, pageSize = 12) {
  const [page, setPage] = useState(1)
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize))
  const paged = items.slice((page - 1) * pageSize, page * pageSize)
  const reset = () => setPage(1)
  return { paged, page, setPage, totalPages, reset }
}

function LoadingBar() {
  return (
    <div className={styles.loadingWrap}>
      <div className={styles.loadingBar} />
    </div>
  )
}

const ALERT_TYPE_OPTIONS = [
  { value: 'league', label: 'LEAGUE' },
  { value: 'team', label: 'TEAM' },
  { value: 'match', label: 'MATCH' },
]

export default function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState([])
  const [leagues, setLeagues] = useState([])
  const [teams, setTeams] = useState([])
  const [matches, setMatches] = useState([])
  const [matchTotalPages, setMatchTotalPages] = useState(1)
  const [matchPage, setMatchPage] = useState(1)
  const [selectedLeague, setSelectedLeague] = useState(null)
  const [tab, setTab] = useState('upcoming')
  const [leagueView, setLeagueView] = useState('leagues')
  const [loadingInit, setLoadingInit] = useState(true)
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [adding, setAdding] = useState(null)
  const [removing, setRemoving] = useState(null)
  const [error, setError] = useState('')
  const [calendarSyncing, setCalendarSyncing] = useState(false)

  // Calendar modal state
  const [modalOpen, setModalOpen] = useState(false)
  const [modalConnected, setModalConnected] = useState(false)
  const [pendingMatchId, setPendingMatchId] = useState(null)
  const [googleModalError, setGoogleModalError] = useState('')

  // Filters
  const [upcomingLeagueFilter, setUpcomingLeagueFilter] = useState(new Set())
  const [activeTypeFilter, setActiveTypeFilter] = useState(new Set())

  const SUB_PAGE_SIZE = 10
  const [subPage, setSubPage] = useState(1)
  const leaguePager = usePaged(leagues, 12)
  const teamPager = usePaged(teams, 15)

  const fetchMatches = useCallback(async (page) => {
    setLoadingMatches(true)
    try {
      const params = new URLSearchParams({ page, page_size: MATCH_PAGE_SIZE })
      const data = await getUpcomingMatches(`?${params}`)
      setMatches(data.items)
      setMatchTotalPages(data.total_pages)
    } catch {
      setError('Failed to load matches')
    } finally {
      setLoadingMatches(false)
    }
  }, [])

  // On mount: load data + resume any pending calendar sync after OAuth redirect
  useEffect(() => {
    const init = async () => {
      try {
        const [subs, lgs] = await Promise.all([
          getSubscriptions(),
          getLeagues(),
          fetchMatches(1),
        ])
        setSubscriptions(subs)
        setLeagues(lgs)

        // Resume pending calendar sync after Google OAuth redirect
        const storedMatchId = localStorage.getItem('pending_match_id')
        if (storedMatchId) {
          localStorage.removeItem('pending_match_id')
          setPendingMatchId(storedMatchId)

          const status = await getGoogleStatus()
          setModalConnected(status.connected)

          if (status.connected) {
            const success = await attemptAddMatchToCalendar(storedMatchId)
            if (!success) {
              setModalOpen(true)
            }
          } else {
            setModalOpen(true)
          }
        }
      } catch {
        setModalConnected(false)
        setModalOpen(true)
      } finally {
        setLoadingInit(false)
      }
    }

    init()
  }, [fetchMatches])

  const filteredMatches = useMemo(() => {
    if (upcomingLeagueFilter.size === 0) return matches
    return matches.filter(m => upcomingLeagueFilter.has(m.league_code))
  }, [matches, upcomingLeagueFilter])

  const filteredSubs = useMemo(() => {
    if (activeTypeFilter.size === 0) return subscriptions
    return subscriptions.filter(s => activeTypeFilter.has(s.subscription_type))
  }, [subscriptions, activeTypeFilter])

  const upcomingLeagueOptions = useMemo(() =>
    leagues.map(lg => ({ value: lg.code, label: lg.name })), [leagues])

  const subTotalPages = Math.max(1, Math.ceil(filteredSubs.length / SUB_PAGE_SIZE))
  const pagedSubs = filteredSubs.slice((subPage - 1) * SUB_PAGE_SIZE, subPage * SUB_PAGE_SIZE)

  const handleTabChange = (newTab) => {
    setTab(newTab)
    setError('')
    if (newTab === 'leagues') setLeagueView('leagues')
  }

  const loadTeams = async (league) => {
    setSelectedLeague(league)
    setLeagueView('teams')
    teamPager.reset()
    setLoadingTeams(true)
    try {
      const data = await getTeamsByLeague(league.code)
      setTeams(data)
    } catch {
      setError('Failed to load teams')
    } finally {
      setLoadingTeams(false)
    }
  }

  const handleMatchPage = async (p) => {
    setMatchPage(p)
    await fetchMatches(p)
  }

  const attemptAddMatchToCalendar = async (matchId) => {
    if (!matchId) return false
    try {
      await addMatchToCalendar(matchId)
      setGoogleModalError('')
      return true
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail
      if (status === 401 && detail === 'GOOGLE_TOKEN_EXPIRED') {
        setModalConnected(false)
        setGoogleModalError('Your Google connection has expired. Please reconnect.')
        return false
      }
      setError(detail || 'Failed to add match to calendar')
      return false
    }
  }

  const isSubscribed = (type, externalId) =>
    subscriptions.some(s => s.subscription_type === type && s.external_id === String(externalId))

  const handleAdd = async (type, externalId, displayName) => {
    const key = `${type}-${externalId}`
    setAdding(key)
    setError('')
    try {
      const sub = await addSubscription(type, String(externalId), displayName)
      setSubscriptions(s => [...s, sub])

      if (type === 'match') {
        setMatches(ms => ms.map(m =>
          String(m.external_id) === String(externalId) ? { ...m, is_subscribed: true } : m
        ))

        // Check Google status and show modal
        const status = await getGoogleStatus()
        setPendingMatchId(externalId)
        setModalConnected(status.connected)
        setGoogleModalError('')
        setModalOpen(true)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add subscription')
    } finally {
      setAdding(null)
    }
  }

  const handleRemove = async (subId, sub) => {
    setRemoving(subId)
    try {
      await removeSubscription(subId)
      setSubscriptions(s => s.filter(x => x.id !== subId))

      if (sub?.subscription_type === 'match') {
        setMatches(ms => ms.map(m =>
          String(m.external_id) === sub.external_id ? { ...m, is_subscribed: false } : m
        ))
        // Remove from Google Calendar silently — don't block on failure
        try {
          await removeMatchFromCalendar(sub.external_id)
        } catch {
          // Silent — calendar removal is best-effort
        }
      }

      if (pagedSubs.length === 1 && subPage > 1) setSubPage(p => p - 1)
    } catch {
      setError('Failed to remove subscription')
    } finally {
      setRemoving(null)
    }
  }

  const handleModalConnect = () => {
    // Store pending match so we can resume after OAuth redirect
    if (pendingMatchId) localStorage.setItem('pending_match_id', pendingMatchId)
    connectGoogle()
  }

  const handleModalConfirm = async () => {
    if (!pendingMatchId) return
    setCalendarSyncing(true)
    const success = await attemptAddMatchToCalendar(pendingMatchId)
    setCalendarSyncing(false)

    if (success) {
      setModalOpen(false)
      setPendingMatchId(null)
    }
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setPendingMatchId(null)
  }

  const getSubId = (type, externalId) =>
    subscriptions.find(s => s.subscription_type === type && s.external_id === String(externalId))?.id

  const TABS = [
    { key: 'upcoming', label: 'UPCOMING MATCHES' },
    { key: 'leagues', label: 'LEAGUES & TEAMS' },
    { key: 'active', label: 'YOUR ACTIVE ALERTS', count: subscriptions.length },
  ]

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>

        <div className={styles.header}>
          <div>
            <p className={styles.label}>CONFIGURATION</p>
            <h1 className={styles.title}>ALERT SETUP</h1>
          </div>
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <CalendarSyncModal
          isOpen={modalOpen}
          isConnected={modalConnected}
          syncing={calendarSyncing}
          errorMessage={googleModalError}
          onClose={handleModalClose}
          onConnect={handleModalConnect}
          onConfirm={handleModalConfirm}
        />

        {loadingInit ? (
          <LoadingBar />
        ) : (
          <>
            <div className={styles.tabs}>
              {TABS.map(t => (
                <button
                  key={t.key}
                  className={`${styles.tab} ${tab === t.key ? styles.tabActive : ''}`}
                  onClick={() => handleTabChange(t.key)}
                >
                  {t.label}
                  {t.count > 0 && (
                    <span className={`${styles.tabBadge} ${tab === t.key ? styles.tabBadgeActive : ''}`}>
                      {t.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* UPCOMING tab */}
            {tab === 'upcoming' && (
              <div className={styles.panel}>
                <FilterChips
                  label="FILTER BY LEAGUE"
                  options={upcomingLeagueOptions}
                  selected={upcomingLeagueFilter}
                  onChange={(next) => { setUpcomingLeagueFilter(next); setMatchPage(1) }}
                />
                {loadingMatches ? <LoadingBar /> : filteredMatches.length === 0 ? (
                  <p className={styles.empty}>No matches found.</p>
                ) : (
                  <>
                    <div className={styles.list}>
                      {filteredMatches.map(match => {
                        const subscribed = isSubscribed('match', match.external_id)
                        const key = `match-${match.external_id}`
                        const subRecord = subscriptions.find(
                          s => s.subscription_type === 'match' && s.external_id === String(match.external_id)
                        )
                        return (
                          <div key={match.external_id} className={styles.item}>
                            <div className={styles.itemInfo}>
                              <p className={styles.itemName}>
                                {match.home_team_name} vs {match.away_team_name}
                              </p>
                              <p className={styles.itemMeta}>
                                {match.league_code} — {formatKickoff(match.kickoff_utc)}
                              </p>
                            </div>
                            {subscribed ? (
                              <button
                                className={styles.removeBtn}
                                onClick={() => handleRemove(getSubId('match', match.external_id), subRecord)}
                                disabled={removing === getSubId('match', match.external_id)}
                              >
                                {removing === getSubId('match', match.external_id) ? '...' : 'REMOVE'}
                              </button>
                            ) : (
                              <button
                                className={styles.addBtn}
                                onClick={() => handleAdd('match', match.external_id, `${match.home_team_name} vs ${match.away_team_name}`)}
                                disabled={adding === key}
                              >
                                {adding === key ? '...' : '+ ALERT'}
                              </button>
                            )}
                          </div>
                        )
                      })}
                    </div>
                    {upcomingLeagueFilter.size === 0 && (
                      <Pagination page={matchPage} totalPages={matchTotalPages} onChange={handleMatchPage} />
                    )}
                  </>
                )}
              </div>
            )}

            {/* LEAGUES tab */}
            {tab === 'leagues' && (
              <div className={styles.panel}>
                {leagueView === 'leagues' ? (
                  <>
                    <div className={styles.list}>
                      {leaguePager.paged.map(lg => {
                        const subscribed = isSubscribed('league', lg.code)
                        const key = `league-${lg.code}`
                        return (
                          <div key={lg.code} className={styles.item}>
                            <div className={styles.itemInfo}>
                              <p className={styles.itemName}>{lg.name}</p>
                              <p className={styles.itemMeta}>{lg.country} — {lg.code}</p>
                            </div>
                            <div className={styles.itemActions}>
                              <button className={styles.browseBtn} onClick={() => loadTeams(lg)}>
                                TEAMS
                              </button>
                              {subscribed ? (
                                <button
                                  className={styles.removeBtn}
                                  onClick={() => handleRemove(getSubId('league', lg.code))}
                                  disabled={removing === getSubId('league', lg.code)}
                                >
                                  {removing === getSubId('league', lg.code) ? '...' : 'REMOVE'}
                                </button>
                              ) : (
                                <button
                                  className={styles.addBtn}
                                  onClick={() => handleAdd('league', lg.code, lg.name)}
                                  disabled={adding === key}
                                >
                                  {adding === key ? '...' : '+ ALERT'}
                                </button>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                    <Pagination page={leaguePager.page} totalPages={leaguePager.totalPages} onChange={leaguePager.setPage} />
                  </>
                ) : (
                  <>
                    <div className={styles.subViewHeader}>
                      <button className={styles.backBtn} onClick={() => setLeagueView('leagues')}>
                        ← BACK
                      </button>
                      <span className={styles.subViewTitle}>
                        {selectedLeague?.name.toUpperCase()} — TEAMS
                      </span>
                    </div>
                    <div className={styles.list}>
                      {loadingTeams ? <LoadingBar /> : teamPager.paged.map(team => {
                        const subscribed = isSubscribed('team', team.id)
                        const key = `team-${team.id}`
                        return (
                          <div key={team.id} className={styles.item}>
                            <div className={styles.itemInfo}>
                              <p className={styles.itemName}>{team.name}</p>
                              {team.short_name && <p className={styles.itemMeta}>{team.short_name}</p>}
                            </div>
                            {subscribed ? (
                              <button
                                className={styles.removeBtn}
                                onClick={() => handleRemove(getSubId('team', team.id))}
                                disabled={removing === getSubId('team', team.id)}
                              >
                                {removing === getSubId('team', team.id) ? '...' : 'REMOVE'}
                              </button>
                            ) : (
                              <button
                                className={styles.addBtn}
                                onClick={() => handleAdd('team', team.id, team.name)}
                                disabled={adding === key}
                              >
                                {adding === key ? '...' : '+ ALERT'}
                              </button>
                            )}
                          </div>
                        )
                      })}
                    </div>
                    {!loadingTeams && (
                      <Pagination page={teamPager.page} totalPages={teamPager.totalPages} onChange={teamPager.setPage} />
                    )}
                  </>
                )}
              </div>
            )}

            {/* ACTIVE ALERTS tab */}
            {tab === 'active' && (
              <div className={styles.panel}>
                <FilterChips
                  label="FILTER BY TYPE"
                  options={ALERT_TYPE_OPTIONS}
                  selected={activeTypeFilter}
                  onChange={(next) => { setActiveTypeFilter(next); setSubPage(1) }}
                  color="neutral"
                />
                {filteredSubs.length === 0 ? (
                  <p className={styles.empty}>
                    {subscriptions.length === 0
                      ? 'No alerts yet. Add leagues, teams, or matches.'
                      : 'No alerts match the selected filter.'}
                  </p>
                ) : (
                  <>
                    <div className={styles.list}>
                      {pagedSubs.map(sub => (
                        <div key={sub.id} className={styles.item}>
                          <div className={styles.itemInfo}>
                            <span className={styles.subType}>{sub.subscription_type}</span>
                            <p className={styles.itemName}>{sub.display_name}</p>
                          </div>
                          <button
                            className={styles.removeBtn}
                            onClick={() => handleRemove(sub.id, sub)}
                            disabled={removing === sub.id}
                          >
                            {removing === sub.id ? '...' : 'REMOVE'}
                          </button>
                        </div>
                      ))}
                    </div>
                    <Pagination page={subPage} totalPages={subTotalPages} onChange={setSubPage} />
                  </>
                )}
              </div>
            )}
          </>
        )}

      </main>
    </div>
  )
}