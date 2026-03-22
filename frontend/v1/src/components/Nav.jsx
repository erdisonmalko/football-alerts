import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { updateProfile, deleteAccount, getGoogleStatus, connectGoogle, disconnectGoogle } from '../api/endpoints'
import styles from './Nav.module.css'

export default function Nav() {
  const { user, signIn, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [googleConnected, setGoogleConnected] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const dropdownRef = useRef(null)

  // Check Google status when dropdown opens
  useEffect(() => {
    if (open) {
      getGoogleStatus()
        .then(data => setGoogleConnected(data.connected))
        .catch(() => {})
    }
  }, [open])

  // Handle redirect back from Google OAuth
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const googleParam = params.get('google')
    if (googleParam === 'connected') {
      setGoogleConnected(true)
      // Clean up URL
      navigate(location.pathname, { replace: true })
    } else if (googleParam === 'error') {
      navigate(location.pathname, { replace: true })
    }
  }, [location, navigate])

  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false)
        setEditing(false)
        setConfirmDelete(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const handleEditOpen = () => {
    setName(user?.full_name || '')
    setEditing(true)
    setConfirmDelete(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await updateProfile({ full_name: name.trim() || null })
      signIn(updated)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleGoogleConnect = () => {
    connectGoogle() // redirects browser
  }

  const handleGoogleDisconnect = async () => {
    setGoogleLoading(true)
    try {
      await disconnectGoogle()
      setGoogleConnected(false)
    } catch {
      // ignore
    } finally {
      setGoogleLoading(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteAccount()
      signOut()
      navigate('/login')
    } finally {
      setDeleting(false)
    }
  }

  const isActive = (path) => location.pathname === path
  const displayName = user?.full_name || user?.email || ''

  return (
    <nav className={styles.nav}>
      <Link to="/dashboard" className={styles.logo}>
        <span className={styles.logoMark}>FA</span>
        <span className={styles.logoText}>FOOTBALL<br />ALERTS</span>
      </Link>

      <div className={styles.links}>
        <Link to="/dashboard" className={`${styles.link} ${isActive('/dashboard') ? styles.active : ''}`}>
          MATCHES
        </Link>
        <Link to="/subscriptions" className={`${styles.link} ${isActive('/subscriptions') ? styles.active : ''}`}>
          ALERTS
        </Link>
      </div>

      <div className={styles.profileWrap} ref={dropdownRef}>
        <button
          className={`${styles.profileBtn} ${open ? styles.profileBtnOpen : ''}`}
          onClick={() => { setOpen(o => !o); setEditing(false); setConfirmDelete(false) }}
        >
          <span className={styles.profileInitial}>
            {displayName.charAt(0).toUpperCase()}
          </span>
          <span className={styles.profileName}>{displayName}</span>
          <span className={styles.profileCaret}>{open ? '▲' : '▼'}</span>
        </button>

        {open && (
          <div className={styles.dropdown}>
            <div className={styles.dropHeader}>
              <p className={styles.dropEmail}>{user?.email}</p>
              <p className={styles.dropJoined}>
                Member since {new Date(user?.created_at).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })}
              </p>
            </div>

            {!confirmDelete && (
              <div className={styles.dropSection}>
                {editing ? (
                  <div className={styles.editRow}>
                    <input
                      className={styles.nameInput}
                      value={name}
                      onChange={e => setName(e.target.value)}
                      placeholder="Your name"
                      maxLength={255}
                      autoFocus
                      onKeyDown={e => e.key === 'Enter' && handleSave()}
                    />
                    <button className={styles.saveBtn} onClick={handleSave} disabled={saving}>
                      {saving ? '...' : 'SAVE'}
                    </button>
                    <button className={styles.cancelBtn} onClick={() => setEditing(false)}>
                      X
                    </button>
                  </div>
                ) : (
                  <button className={styles.dropAction} onClick={handleEditOpen}>
                    EDIT NAME
                  </button>
                )}
              </div>
            )}

            <div className={styles.dropDivider} />

            {/* Google Calendar */}
            {!confirmDelete && (
              <>
                <div className={styles.dropSection}>
                  <div className={styles.googleRow}>
                    <div className={styles.googleInfo}>
                      <span className={styles.googleLabel}>GOOGLE CALENDAR</span>
                      <span className={`${styles.googleStatus} ${googleConnected ? styles.googleConnected : styles.googleDisconnected}`}>
                        {googleConnected ? '● CONNECTED' : '○ NOT CONNECTED'}
                      </span>
                    </div>
                    {googleConnected ? (
                      <button
                        className={styles.googleBtn}
                        onClick={handleGoogleDisconnect}
                        disabled={googleLoading}
                      >
                        {googleLoading ? '...' : 'DISCONNECT'}
                      </button>
                    ) : (
                      <button
                        className={`${styles.googleBtn} ${styles.googleBtnConnect}`}
                        onClick={handleGoogleConnect}
                        disabled={googleLoading}
                      >
                        CONNECT
                      </button>
                    )}
                  </div>
                </div>
                <div className={styles.dropDivider} />
              </>
            )}

            {!confirmDelete && (
              <button className={styles.dropAction} onClick={handleSignOut}>
                SIGN OUT
              </button>
            )}

            {!confirmDelete ? (
              <button
                className={`${styles.dropAction} ${styles.dropDanger}`}
                onClick={() => { setConfirmDelete(true); setEditing(false) }}
              >
                DELETE ACCOUNT
              </button>
            ) : (
              <div className={styles.deleteConfirm}>
                <p className={styles.deleteWarning}>
                  This will permanently delete your account and all alert subscriptions. This cannot be undone.
                </p>
                <div className={styles.deleteActions}>
                  <button
                    className={styles.deleteConfirmBtn}
                    onClick={handleDelete}
                    disabled={deleting}
                  >
                    {deleting ? 'DELETING...' : 'YES, DELETE'}
                  </button>
                  <button
                    className={styles.cancelBtn}
                    onClick={() => setConfirmDelete(false)}
                  >
                    CANCEL
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}