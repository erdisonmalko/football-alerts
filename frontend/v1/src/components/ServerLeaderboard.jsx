import styles from '../pages/Dashboard.module.css'

export default function ServerLeaderboard({ leaderboard }) {
  if (!leaderboard) return null

  return (
    <div className={styles.leaderboardSection}>
      <h3 className={styles.sectionTitle}>LEADERBOARD</h3>
      {leaderboard.entries && leaderboard.entries.length > 0 ? (
        <div className={styles.leaderboardList}>
          {leaderboard.entries.map((entry) => (
            <div key={entry.user_id} className={styles.leaderboardEntry}>
              <span className={styles.rank}>#{entry.rank}</span>
              <span className={styles.playerName}>
                {entry.full_name || entry.email}
              </span>
              <span className={styles.stats}>
                {entry.total_wins}W {entry.total_losses}L {entry.total_draws}D
              </span>
              <span className={styles.points}>{entry.total_points} pts</span>
            </div>
          ))}
        </div>
      ) : (
        <p className={styles.emptyText}>No leaderboard data yet.</p>
      )}
    </div>
  )
}