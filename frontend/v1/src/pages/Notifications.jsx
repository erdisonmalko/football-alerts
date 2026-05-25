import { useEffect, useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import Pagination from '../components/Pagination'
import * as bellStyles from '../components/NotificationBell.module.css'
import styles from './Notifications.module.css'
import {
  getMyServers,
  getChallengeFeed,
  getJoinRequests,
  handleJoinRequest,
  acceptChallenge,
  declineChallenge,
} from '../api/endpoints'
import { parseApiError } from '../api/errorHandler'

const ITEMS_PER_PAGE = 6

export default function Notifications() {
  const { user } = useAuth()
  const [joinRequests, setJoinRequests] = useState([])
  const [incomingChallenges, setIncomingChallenges] = useState([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)
  const [prediction, setPrediction] = useState({})
  const [challengeError, setChallengeError] = useState({})
  const [responded, setResponded] = useState({})
  const [page, setPage] = useState(1)

  const name = user?.full_name?.split(' ')[0] || 'Fan'

  const fetchNotifications = useCallback(async () => {
    setLoading(true)
    try {
      const [servers, feedData] = await Promise.all([
        getMyServers(),
        getChallengeFeed(),
      ])

      const serverList = Array.isArray(servers) ? servers : servers?.items || []
      const ownedServers = serverList.filter(s => s.is_owner === true)
      const nestedRequests = await Promise.all(
        ownedServers.map(async (server) => {
          try {
            const reqs = await getJoinRequests(server.id)
            return reqs.map(req => ({ serverId: server.id, serverName: server.name, request: req }))
          } catch {
            return []
          }
        })
      )

      setJoinRequests(nestedRequests.flat())
      setIncomingChallenges(feedData.incoming || [])
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  const handleJoinAccept = async (serverId, requestId) => {
    setActing(requestId)
    try {
      await handleJoinRequest(serverId, requestId, 'accept')
      setJoinRequests(prev => prev.filter(r => r.request.id !== requestId))
    } catch (err) {
      console.error('Failed to accept join request:', err)
    } finally {
      setActing(null)
    }
  }

  const handleJoinDecline = async (serverId, requestId) => {
    setActing(requestId)
    try {
      await handleJoinRequest(serverId, requestId, 'decline')
      setJoinRequests(prev => prev.filter(r => r.request.id !== requestId))
    } catch (err) {
      console.error('Failed to decline join request:', err)
    } finally {
      setActing(null)
    }
  }

  const handleChallengeAccept = async (challenge) => {
    const pred = prediction[challenge.id] || ''
    if (!pred) {
      setPrediction(prev => ({ ...prev, [`${challenge.id}_error`]: true }))
      return
    }

    setActing(`challenge-${challenge.id}`)
    try {
      await acceptChallenge(challenge.server_id, challenge.id, pred)
      setResponded(prev => ({ ...prev, [challenge.id]: 'accepted' }))
      setChallengeError(prev => ({ ...prev, [challenge.id]: undefined }))
    } catch (err) {
      const message = parseApiError(err)
      setChallengeError(prev => ({ ...prev, [challenge.id]: message }))
      console.error('Failed to accept challenge:', err)
    } finally {
      setActing(null)
    }
  }

  const handleChallengeDecline = async (challenge) => {
    setActing(`challenge-${challenge.id}`)
    try {
      await declineChallenge(challenge.server_id, challenge.id)
      setResponded(prev => ({ ...prev, [challenge.id]: 'declined' }))
      setChallengeError(prev => ({ ...prev, [challenge.id]: undefined }))
    } catch (err) {
      const message = parseApiError(err)
      setChallengeError(prev => ({ ...prev, [challenge.id]: message }))
      console.error('Failed to decline challenge:', err)
    } finally {
      setActing(null)
    }
  }

  const activeChallenges = useMemo(
    () => incomingChallenges.filter(c => !responded[c.id]),
    [incomingChallenges, responded]
  )

  const notificationItems = useMemo(() => {
    return [
      ...joinRequests.map(({ serverId, serverName, request }) => ({
        id: request.id,
        type: 'join',
        created_at: request.created_at,
        serverId,
        serverName,
        request,
      })),
      ...activeChallenges.map(challenge => ({
        id: `challenge-${challenge.id}`,
        type: 'challenge',
        created_at: challenge.created_at,
        challenge,
      })),
    ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }, [joinRequests, activeChallenges])

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(notificationItems.length / ITEMS_PER_PAGE)),
    [notificationItems.length]
  )

  const pageIndex = Math.min(Math.max(page, 1), totalPages)
  const visibleNotifications = useMemo(
    () => notificationItems.slice((pageIndex - 1) * ITEMS_PER_PAGE, pageIndex * ITEMS_PER_PAGE),
    [notificationItems, pageIndex]
  )
  const isEmpty = notificationItems.length === 0

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>NOTIFICATIONS</p>
            <h1 className={styles.title}>Manage your pending notifications</h1>
          </div>
        </div>

        {loading ? (
          <div className={styles.loading}>Loading notifications…</div>
        ) : isEmpty ? (
          <p className={styles.empty}>No pending notifications.</p>
        ) : (
          <>
            <div className={styles.summaryBar}>
              <div>
                <p className={styles.summaryLabel}>PENDING NOTIFICATIONS</p>
                <p className={styles.summaryTitle}>{joinRequests.length + activeChallenges.length} total</p>
              </div>
              <span className={styles.summaryMeta}>
                {joinRequests.length} join request{joinRequests.length === 1 ? '' : 's'} · {activeChallenges.length} challenge invite{activeChallenges.length === 1 ? '' : 's'}
              </span>
            </div>

            <div className={styles.notificationsList}>
              {visibleNotifications.map(item => (
                <div key={item.id} className={`${bellStyles.item} ${styles.notificationItem}`}>
                  <div className={styles.notificationRowTop}>
                    <span className={styles.notificationBadge}>
                      {item.type === 'join' ? 'JOIN REQUEST' : 'CHALLENGE INVITE'}
                    </span>
                    <p className={`${bellStyles.createAt} ${styles.notificationDate}`}>
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>

                  {item.type === 'join' ? (
                    <>
                      <div className={`${bellStyles.itemInfo} ${styles.notificationInfo}`}>
                        <p className={`${bellStyles.itemServer} ${styles.notificationTitle}`}>{item.serverName}</p>
                        <p className={`${bellStyles.itemUser} ${styles.notificationText}`}>
                          {item.request.user_full_name} wants to join {item.serverName}
                        </p>
                      </div>
                      <div className={`${bellStyles.itemActions} ${styles.notificationActions}`}>
                        <button
                          className={bellStyles.acceptBtn}
                          onClick={() => handleJoinAccept(item.serverId, item.request.id)}
                          disabled={acting === item.request.id}
                        >
                          {acting === item.request.id ? '...' : '✓'}
                        </button>
                        <button
                          className={bellStyles.declineBtn}
                          onClick={() => handleJoinDecline(item.serverId, item.request.id)}
                          disabled={acting === item.request.id}
                        >
                          {acting === item.request.id ? '...' : '✕'}
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className={`${bellStyles.itemInfo} ${styles.notificationInfo}`}>
                        <p className={`${bellStyles.itemServer} ${styles.notificationTitle}`}>
                          {item.challenge.match.home_team_name} vs {item.challenge.match.away_team_name}
                        </p>
                        <p className={`${bellStyles.itemUser} ${styles.notificationText}`}>Stake: {item.challenge.stake}</p>
                        <Link to={`/servers/${item.challenge.server_id}`} className={`${bellStyles.serverLink} ${styles.serverLinkLarge}`}>
                          View server
                        </Link>
                      </div>

                      {responded[item.challenge.id] ? (
                        <span className={`${bellStyles.respondedBadge} ${bellStyles[responded[item.challenge.id]]}`}>
                          {responded[item.challenge.id] === 'accepted' ? '✓ Accepted' : '✕ Declined'}
                        </span>
                      ) : (
                        <div className={`${bellStyles.challengeActions} ${styles.notificationActions}`}>
                          <input
                            className={`${bellStyles.predInput} ${styles.notificationInput}`}
                            placeholder="2-1"
                            value={prediction[item.challenge.id] || ''}
                            onChange={e => setPrediction(prev => ({
                              ...prev,
                              [item.challenge.id]: e.target.value,
                              [`${item.challenge.id}_error`]: false,
                            }))}
                          />
                          {prediction[`${item.challenge.id}_error`] && (
                            <span className={bellStyles.predError}>Enter prediction</span>
                          )}
                          {challengeError[item.challenge.id] && (
                            <span className={bellStyles.predError}>{challengeError[item.challenge.id]}</span>
                          )}
                          <div className={`${bellStyles.itemActions} ${styles.notificationActions}`}>
                            <button
                              className={bellStyles.acceptBtn}
                              onClick={() => handleChallengeAccept(item.challenge)}
                              disabled={acting === `challenge-${item.challenge.id}`}
                            >
                              {acting === `challenge-${item.challenge.id}` ? '...' : '✓'}
                            </button>
                            <button
                              className={bellStyles.declineBtn}
                              onClick={() => handleChallengeDecline(item.challenge)}
                              disabled={acting === `challenge-${item.challenge.id}`}
                            >
                              {acting === `challenge-${item.challenge.id}` ? '...' : '✕'}
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>

            <Pagination page={pageIndex} totalPages={totalPages} onChange={setPage} />
          </>
        )}
      </main>
    </div>
  )
}
