import { useEffect, useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  getPendingRequestsCount, getMyServers,
  getJoinRequests, handleJoinRequest,
  getChallengeFeed, acceptChallenge, declineChallenge,
} from '../api/endpoints'
import { parseApiError } from '../api/errorHandler'
import styles from './NotificationBell.module.css'

const POLL_INTERVAL = 60 * 1000

export default function NotificationBell() {
  const [count, setCount] = useState(0)
  const [open, setOpen] = useState(false)
  const [joinRequests, setJoinRequests] = useState([])
  const [incomingChallenges, setIncomingChallenges] = useState([])
  const [loading, setLoading] = useState(false)
  const [acting, setActing] = useState(null)
  const [prediction, setPrediction] = useState({}) // { challengeId: value }
  const [challengeError, setChallengeError] = useState({})
  const [responded, setResponded] = useState({}) // { challengeId: 'accepted'|'declined' }
  const ref = useRef(null)

  const fetchCount = useCallback(async () => {
    try {
      const [requestsData, feedData] = await Promise.all([
        getPendingRequestsCount(),
        getChallengeFeed(),
      ])
      setCount((requestsData.count || 0) + (feedData.incoming?.length || 0))
    } catch {
      // silent
    }
  }, [])

  const fetchAll = useCallback(async () => {
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
            return reqs.map(req => {
              return { serverId: server.id, serverName: server.name, request: req }
            })
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
    fetchCount()
    const interval = setInterval(fetchCount, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchCount])

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleOpen = () => {
    setOpen(o => !o)
    if (!open) fetchAll()
  }

  const handleJoinAccept = async (serverId, requestId) => {
    setActing(requestId)
    try {
      await handleJoinRequest(serverId, requestId, 'accept')
      setJoinRequests(prev => prev.filter(r => r.request.id !== requestId))
      setCount(c => Math.max(0, c - 1))
    } finally {
      setActing(null)
    }
  }

  const handleJoinDecline = async (serverId, requestId) => {
    setActing(requestId)
    try {
      await handleJoinRequest(serverId, requestId, 'decline')
      setJoinRequests(prev => prev.filter(r => r.request.id !== requestId))
      setCount(c => Math.max(0, c - 1))
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
      setCount(c => Math.max(0, c - 1))
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
      setCount(c => Math.max(0, c - 1))
    } catch (err) {
      const message = parseApiError(err)
      setChallengeError(prev => ({ ...prev, [challenge.id]: message }))
      console.error('Failed to decline challenge:', err)
    } finally {
      setActing(null)
    }
  }

  const totalCount = joinRequests.length + incomingChallenges.filter(c => !responded[c.id]).length
  const isEmpty = joinRequests.length === 0 && incomingChallenges.length === 0
  const MAX_VISIBLE = 5

  // In the render:
  const visibleJoinRequests = joinRequests.slice(0, MAX_VISIBLE)
  const hiddenJoinCount = joinRequests.length - visibleJoinRequests.length

  const visibleChallenges = incomingChallenges.filter(c => !responded[c.id]).slice(0, MAX_VISIBLE)
  const hiddenChallengeCount = incomingChallenges.filter(c => !responded[c.id]).length - visibleChallenges.length
  
  return (
    <div className={styles.wrap} ref={ref}>
      <button className={styles.bell} onClick={handleOpen}>
        <span className={styles.bellIcon}>🔔</span>
        {count > 0 && (
          <span className={styles.badge}>{count > 99 ? '99+' : count}</span>
        )}
      </button>

      {open && (
        <div className={styles.panel}>
          <p className={styles.panelTitle}>NOTIFICATIONS</p>

          {loading ? (
            <p className={styles.empty}>Loading...</p>
          ) : isEmpty ? (
            <p className={styles.empty}>No notifications.</p>
          ) : (
            <div className={styles.list}>

              {/* Join requests */}
              {visibleJoinRequests.length > 0 && (
                <>
                  <p className={styles.sectionLabel}>JOIN REQUESTS</p>
                  {visibleJoinRequests.map(({ serverId, serverName, request }) => (
                    <div key={request.id} className={styles.item}>
                      <div className={styles.itemInfo}>
                        <p className={styles.createAt}>
                          {new Date(request.created_at).toLocaleString()}
                        </p>
                        <p className={styles.itemServer}>{serverName}</p>
                        <p className={styles.itemUser}>
                          {request.user_full_name} wants to join {serverName}
                        </p>
                      </div>
                      <div className={styles.itemActions}>
                        <button
                          className={styles.acceptBtn}
                          onClick={() => handleJoinAccept(serverId, request.id)}
                          disabled={acting === request.id}
                        >
                          {acting === request.id ? '...' : '✓'}
                        </button>
                        <button
                          className={styles.declineBtn}
                          onClick={() => handleJoinDecline(serverId, request.id)}
                          disabled={acting === request.id}
                        >
                          {acting === request.id ? '...' : '✕'}
                        </button>
                      </div>
                    </div>
                  ))}
                </>
              )}
              {hiddenJoinCount > 0 && (
                <Link to="/notifications" className={styles.seeMore} onClick={() => setOpen(false)}>
                  +{hiddenJoinCount} more join requests
                </Link>
              )}

              {/* Challenge invites */}
              {visibleChallenges.length > 0 && (
                <>
                  <p className={styles.sectionLabel}>CHALLENGE INVITES</p>
                  {visibleChallenges.map(challenge => (
                    <div key={challenge.id} className={styles.item}>
                      <div className={styles.itemInfo}>
                        <p className={styles.createAt}>
                          {new Date(challenge.created_at).toLocaleString()}
                        </p>
                        <p className={styles.itemServer}>
                          {challenge.match.home_team_name} vs {challenge.match.away_team_name}
                        </p>
                        <p className={styles.itemUser}>
                          Stake: {challenge.stake}
                        </p>
                      </div>

                      {responded[challenge.id] ? (
                        <span className={`${styles.respondedBadge} ${styles[responded[challenge.id]]}`}>
                          {responded[challenge.id] === 'accepted' ? '✓ Accepted' : '✕ Declined'}
                        </span>
                      ) : (
                        <div className={styles.challengeActions}>
                          <input
                            className={styles.predInput}
                            placeholder="2-1"
                            value={prediction[challenge.id] || ''}
                            onChange={e => setPrediction(prev => ({
                              ...prev,
                              [challenge.id]: e.target.value,
                              [`${challenge.id}_error`]: false,
                            }))}
                          />
                          {prediction[`${challenge.id}_error`] && (
                            <span className={styles.predError}>Enter prediction</span>
                          )}
                          {challengeError[challenge.id] && (
                            <span className={styles.predError}>{challengeError[challenge.id]}</span>
                          )}
                          <div className={styles.itemActions}>
                            <button
                              className={styles.acceptBtn}
                              onClick={() => handleChallengeAccept(challenge)}
                              disabled={acting === `challenge-${challenge.id}`}
                            >
                              {acting === `challenge-${challenge.id}` ? '...' : '✓'}
                            </button>
                            <button
                              className={styles.declineBtn}
                              onClick={() => handleChallengeDecline(challenge)}
                              disabled={acting === `challenge-${challenge.id}`}
                            >
                              {acting === `challenge-${challenge.id}` ? '...' : '✕'}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}

              {hiddenChallengeCount > 0 && (
                <Link to="/notifications" className={styles.seeMore} onClick={() => setOpen(false)}>
                  +{hiddenChallengeCount} more challenge invites
                </Link>
              )}

            </div>
          )}
        </div>
      )}
    </div>
  )
}