import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import ServersList from '../components/ServersList'
import ServerDetail from '../components/ServerDetail'
import ServerCreateModal from '../components/ServerCreateModal'
import styles from './Dashboard.module.css'
import {
  getMyServers,
  createServer, getServer,
  getServerLeaderboard, getServerChallenges,
  getPublicServers, requestToJoin, leaveServer
} from '../api/endpoints'

export default function Servers() {
  const { user } = useAuth()

  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState(null)
  const [serverDetails, setServerDetails] = useState(null)
  const [leaderboard, setLeaderboard] = useState(null)
  const [challenges, setChallenges] = useState([])
  const [serversLoading, setServersLoading] = useState(true)
  const [publicServers, setPublicServers] = useState([])
  const [publicServersLoading, setPublicServersLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creatingServer, setCreatingServer] = useState(false)

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

  const fetchPublicServers = useCallback(async () => {
    setPublicServersLoading(true)
    try {
      const data = await getPublicServers()
      setPublicServers(data)
    } catch (err) {
      console.error('Failed to fetch public servers:', err)
    } finally {
      setPublicServersLoading(false)
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
      setServers(prev => [newServer, ...prev])
      setShowCreateModal(false)
    } catch (err) {
      console.error('Failed to create server:', err)
      throw err
    } finally {
      setCreatingServer(false)
    }
  }, [])

  const handleRequestToJoin = useCallback(async (serverId) => {
    await requestToJoin(serverId)
    await fetchPublicServers()
  }, [fetchPublicServers])

  useEffect(() => {
    fetchServers()
    fetchPublicServers()
  }, [fetchServers, fetchPublicServers])

  const handleLeaveServer = useCallback(async (serverId) => {
    if (!window.confirm("Are you sure you want to leave this server?")) return;

    try {
      await leaveServer(serverId);
      // Remove the server from the list and clear selection if it's the open one
      setServers(prev => prev.filter(s => s.id !== serverId));
      if (selectedServer === serverId) {
        setSelectedServer(null);
        setServerDetails(null);
      }
    } catch (err) {
      console.error('Failed to leave server:', err);
      alert("Could not leave the server. Please try again.");
    }
  }, [selectedServer]);


  const name = user?.full_name?.split(' ')[0] || 'Fan'

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>WELCOME BACK, {name.toUpperCase()}</p>
            <h1 className={styles.title}>SERVERS</h1>
          </div>
          <button
            className={styles.createServerBtn}
            onClick={() => setShowCreateModal(true)}
          >
            + CREATE SERVER
          </button>
        </div>

        {selectedServer && serverDetails ? (
          <ServerDetail
            serverDetails={serverDetails}
            leaderboard={leaderboard}
            challenges={challenges}
            onBack={() => { setSelectedServer(null); setServerDetails(null) }}
            onLeave={() => handleLeaveServer(serverDetails.id)}
          />
          
        ) : (
          <ServersList
            servers={servers}
            publicServers={publicServers}
            loading={serversLoading}
            publicLoading={publicServersLoading}
            onSelectServer={fetchServerDetails}
            onRequestJoin={handleRequestToJoin}
            onLeaveServer={handleLeaveServer} 
          />
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