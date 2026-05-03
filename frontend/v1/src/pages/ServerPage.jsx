import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState, useCallback } from 'react'
import {
  getServer,
  getServerLeaderboard,
  getServerChallenges,
  updateServer,
  leaveServer
} from '../api/endpoints'
import Nav from '../components/Nav'
import ServerDetail from '../components/ServerDetail'
import styles from './ServerPage.module.css'

export default function ServerPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [serverDetails, setServerDetails] = useState(null)
  const [leaderboard, setLeaderboard] = useState(null)
  const [challenges, setChallenges] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAll = useCallback(async () => {
    setLoading(true)

    try {
      const [details, leader, chal] = await Promise.all([
        getServer(id),
        getServerLeaderboard(id),
        getServerChallenges(id),
      ])
      
      console.log('[ServerPage] Challenges fetched:', chal)

      setServerDetails(details)
      setLeaderboard(leader)
      setChallenges(chal || [])
      // runs only on dev, localhost
      if (import.meta.env.DEV) {
        await new Promise(resolve => setTimeout(resolve, 10000))
      }
    } catch (err) {
      console.error('Failed to fetch server page:', err)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleUpdate = async (name, isPublic) => {
    await updateServer(id, name, isPublic)
    await fetchAll()
  }

  const handleLeave = async () => {
    await leaveServer(id)
    navigate('/servers')
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <Nav />
        <main className={styles.main}>
          <div className={styles.loadingShell}>
            <div className={styles.loadingCard}>
              <div className={styles.loaderRow}>
                <div className={styles.loader} />
                <div>
                  <p className={styles.loadingTitle}>Loading server</p>
                  <p className={styles.loadingText}>Fetching server details and challenges…</p>
                </div>
              </div>

              <div className={styles.skeleton} />
              <div className={`${styles.skeleton} ${styles.skeletonShort}`} />
              <div className={`${styles.skeleton} ${styles.skeletonLong}`} />
            </div>
          </div>
        </main>
      </div>
    )
  }
  if (!serverDetails) {
    return (
      <div className={styles.page}>
        <Nav />
        <main className={styles.main}>
          <p className={styles.errorText}>Server not found</p>
        </main>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <ServerDetail
          serverDetails={serverDetails}
          leaderboard={leaderboard}
          challenges={challenges}
          onUpdate={handleUpdate}
          onLeave={handleLeave}
          onRefresh={fetchAll}
        />
      </main>
    </div>
  )
}