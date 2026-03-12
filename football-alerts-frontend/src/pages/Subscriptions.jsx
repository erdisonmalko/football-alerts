import { useEffect, useState } from 'react'
import {
  getSubscriptions, addSubscription, removeSubscription,
  getLeagues, getTeamsByLeague,
} from '../api/endpoints'
import Nav from '../components/Nav'
import styles from './Subscriptions.module.css'

export default function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState([])
  const [leagues, setLeagues] = useState([])
  const [teams, setTeams] = useState([])
  const [selectedLeague, setSelectedLeague] = useState(null)
  const [tab, setTab] = useState('leagues') // 'leagues' | 'teams'
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [adding, setAdding] = useState(null) // id of item being added
  const [removing, setRemoving] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getSubscriptions().then(setSubscriptions)
    getLeagues().then(setLeagues)
  }, [])

  const loadTeams = async (league) => {
    setSelectedLeague(league)
    setTab('teams')
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

  const isSubscribed = (type, externalId) =>
    subscriptions.some(s => s.subscription_type === type && s.external_id === String(externalId))

  const handleAdd = async (type, externalId, displayName) => {
    const key = `${type}-${externalId}`
    setAdding(key)
    setError('')
    try {
      const sub = await addSubscription(type, String(externalId), displayName)
      setSubscriptions(s => [...s, sub])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add subscription')
    } finally {
      setAdding(null)
    }
  }

  const handleRemove = async (subId) => {
    setRemoving(subId)
    try {
      await removeSubscription(subId)
      setSubscriptions(s => s.filter(x => x.id !== subId))
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
                className={`${styles.tab} ${tab === 'teams' ? styles.tabActive : ''}`}
                onClick={() => setTab('teams')}
                disabled={!selectedLeague}
              >
                {selectedLeague ? `${selectedLeague.name.toUpperCase()} TEAMS` : 'TEAMS'}
              </button>
            </div>

            {tab === 'leagues' && (
              <div className={styles.list}>
                {leagues.map(lg => {
                  const subscribed = isSubscribed('league', lg.code)
                  const key = `league-${lg.code}`
                  return (
                    <div key={lg.code} className={styles.item}>
                      <div className={styles.itemInfo}>
                        <p className={styles.itemName}>{lg.name}</p>
                        <p className={styles.itemMeta}>{lg.country} — {lg.code}</p>
                      </div>
                      <div className={styles.itemActions}>
                        <button
                          className={styles.browseBtn}
                          onClick={() => loadTeams(lg)}
                        >
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
            )}

            {tab === 'teams' && (
              <div className={styles.list}>
                {loadingTeams ? (
                  <p className={styles.loading}>Loading teams...</p>
                ) : teams.map(team => {
                  const subscribed = isSubscribed('team', team.id)
                  const key = `team-${team.id}`
                  return (
                    <div key={team.id} className={styles.item}>
                      <div className={styles.itemInfo}>
                        <p className={styles.itemName}>{team.name}</p>
                        {team.short_name && (
                          <p className={styles.itemMeta}>{team.short_name}</p>
                        )}
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
            )}
          </div>

          {/* Right: Active subscriptions */}
          <div className={styles.active}>
            <p className={styles.activeLabel}>ACTIVE ALERTS</p>
            {subscriptions.length === 0 ? (
              <p className={styles.noSubs}>No alerts yet. Add leagues or teams from the left.</p>
            ) : (
              <div className={styles.subList}>
                {subscriptions.map(sub => (
                  <div key={sub.id} className={styles.subItem}>
                    <div>
                      <span className={styles.subType}>{sub.subscription_type}</span>
                      <p className={styles.subName}>{sub.display_name}</p>
                    </div>
                    <button
                      className={styles.removeSm}
                      onClick={() => handleRemove(sub.id)}
                      disabled={removing === sub.id}
                    >
                      {removing === sub.id ? '...' : 'X'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  )
}
