import ServerLeaderboard from './ServerLeaderboard'
import ServerChallenges from './ServerChallenges'
import styles from '../pages/Dashboard.module.css'

export default function ServerDetail({ serverDetails, leaderboard, challenges, onBack, onLeave }) {
  return (
    <div className={styles.serverDetail}>
      <div className={styles.topActions}>
      <button onClick={onBack} className={styles.backBtn}>← BACK</button>
      <button onClick={onLeave} className={styles.leaveBtn}>LEAVE SERVER</button>
    </div>

      <div className={styles.serverHeader}>
        <h2 className={styles.serverName}>{serverDetails.name}</h2>
        <span className={styles.memberCount}>{serverDetails.members?.length || 0} members</span>
      </div>

      <ServerLeaderboard leaderboard={leaderboard} />
      <ServerChallenges challenges={challenges} />
    </div>
  )
}
