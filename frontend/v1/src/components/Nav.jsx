import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

import styles from './Nav.module.css'
import NotificationBell from './NotificationBell'
import ConfirmationDialog from './ConfirmationDialog'

export default function Nav() {
  const { user, signIn, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [confirmSignOut, setConfirmSignOut] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const dropdownRef = useRef(null)


  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSignOut = async () => {
    setSigningOut(true)
    setOpen(false)
    try {
      await signOut()
      navigate('/login')
    } finally {
      setSigningOut(false)
      setConfirmSignOut(false)
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
        <Link to="/servers" className={`${styles.link} ${isActive('/servers') ? styles.active : ''}`}>
          SERVERS
        </Link>
        <Link to="/notifications" className={`${styles.link} ${isActive('/notifications') ? styles.active : ''}`}>
          NOTIFICATIONS
        </Link>
      </div>
      <NotificationBell />
      <div className={styles.profileWrap} ref={dropdownRef}>
        <button
          className={`${styles.profileBtn} ${open ? styles.profileBtnOpen : ''}`}
          onClick={() => setOpen(o => !o)}
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

            <div className={styles.dropSection}>
              <Link to="/profile" className={styles.dropAction} onClick={() => setOpen(false)}>
                PROFILE
              </Link>
            </div>

            <div className={styles.dropDivider} />

            <button className={styles.dropAction} onClick={() => setConfirmSignOut(true)}>
              SIGN OUT
            </button>
          </div>
        )}
      </div>

      <ConfirmationDialog
        isOpen={confirmSignOut}
        title="Sign out"
        description="Are you sure you want to sign out? You will need to log in again to continue." 
        confirmLabel={signingOut ? 'Signing out...' : 'Sign out'}
        cancelLabel="Cancel"
        confirmVariant="danger"
        isLoading={signingOut}
        onConfirm={handleSignOut}
        onCancel={() => setConfirmSignOut(false)}
      />
    </nav>
  )
}