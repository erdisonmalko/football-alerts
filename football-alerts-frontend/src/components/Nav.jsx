import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Nav.module.css'

export default function Nav() {
  const { user, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path

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

      <div className={styles.user}>
        <span className={styles.email}>{user?.full_name || user?.email}</span>
        <button className={styles.signOut} onClick={handleSignOut}>SIGN OUT</button>
      </div>
    </nav>
  )
}