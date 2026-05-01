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

  if (loading) return <div>Loading...</div>
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