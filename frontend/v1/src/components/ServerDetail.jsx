import ServerLeaderboard from './ServerLeaderboard'
import ServerChallenges from './ServerChallenges'
import styles from '../pages/Dashboard.module.css'

export default function ServerDetail({ serverDetails, leaderboard, challenges, onBack }) {
  return (
    <div className={styles.serverDetail}>
      <button onClick={onBack} className={styles.backBtn}>← Back</button>
      
      <div className={styles.serverHeader}>
        <h2 className={styles.serverName}>{serverDetails.name}</h2>
        <span className={styles.memberCount}>{serverDetails.members?.length || 0} members</span>
      </div>

      <ServerLeaderboard leaderboard={leaderboard} />
      <ServerChallenges challenges={challenges} />
    </div>
  )
}
