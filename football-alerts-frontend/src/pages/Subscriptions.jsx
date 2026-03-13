import { useEffect, useState } from 'react'
import {
  getSubscriptions, addSubscription, removeSubscription,
  getLeagues, getTeamsByLeague, getUpcomingMatches,
} from '../api/endpoints'
import Nav from '../components/Nav'
import Pagination from '../components/Pagination'
import styles from './Subscriptions.module.css'

const MATCH_PAGE_SIZE = 15

function formatKickoff(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
    + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

// Simple client-side paginator for short static lists (leagues, teams)
function usePaged(items, pageSize = 12) {
  const [page, setPage] = useState(1)
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize))
  const paged = items.slice((page - 1) * pageSize, page * pageSize)
  const reset = () => setPage(1)
  return { paged, page, setPage, totalPages, reset }
}

export default function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState([])
  const [leagues, setLeagues] = useState([])
  const [teams, setTeams] = useState([])
  const [matches, setMatches] = useState([])
  const [matchTotal, setMatchTotal] = useState(0)
  const [matchTotalPages, setMatchTotalPages] = useState(1)
  const [matchPage, setMatchPage] = useState(1)
  const [selectedLeague, setSelectedLeague] = useState(null)
  const [tab, setTab] = useState('leagues')
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [adding, setAdding] = useState(null)
  const [removing, setRemoving] = useState(null)
  const [error, setError] = useState('')

  // Active subscriptions pagination (client-side)
  const [subPage, setSubPage] = useState(1)
  const SUB_PAGE_SIZE = 10
  const subTotalPages = Math.max(1, Math.ceil(subscriptions.length / SUB_PAGE_SIZE))
  const pagedSubs = subscriptions.slice((subPage - 1) * SUB_PAGE_SIZE, subPage * SUB_PAGE_SIZE)

  // League + team pagination (client-side, lists are small)
  const leaguePager = usePaged(leagues, 12)
  const teamPager = usePaged(teams, 15)

  useEffect(() => {
    getSubscriptions().then(setSubscriptions)
    getLeagues().then(setLeagues)
  }, [])

  const loadTeams = async (league) => {
    setSelectedLeague(league)
    setTab('teams')
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

  const fetchMatches = async (page) => {
    setLoadingMatches(true)
    try {
      const params = new URLSearchParams({ page, page_size: MATCH_PAGE_SIZE })
      const data = await getUpcomingMatches(`?${params}`)
      setMatches(data.items)
      setMatchTotal(data.total)
      setMatchTotalPages(data.total_pages)
    } catch {
      setError('Failed to load matches')
    } finally {
      setLoadingMatches(false)
    }
  }

  const loadMatches = async () => {
    setTab('matches')
    if (matches.length === 0) await fetchMatches(1)
  }

  const handleMatchPage = async (p) => {
    setMatchPage(p)
    await fetchMatches(p)
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
      }
      // If removing last item on this sub page, go back one
      if (pagedSubs.length === 1 && subPage > 1) setSubPage(p => p - 1)
    } catch {
      setError('Failed to remove subscription')
    } finally {
      setRemoving(null)
    }
  }

  const getSubId = (type, externalId) =>
    subscriptions.find(s => s.subscription_type === type && s.external_id === String(externalId))?.id

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

        <div className={styles.layout}>

          {/* Left: Browse */}
          <div className={styles.browser}>
            <div className={styles.tabs}>
              <button
                className={`${styles.tab} ${tab === 'leagues' ? styles.tabActive : ''}`}
                onClick={() => setTab('leagues')}
              >
                LEAGUES
              </button>
              <button
                className={`${styles.tab} ${tab === 'matches' ? styles.tabActive : ''}`}
                onClick={loadMatches}
              >
                MATCHES
              </button>
            </div>

            {/* LEAGUES tab */}
            {tab === 'leagues' && (
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
            )}

            {/* TEAMS tab - shown when user clicks TEAMS on a league row */}
            {tab === 'teams' && (
              <>
                <div className={styles.teamsHeader}>
                  <button className={styles.backBtn} onClick={() => setTab('leagues')}>
                    BACK
                  </button>
                  <span className={styles.teamsLeagueName}>
                    {selectedLeague?.name.toUpperCase()} TEAMS
                  </span>
                </div>
                <div className={styles.list}>
                  {loadingTeams ? (
                    <p className={styles.loading}>Loading teams...</p>
                  ) : teamPager.paged.map(team => {
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

            {/* MATCHES tab */}
            {tab === 'matches' && (
              <>
                <div className={styles.list}>
                  {loadingMatches ? (
                    <p className={styles.loading}>Loading matches...</p>
                  ) : matches.map(match => {
                    const subscribed = isSubscribed('match', match.external_id)
                    const key = `match-${match.external_id}`
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
                            onClick={() => handleRemove(
                              getSubId('match', match.external_id),
                              subscriptions.find(s => s.subscription_type === 'match' && s.external_id === String(match.external_id))
                            )}
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
                {!loadingMatches && (
                  <Pagination page={matchPage} totalPages={matchTotalPages} onChange={handleMatchPage} />
                )}
              </>
            )}
          </div>

          {/* Right: Active subscriptions */}
          <div className={styles.active}>
            <p className={styles.activeLabel}>
              ACTIVE ALERTS
              {subscriptions.length > 0 && (
                <span className={styles.activeBadge}>{subscriptions.length}</span>
              )}
            </p>
            {subscriptions.length === 0 ? (
              <p className={styles.noSubs}>No alerts yet. Add leagues, teams, or matches.</p>
            ) : (
              <>
                <div className={styles.subList}>
                  {pagedSubs.map(sub => (
                    <div key={sub.id} className={styles.subItem}>
                      <div>
                        <span className={styles.subType}>{sub.subscription_type}</span>
                        <p className={styles.subName}>{sub.display_name}</p>
                      </div>
                      <button
                        className={styles.removeSm}
                        onClick={() => handleRemove(sub.id, sub)}
                        disabled={removing === sub.id}
                      >
                        {removing === sub.id ? '...' : 'X'}
                      </button>
                    </div>
                  ))}
                </div>
                <Pagination page={subPage} totalPages={subTotalPages} onChange={setSubPage} />
              </>
            )}
          </div>

        </div>
      </main>
    </div>
  )
}