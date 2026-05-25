import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import Nav from '../components/Nav'
import ConfirmationDialog from '../components/ConfirmationDialog'
import FeedbackBanner from '../components/FeedbackBanner'
import {
  updateProfile,
  getGoogleStatus,
  connectGoogle,
  disconnectGoogle,
  deleteAccount,
  getSubscriptions,
  getMyServers,
} from '../api/endpoints'
import styles from './UserProfile.module.css'

export default function UserProfile() {
  const { user, signIn, signOut } = useAuth()
  const [name, setName] = useState(user?.full_name || '')
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [googleConnected, setGoogleConnected] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [googleConfirmation, setGoogleConfirmation] = useState(null)
  const [subscriptionStats, setSubscriptionStats] = useState({
    total: 0,
    league: 0,
    team: 0,
    match: 0,
  })
  const [serverCount, setServerCount] = useState(0)
  const [statsLoading, setStatsLoading] = useState(true)
  const [feedback, setFeedback] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const navigate = useNavigate()

  useEffect(() => {
    setName(user?.full_name || '')
  }, [user])

  useEffect(() => {
    let active = true
    getGoogleStatus()
      .then(data => {
        if (active) setGoogleConnected(data.connected)
      })
      .catch(() => {})

    const loadProfileStats = async () => {
      try {
        const [subscriptions, servers] = await Promise.all([
          getSubscriptions(),
          getMyServers({ page: 1, pageSize: 50 }),
        ])

        if (!active) return

        const counts = subscriptions.reduce((acc, sub) => {
          acc[sub.subscription_type] = (acc[sub.subscription_type] || 0) + 1
          return acc
        }, { league: 0, team: 0, match: 0 })

        setSubscriptionStats({
          total: subscriptions.length,
          league: counts.league,
          team: counts.team,
          match: counts.match,
        })

        const totalServers = typeof servers.total === 'number'
          ? servers.total
          : Array.isArray(servers)
            ? servers.length
            : servers?.items?.length || 0
        setServerCount(totalServers)
      } catch (err) {
        console.error('Failed to load profile stats:', err)
      } finally {
        if (active) setStatsLoading(false)
      }
    }

    loadProfileStats()

    return () => { active = false }
  }, [])

  const showFeedback = useCallback((type, message, duration = 6000) => {
    setFeedback({ type, message })
    window.setTimeout(() => setFeedback(null), duration)
  }, [])

  const handleEdit = () => {
    setEditing(true)
  }

  const handleSave = async () => {
    if (!name.trim()) {
      showFeedback('error', 'Name cannot be empty.')
      return
    }

    setSaving(true)
    try {
      const updated = await updateProfile({ full_name: name.trim() })
      signIn(updated)
      setEditing(false)
      showFeedback('success', 'Profile updated successfully.')
    } catch (err) {
      console.error('Failed to update profile:', err)
      showFeedback('error', err.response?.data?.detail || 'Could not update profile.')
    } finally {
      setSaving(false)
    }
  }

  const openGoogleConfirmation = (action) => {
    setGoogleConfirmation({
      action,
      title: action === 'connect' ? 'Connect Google Calendar' : 'Disconnect Google Calendar',
      description: action === 'connect'
        ? 'Allow Football Alerts to connect your Google Calendar so it can sync your matches.'
        : 'Disconnect Google Calendar and stop syncing your match events.',
      confirmLabel: action === 'connect' ? 'Connect Google' : 'Disconnect Google',
      confirmVariant: action === 'connect' ? 'primary' : 'danger',
    })
  }

  const handleGoogleConfirm = async () => {
    if (!googleConfirmation) return

    if (googleConfirmation.action === 'connect') {
      setGoogleConfirmation(null)
      connectGoogle()
      return
    }

    setGoogleLoading(true)
    try {
      await disconnectGoogle()
      setGoogleConnected(false)
      showFeedback('success', 'Google disconnected.')
    } catch (err) {
      showFeedback('error', 'Failed to disconnect Google.')
    } finally {
      setGoogleLoading(false)
      setGoogleConfirmation(null)
    }
  }

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const handleDeleteAccount = async () => {
    setDeleting(true)
    try {
      await deleteAccount()
      signOut()
      navigate('/login')
    } catch (err) {
      showFeedback('error', 'Failed to delete account.')
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>User Profile</h1>
            <p className={styles.subtitle}>Manage your account details, Google calendar connection, and profile settings.</p>
          </div>
        </div>

        {feedback && (
          <FeedbackBanner type={feedback.type} message={feedback.message} onClose={() => setFeedback(null)} />
        )}

        <section className={styles.card}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Account Summary</h2>
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Active alerts</span>
            <span className={styles.value}>
              {statsLoading ? 'Loading…' : subscriptionStats.total}
            </span>
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Alert types</span>
            <span className={styles.value}>
              {statsLoading ? 'Loading…' : `${subscriptionStats.league} league · ${subscriptionStats.team} team · ${subscriptionStats.match} match`}
            </span>
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Servers joined</span>
            <span className={styles.value}>{statsLoading ? 'Loading…' : serverCount}</span>
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Account Information</h2>
            {!editing ? (
              <button className={styles.editBtn} onClick={handleEdit}>Edit</button>
            ) : null}
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Full name</span>
            {editing ? (
              <input
                className={styles.input}
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={saving}
              />
            ) : (
              <span className={styles.value}>{user?.full_name || '—'}</span>
            )}
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Email</span>
            <span className={styles.value}>{user?.email || '—'}</span>
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Member since</span>
            <span className={styles.value}>{user?.created_at ? new Date(user.created_at).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' }) : '—'}</span>
          </div>

          {editing && (
            <div className={styles.actions}>
              <button className={styles.cancelBtn} onClick={() => setEditing(false)} disabled={saving}>Cancel</button>
              <button className={styles.saveBtn} onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : 'Save changes'}
              </button>
            </div>
          )}
        </section>

        <section className={styles.card}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Google Calendar</h2>
          </div>

          <div className={styles.row}>
            <span className={styles.label}>Connection status</span>
            <span className={styles.value}>{googleConnected ? 'Connected' : 'Not connected'}</span>
          </div>

          <div className={styles.actions}>
            {googleConnected ? (
              <button className={styles.secondaryBtn} onClick={() => openGoogleConfirmation('disconnect')} disabled={googleLoading}>
                {googleLoading ? 'Disconnecting...' : 'Disconnect Google'}
              </button>
            ) : (
              <button className={styles.primaryBtn} onClick={() => openGoogleConfirmation('connect')} disabled={googleLoading}>
                {googleLoading ? 'Connecting...' : 'Connect Google'}
              </button>
            )}
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Danger Zone</h2>
          </div>
          <p className={styles.description}>Delete your account permanently. This action cannot be undone.</p>
          <button className={styles.dangerBtn} onClick={() => setConfirmDelete(true)} disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete Account'}
          </button>
        </section>

        <ConfirmationDialog
          isOpen={confirmDelete}
          title="Delete account"
          description="This will permanently delete your account and all alert subscriptions. This cannot be undone."
          confirmLabel={deleting ? 'Deleting...' : 'Delete account'}
          cancelLabel="Cancel"
          confirmVariant="danger"
          isLoading={deleting}
          onConfirm={handleDeleteAccount}
          onCancel={() => setConfirmDelete(false)}
        />

        <ConfirmationDialog
          isOpen={!!googleConfirmation}
          title={googleConfirmation?.title}
          description={googleConfirmation?.description}
          confirmLabel={googleConfirmation?.confirmLabel}
          cancelLabel="Cancel"
          confirmVariant={googleConfirmation?.confirmVariant}
          isLoading={googleLoading && googleConfirmation?.action === 'disconnect'}
          onConfirm={handleGoogleConfirm}
          onCancel={() => setGoogleConfirmation(null)}
        />
      </main>
    </div>
  )
}
