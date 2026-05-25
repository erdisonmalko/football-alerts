import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import ServersList from '../components/ServersList'
import ServerDetail from '../components/ServerDetail'
import ServerCreateModal from '../components/ServerCreateModal'
import FeedbackBanner from '../components/FeedbackBanner'
import ConfirmationDialog from '../components/ConfirmationDialog'
import styles from './Dashboard.module.css'
import {
  getMyServers,
  createServer, getServer,
  getServerLeaderboard,
  getPublicServers, requestToJoin, leaveServer,
  updateServer
} from '../api/endpoints'

export default function Servers() {
  const { user } = useAuth()

  const [servers, setServers] = useState({ items: [], total_pages: 1 })
  const [myServerPage, setMyServerPage] = useState(1)
  const [selectedServer, setSelectedServer] = useState(null)
  const [serverDetails, setServerDetails] = useState(null)
  const [leaderboard, setLeaderboard] = useState(null)
  const [challenges, setChallenges] = useState([])
  const [serversLoading, setServersLoading] = useState(true)
  const [publicServers, setPublicServers] = useState({ items: [], total_pages: 1 })
  const [publicServersLoading, setPublicServersLoading] = useState(false)
  const [publicServerPage, setPublicServerPage] = useState(1)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creatingServer, setCreatingServer] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [confirmation, setConfirmation] = useState(null)
  const [confirmationLoading, setConfirmationLoading] = useState(false)
  const feedbackTimer = useRef(null)

  const navigate = useNavigate()

  const handleSelectServer = (serverId) => {
    navigate(`/servers/${serverId}`)
  }

  const fetchServers = useCallback(async (page = 1) => {
    setServersLoading(true)
    try {
      const data = await getMyServers({ page, pageSize: 15 })
      setServers(data)
      setMyServerPage(page)
    } catch (err) {
      console.error('Failed to fetch servers:', err)
    } finally {
      setServersLoading(false)
    }
  }, [])

  const fetchPublicServers = useCallback(async (page = 1) => {
    setPublicServersLoading(true)
    try {
      const data = await getPublicServers({ page, pageSize: 15 })
      setPublicServers(data)
      setPublicServerPage(page)
    } catch (err) {
      console.error('Failed to fetch public servers:', err)
    } finally {
      setPublicServersLoading(false)
    }
  }, [])


  const showFeedback = useCallback((type, message, duration = 6000) => {
    if (feedbackTimer.current) {
      clearTimeout(feedbackTimer.current)
    }

    setFeedback({ type, message })
    feedbackTimer.current = window.setTimeout(() => {
      setFeedback(null)
      feedbackTimer.current = null
    }, duration)
  }, [])

  useEffect(() => {
    return () => {
      if (feedbackTimer.current) {
        clearTimeout(feedbackTimer.current)
      }
    }
  }, [])

  const dismissFeedback = useCallback(() => {
    if (feedbackTimer.current) {
      clearTimeout(feedbackTimer.current)
      feedbackTimer.current = null
    }
    setFeedback(null)
  }, [])

  const openJoinConfirmation = useCallback((server) => {
    setConfirmation({
      action: 'join',
      serverId: server.id,
      title: 'Send join request?',
      description: `Send a join request to ${server.name}?`,
      confirmLabel: 'Send request',
      cancelLabel: 'Cancel',
    })
  }, [])

  const closeConfirmation = useCallback(() => {
    setConfirmation(null)
  }, [])

  const handleCreateServer = useCallback(async (name, isPublic) => {
    setCreatingServer(true)
    try {
      const newServer = await createServer(name, isPublic)
      setServers(prev => ({
        ...prev,
        items: [newServer, ...prev.items],
        total: prev.total + 1
      }))
      setShowCreateModal(false)
      showFeedback('success', `Server created: ${newServer.name}`)
    } catch (err) {
      console.error('Failed to create server:', err)
      throw err
    } finally {
      setCreatingServer(false)
    }
  }, [showFeedback])

  const handleRequestToJoin = useCallback(async (serverId) => {
    try {
      await requestToJoin(serverId)
      showFeedback('success', 'Request sent!')
      await fetchPublicServers(publicServerPage)
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Could not send request.'
      console.error('Server says:', errorMessage)
      showFeedback('error', errorMessage)
    }
  }, [fetchPublicServers, publicServerPage, showFeedback])

  // Initial load: fetch both tabs' first pages
  useEffect(() => {
    fetchServers(1)
    fetchPublicServers(1)
  }, [fetchServers, fetchPublicServers])

  // Separate effect for my-servers page changes
  useEffect(() => {
    if (myServerPage > 1) {
      fetchServers(myServerPage)
    }
  }, [myServerPage, fetchServers])

  // Separate effect for public-servers page changes
  useEffect(() => {
    if (publicServerPage > 1) {
      fetchPublicServers(publicServerPage)
    }
  }, [publicServerPage, fetchPublicServers])

  const handleLeaveServer = useCallback(async (serverId) => {
    try {
      await leaveServer(serverId)
      setServers(prev => ({
        ...prev,
        items: prev.items.filter(s => s.id !== serverId),
        total: Math.max(0, prev.total - 1)
      }))
      if (selectedServer === serverId) {
        setSelectedServer(null)
        setServerDetails(null)
      }
      showFeedback('success', 'Left server successfully.')
    } catch (err) {
      console.error('Failed to leave server:', err)
      const message = err.response?.data?.detail || 'Could not leave the server. Please try again.'
      showFeedback('error', message)
    }
  }, [selectedServer, showFeedback])

  const handleConfirmAction = useCallback(async () => {
    if (!confirmation) return

    setConfirmationLoading(true)
    try {
      if (confirmation.action === 'join') {
        await handleRequestToJoin(confirmation.serverId)
      } else if (confirmation.action === 'leave') {
        await handleLeaveServer(confirmation.serverId)
      }
    } finally {
      setConfirmationLoading(false)
      setConfirmation(null)
    }
  }, [confirmation, handleRequestToJoin, handleLeaveServer])

  const handleServerPageChange = useCallback((nextPage, tab) => {
    if (tab === 'mine') {
      setMyServerPage(nextPage)
    } else if (tab === 'discover') {
      setPublicServerPage(nextPage)
    }
  }, [])

  const handleUpdateServer = useCallback(async (serverId, name, isPublic) => {
    if (!serverId) {
      console.warn('updateServer called with invalid serverId:', serverId)
      return
    }

    try {
      await updateServer(serverId, name, isPublic)
      await fetchServers()
      showFeedback('success', 'Server updated successfully.')
    } catch (err) {
      console.error('Failed to update server:', err)
      const message = err.response?.data?.detail || 'Could not update the server. Please try again.'
      showFeedback('error', message)
    }
  }, [fetchServers, showFeedback])

  const name = user?.full_name?.split(' ')[0] || 'Fan'

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>SERVERS</h1>
          </div>
          <button
            className={styles.createServerBtn}
            onClick={() => setShowCreateModal(true)}
          >
            + CREATE SERVER
          </button>
        </div>
        {feedback && (
          <FeedbackBanner
            type={feedback.type}
            message={feedback.message}
            onClose={dismissFeedback}
          />
        )}

        <ConfirmationDialog
          isOpen={!!confirmation}
          title={confirmation?.title}
          description={confirmation?.description}
          confirmLabel={confirmation?.confirmLabel}
          cancelLabel={confirmation?.cancelLabel}
          isLoading={confirmationLoading}
          onConfirm={handleConfirmAction}
          onCancel={closeConfirmation}
        />

        <ServersList
              servers={servers}
              publicServers={publicServers}
              loading={serversLoading}
              publicLoading={publicServersLoading}
              onSelectServer={handleSelectServer}
              onRequestJoin={openJoinConfirmation}
              onLeaveServer={handleLeaveServer}
              onPageChange={handleServerPageChange}
            />
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