
import { useEffect, useState, useRef, useCallback } from 'react'
import { getPendingRequestsCount, getMyServers, 
  getJoinRequests, handleJoinRequest
} from '../api/endpoints'
import styles from './NotificationBell.module.css'

const POLL_INTERVAL = 60 * 1000 // check every 60s

export default function NotificationBell() {
  const [count, setCount] = useState(0)
  const [open, setOpen] = useState(false)
  const [requests, setRequests] = useState([]) // { serverId, serverName, request }
  const [loading, setLoading] = useState(false)
  const [acting, setActing] = useState(null)
  const ref = useRef(null)

  const fetchCount = useCallback(async () => {
    try {
      const data = await getPendingRequestsCount()
      setCount(data.count)
    } catch {
      // silent
    }
  }, [])

  const fetchRequests = useCallback(async () => {
    setLoading(true)
    try {
      const servers = await getMyServers()      
      // Fetch all requests in parallel
      const nestedRequests = await Promise.all(
        servers.map(async (server) => {
          try {
            const reqs = await getJoinRequests(server.id)
            return reqs.map(req => ({ 
              serverId: server.id, 
              serverName: server.name, 
              request: req 
            }))
          } catch (err) {
            console.error(`Failed to fetch reqs for server ${server.id}:`, err)
            return [] // Return empty array so other servers still load
          }
        })
      )
      
      // Flatten the array of arrays into one list
      setRequests(nestedRequests.flat())
    } catch (err) {
      console.error('Failed to fetch servers:', err)
    } finally {
      setLoading(false)
    }
  }, [])


  // Poll count periodically
  useEffect(() => {
    fetchCount()
    const interval = setInterval(fetchCount, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchCount])

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleOpen = () => {
    setOpen(o => !o)
    if (!open) fetchRequests()
  }

  const handleAccept = async (serverId, requestId) => {
    setActing(requestId)
    try {
      await handleJoinRequest(serverId, requestId, 'accept')
      setRequests(prev => prev.filter(r => r.request.id !== requestId))
      setCount(c => Math.max(0, c - 1))
    } finally {
      setActing(null)
    }
  }

  const handleDecline = async (serverId, requestId) => {
    setActing(requestId)
    try {
      await handleJoinRequest(serverId, requestId, 'decline')
      setRequests(prev => prev.filter(r => r.request.id !== requestId))
      setCount(c => Math.max(0, c - 1))
    } finally {
      setActing(null)
    }
  }

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
          <p className={styles.panelTitle}>JOIN REQUESTS</p>
          {loading ? (
            <p className={styles.empty}>Loading...</p>
          ) : requests.length === 0 ? (
            <p className={styles.empty}>No pending requests.</p>
          ) : (
            <div className={styles.list}>
              {requests.map(({ serverId, serverName, request }) => (
                <div key={request.id} className={styles.item}>
                  <div className={styles.itemInfo}>
                    <p className={styles.itemServer}>{serverName}</p>
                    <p className={styles.itemUser}>User #{request.user_id} wants to join</p>
                  </div>
                  <div className={styles.itemActions}>
                    <button
                      className={styles.acceptBtn}
                      onClick={() => handleAccept(serverId, request.id)}
                      disabled={acting === request.id}
                    >
                      {acting === request.id ? '...' : '✓'}
                    </button>
                    <button
                      className={styles.declineBtn}
                      onClick={() => handleDecline(serverId, request.id)}
                      disabled={acting === request.id}
                    >
                      {acting === request.id ? '...' : '✕'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}