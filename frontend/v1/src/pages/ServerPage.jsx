import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState, useCallback } from 'react'
import {
  getServer,
  getServerLeaderboard,
  getServerChallenges,
  updateServer,
  leaveServer
} from '../api/endpoints'
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
      <div className="pageLoader">
        <div className="loader" />
        <p className="loaderText">Loading server...</p>
      </div>
    )
  }
  if (!serverDetails) return <div>Server not found</div>

  return (
    <ServerDetail
      serverDetails={serverDetails}
      leaderboard={leaderboard}
      challenges={challenges}
      onUpdate={handleUpdate}
      onLeave={handleLeave}
      onRefresh={fetchAll}
    />
  )
}