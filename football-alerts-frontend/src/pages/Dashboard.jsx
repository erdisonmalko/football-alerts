import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getSubscriptions } from '../api/endpoints'
import Nav from '../components/Nav'
import styles from './Dashboard.module.css'

function timeUntil(dateStr) {
  const diff = new Date(dateStr) - new Date()
  if (diff < 0) return 'LIVE / FINISHED'
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  if (days > 0) return `${days}D ${hours}H`
  return `${hours}H`
}

function formatKickoff(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short',
  }) + ' — ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) + ' UTC'
}

function alertBadge(dateStr) {
  const diff = new Date(dateStr) - new Date()
  const days = diff / 86400000
  if (days <= 0.25) return { label: '6H ALERT', cls: 'urgent' }
  if (days <= 3.1)  return { label: '3D ALERT', cls: 'soon' }
  if (days <= 7.1)  return { label: '1W ALERT', cls: 'upcoming' }
  return null
}

export default function Dashboard() {
  const { user } = useAuth()
  const [subscriptions, setSubscriptions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSubscriptions()
      .then(setSubscriptions)
      .finally(() => setLoading(false))
  }, [])

  const name = user?.full_name?.split(' ')[0] || 'Fan'

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <div className={styles.header}>
          <div>
            <p className={styles.greeting}>WELCOME BACK, {name.toUpperCase()}</p>
            <h1 className={styles.title}>YOUR MATCHES</h1>
          </div>
          <Link to="/subscriptions" className={styles.manageBtn}>
            MANAGE ALERTS
          </Link>
        </div>

        {loading ? (
          <div className={styles.empty}>
            <p>Loading...</p>
          </div>
        ) : subscriptions.length === 0 ? (
          <div className={styles.empty}>
            <p className={styles.emptyTitle}>NO ALERTS SET UP</p>
            <p className={styles.emptySub}>Subscribe to leagues or teams to see upcoming matches here.</p>
            <Link to="/subscriptions" className={styles.emptyBtn}>SET UP ALERTS</Link>
          </div>
        ) : (
          <div className={styles.subsGrid}>
            {subscriptions.map(sub => (
              <div key={sub.id} className={styles.subCard}>
                <div className={styles.subHeader}>
                  <span className={styles.subType}>{sub.subscription_type.toUpperCase()}</span>
                  <span className={styles.subName}>{sub.display_name}</span>
                </div>
                <p className={styles.subNote}>
                  Email alerts active — 1 week, 3 days, and 6 hours before each match.
                </p>
              </div>
            ))}
          </div>
        )}

        <div className={styles.alertsInfo}>
          <h2 className={styles.sectionTitle}>HOW ALERTS WORK</h2>
          <div className={styles.timeline}>
            <div className={styles.timelineStep}>
              <span className={styles.tlDot} data-type="week" />
              <div>
                <p className={styles.tlLabel}>1 WEEK BEFORE</p>
                <p className={styles.tlDesc}>Plan your schedule — match is on the horizon.</p>
              </div>
            </div>
            <div className={styles.timelineStep}>
              <span className={styles.tlDot} data-type="days" />
              <div>
                <p className={styles.tlLabel}>3 DAYS BEFORE</p>
                <p className={styles.tlDesc}>Reminder to clear your calendar.</p>
              </div>
            </div>
            <div className={styles.timelineStep}>
              <span className={styles.tlDot} data-type="hours" />
              <div>
                <p className={styles.tlLabel}>6 HOURS BEFORE</p>
                <p className={styles.tlDesc}>Kickoff is today — don't miss it.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
